import requests

from django.db import models
from django.conf import settings
from django.views import View
from django.shortcuts import render, redirect
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.password_validation import validate_password

from core.model_utils import BaseModel
from core.view_utils import safe_next_url
from ui.constants import (
    CIIU_CODES,
    COMPANY_TYPES,
    COMPANY_SECTORS,
    COMPANY_SIZES,
)


class CustomUserManager(BaseUserManager):
    """
    legal_id is the unique identifier for authentication instead of usernames
    """

    def create_user(self, legal_id, password, **extra_fields):
        if not legal_id:
            raise ValueError("The Legal ID must be set")

        user = self.model(legal_id=legal_id, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, legal_id, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(legal_id, password, **extra_fields)


class User(AbstractUser, BaseModel):
    legal_id = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    phone = models.CharField(max_length=32)
    contact_name = models.CharField(max_length=128)

    activity_years = models.PositiveIntegerField(null=True)
    ciiu = models.CharField(max_length=8, choices=CIIU_CODES)

    company_type = models.CharField(max_length=128, choices=COMPANY_TYPES, blank=True)
    company_sector = models.CharField(
        max_length=128, choices=COMPANY_SECTORS, blank=True
    )
    company_size = models.CharField(max_length=128, choices=COMPANY_SIZES, blank=True)

    address = models.CharField(max_length=256, blank=True)
    lnglat = models.CharField(
        max_length=100, blank=True, verbose_name="Coordenadas (lon.gitud,lat.itud)"
    )  # Always use the format 'lon.gitude,lat.itude'

    debug_toolbar = models.BooleanField(default=False)

    USERNAME_FIELD = "legal_id"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    @property
    def active_survey(self):
        try:
            return self.surveyattempt_set.get(user=self, end_time=None)
        except ObjectDoesNotExist:
            return None

    @cached_property
    def ciudad(self):
        if not self.lnglat:
            return "Sin coordenadas"

        url = settings.MAPBOX_GEOCODING_ENDPOINT.format(
            coords=self.lnglat,
            token=settings.MAP_KEY,
        )
        try:
            resp = requests.get(url)
            data = resp.json()
            feat = data.get("features")[0]
            return feat["text_es"]
        except Exception as e:
            print(f"Error sacando ciudad: {e}", flush=True)
            return "Desconocida"


    def __str__(self):
        return f"<{self.short_id}> {self.name} ({self.legal_id})"

    def __json__(self, *attrs):
        return self.attrs(
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
            "is_superuser",
            "is_god",
            "last_login",
            "date_joined",
            "created",
            "updated",
            *attrs,
        )
