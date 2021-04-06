import uuid
import bleach

from enum import Enum
from typeguard import typechecked
from typing import Optional, Dict, Any, Union, List

from django.conf import settings
from django.urls import reverse
from django.views import View
from django.utils import timezone
from django.db import connection
from django.shortcuts import render
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import DecimalField, CharField, IntegerField, AutoField, QuerySet


JSONValueType = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]


def safe_next_url(next_url: str) -> str:
    # send them to the homepage if no next is specified
    next_url = next_url or reverse("home")
    # dont allow outside redirects like https://attacker.com,
    #   //attacker.com or ftp://attacker.com
    if next_url.startswith("//") or not next_url.startswith("/"):
        next_url = reverse("home")

    return next_url


def sanitize_html(text, strip=False, allow_safe=True):
    """
    Strip/escape html tags, attributes, and styles using a whitelist.
    Set allow_safe=False to escape all html tags, by default it allows
    a limited subset of safe ones (e.g. <b>, <i>, <img>...).
    """
    attrs = {
        "*": [
            "style",
            "href",
            "alt",
            "title",
            "class",
            "border",
            "padding",
            "margin",
            "line-height",
        ],
        "img": ["src"],
    }
    if not allow_safe:
        tags = []
        styles = []
    else:
        tags = [
            "p",
            "b",
            "br",
            "em",
            "blockquote",
            "strong",
            "i",
            "u",
            "a",
            "ul",
            "li",
            "ol",
            "img",
            "span",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "h7",
            "table",
            "td",
            "thead",
            "tbody",
            "tr",
            "div",
            "sub",
            "sup",
            "small",
        ]
        styles = [
            "color",
            "font-weight",
            "font-size",
            "font-family",
            "text-decoration",
            "font-variant",
        ]

    cleaned_text = bleach.clean(text, tags, attrs, styles, strip=strip)

    return cleaned_text  # "free of XSS"


class classproperty:
    """like @classmethod for @property"""

    def __init__(self, f):
        self.f = f

    def __get__(self, obj, owner):
        return self.f(owner)


class BaseView(View):
    def __init__(self, *args, **kwargs):
        self.python_start_ts = round(timezone.now().timestamp() * 1000)
        super().__init__(*args, **kwargs)

    @classproperty
    def view_class(cls):
        return f"{cls.__module__}.{cls.__name__}"

    def global_context(self, request=None):
        self.python_end_ts = round(timezone.now().timestamp() * 1000)

        gmt_offset = self.request.COOKIES.get("gmt_offset")
        tz = None
        if gmt_offset:
            tz = timezone.get_fixed_timezone(int(gmt_offset.strip()))
            timezone.activate(tz)

        return {
            "DEFAULT_HOST": settings.DEFAULT_HOST,
            "DEBUG": settings.DEBUG,
            "ENV": settings.SERVER_ENV,
            "view": self.view_class,
            "template": getattr(self, "template", ""),
            "custom_stylesheet": getattr(self, "custom_stylesheet", ""),
            "python_start_ts": self.python_start_ts,
            "python_end_ts": self.python_end_ts,
            "sql_queries": len(connection.queries),
            "timezone": tz,
            "nonce": str(getattr(request, "csp_nonce", "")),
            "PAGE_DESCRIPTION": settings.PAGE_DESCRIPTION,
        }

    @typechecked
    def render_json(self, json: JSONValueType, **kwargs):
        return JsonResponse(json, **kwargs)

    def render_template(
        self,
        request,
        context: Optional[Dict[str, Any]] = None,
        template: Optional[str] = None,
    ):
        return render(
            request,
            template or self.template,
            {**self.global_context(request), **(context or {})},
        )


class StrBasedEnum(Enum):
    @classmethod
    def from_str(cls, string):
        return cls._member_map_[string.upper()]

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class ExtendedEncoder(DjangoJSONEncoder):
    """
    Extended json serializer that supports serializing several model
    fields and objects
    """

    def default(self, obj):
        cls_name = obj.__class__.__name__

        if isinstance(obj, (DecimalField, CharField)):
            return str(obj)

        elif isinstance(obj, (IntegerField, AutoField)):
            return int(obj)

        elif hasattr(obj, "__json__"):
            return obj.__json__()

        elif isinstance(obj, QuerySet):
            return list(obj)

        elif isinstance(obj, set):
            return list(obj)

        elif isinstance(obj, uuid.UUID):
            return str(obj)

        elif isinstance(obj, bytes):
            return obj.decode()

        elif cls_name == "CallableBool":
            # ^ shouldn't check using isinstance because CallableBools
            #   will eventually be deprecated
            return bool(obj)

        elif cls_name == "AnonymousUser":
            # ^ cant check using isinstance since models aren't ready
            #   yet when this is called
            return None  # AnonUser should always be represented as null in JS

        elif isinstance(obj, StrBasedEnum):
            return str(obj)

        elif cls_name in ("dict_items", "dict_keys", "dict_values"):
            return tuple(obj)

        return DjangoJSONEncoder.default(self, obj)

    @classmethod
    def convert_for_json(cls, obj, recursive=True):
        if recursive:
            if isinstance(obj, dict):
                return {
                    cls.convert_for_json(k): cls.convert_for_json(v)
                    for k, v in obj.items()
                }
            elif isinstance(obj, (list, tuple)):
                return [cls.convert_for_json(i) for i in obj]

        try:
            return cls.convert_for_json(cls().default(obj))
        except TypeError:
            return obj
