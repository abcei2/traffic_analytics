import requests

from django.conf import settings
from django.views import View
from django.db.models import Q
from django.urls import reverse
from django.shortcuts import redirect, get_object_or_404
from django.utils.safestring import mark_safe
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.core.exceptions import ValidationError, PermissionDenied
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.mixins import LoginRequiredMixin

from core.view_utils import BaseView, safe_next_url, sanitize_html
from ui.models import User
from ui.constants import (
    CIIU_CODES,
    COMPANY_TYPES,
    MANUFACTURE_SECTORS,
    SERVICE_SECTORS,
    COMMERCE_SECTORS,
    MANUFACTURE_SIZES,
    SERVICE_SIZES,
    COMMERCE_SIZES,
)


class PasswordResetView(LoginRequiredMixin, BaseView):
    def post(self, request, uid):
        if not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied

        user = get_object_or_404(User, pk=uid)

        url = reverse(
            "password_reset_confirm",
            kwargs={
                "uidb64": urlsafe_base64_encode(force_bytes(user.pk)),
                "token": default_token_generator.make_token(user),
            },
        )
        url = request.build_absolute_uri(url)
        return self.render_json(
            {
                "success": True,
                "url": url,
            }
        )


class Logout(BaseView):
    def get(self, request):
        next_url = safe_next_url(request.GET.get("next", reverse("signup")))

        if request.user.is_authenticated:
            logout(request)

        return redirect(next_url)


class Login(BaseView):
    template = "ui/login.html"
    # custom_stylesheet = "journal.min.css"

    def get(self, request):
        next_url = safe_next_url(request.GET.get("next"))

        if request.user.is_authenticated:
            return redirect(next_url)

        return self.render_template(request, {"next": next_url})

    def post(self, request):
        legal_id = request.POST.get("legal_id")
        password = request.POST.get("password")
        next_url = safe_next_url(request.POST.get("next"))

        if request.user.is_authenticated:
            return redirect(next_url)

        if not (legal_id and password):
            return self.render_template(
                request,
                {
                    "login_errors": ["Falta el NIT o la clave"],
                    "next": next_url,
                },
            )

        user = authenticate(legal_id=legal_id, password=password)
        if not user:
            return self.render_template(
                request,
                {
                    "login_errors": ["NIT o clave incorrectos"],
                    "next": next_url,
                },
            )

        login(request, user)
        return redirect(next_url)


class Signup(BaseView):
    template = "ui/signup.html"
    # custom_stylesheet = "journal.min.css"

    def context(self):
        return {
            "title": "PACT 4.0 | CTA",
            "CAPTCHA_SITE_KEY": settings.CAPTCHA_SITE_KEY,
            "CIIU_CODES": CIIU_CODES,
            "COMPANY_TYPES": COMPANY_TYPES,
            "COMPANY_SECTORS_DICT": {
                "MANUFACTURE_SECTORS": MANUFACTURE_SECTORS,
                "SERVICE_SECTORS": SERVICE_SECTORS,
                "COMMERCE_SECTORS": COMMERCE_SECTORS,
            },
            "COMPANY_SIZES_DICT": {
                "MANUFACTURE_SIZES": MANUFACTURE_SIZES,
                "SERVICE_SIZES": SERVICE_SIZES,
                "COMMERCE_SIZES": COMMERCE_SIZES,
            },
            "MAP_KEY": settings.MAP_KEY,
        }

    def get(self, request):
        next_url = safe_next_url(request.GET.get("next"))

        # they're already logged in
        if request.user.is_authenticated:
            return redirect(next_url)

        return self.render_template(
            request,
            {"next": next_url, **self.context()},
        )

    def post(self, request):
        legal_id = sanitize_html(request.POST.get("legal_id"))
        name = sanitize_html(request.POST.get("name"))
        phone = sanitize_html(request.POST.get("phone"))
        email = sanitize_html(request.POST.get("email"))
        activity_years = sanitize_html(request.POST.get("activity_years"))
        contact_name = sanitize_html(request.POST.get("contact_name"))
        ciiu = sanitize_html(request.POST.get("ciiu"))
        company_type = sanitize_html(request.POST.get("company_type"))
        company_sector = sanitize_html(request.POST.get("company_sector"))
        company_size = sanitize_html(request.POST.get("company_size"))
        address = sanitize_html(request.POST.get("address"))
        lnglat = sanitize_html(request.POST.get("lnglat"))

        password = request.POST.get("password")
        password2 = request.POST.get("password2")
        privacy = request.POST.get("privacy")
        recaptcha_response = request.POST.get("g-recaptcha-response")

        next_url = safe_next_url(request.POST.get("next"))

        # they're already logged in
        if request.user.is_authenticated:
            return redirect(next_url)

        # they tried to log in using the signup page
        user = authenticate(legal_id=legal_id, password=password)
        if user:
            login(request, user)
            return redirect(next_url)

        # validate data
        errors = validate_signup_form(
            legal_id,
            contact_name,
            email,
            ciiu,
            company_type,
            company_sector,
            company_size,
            password,
            password2,
            privacy,
            recaptcha_response,
            lnglat,
        )
        if errors:
            return self.render_template(
                request,
                {
                    "signup_errors": errors,
                    "legal_id": legal_id,
                    "name": name,
                    "contact_name": contact_name,
                    "phone": phone,
                    "email": email,
                    "activity_years": activity_years,
                    "ciiu": ciiu,
                    "address": address,
                    "lnglat": lnglat,
                    "next": next_url,
                    **self.context(),
                },
            )

        # create a new user account and log them in
        user = User.objects.create_user(
            legal_id=legal_id,
            name=name,
            phone=phone,
            contact_name=contact_name,
            activity_years=activity_years,
            ciiu=ciiu,
            company_type=company_type,
            company_sector=company_sector,
            company_size=company_size,
            address=address,
            lnglat=lnglat,
            username=email,
            email=email or "",
            password=password,
        )

        # send_signup_email.send(user.username)
        login(request, user)
        return redirect(next_url)


def validate_signup_form(
    legal_id,
    contact_name,
    email,
    ciiu,
    company_type,
    company_sector,
    company_size,
    password,
    password2,
    privacy,
    recaptcha_response,
    lnglat,
):
    errors = []
    # they're missing a email/password/contact
    if not email:
        errors += ["Hace falta el correo."]

    if not password:
        errors += ["Hace falta la clave."]

    if not contact_name:
        errors += ["Hace falta el nombre de la persona de contacto de la empresa."]

    if not lnglat:
        errors += [
            "Hace falta la ubicación de la empresa, por favor use el mapa para esto."
        ]

    # CIIU code validation
    if not ciiu in [code for code, _ in CIIU_CODES]:
        errors += ["El código CIIU no es válido."]

    # Validate company type/sector/size
    sectors = eval(f"{company_type.upper()}_SECTORS")
    if company_sector not in [sector for sector, _ in sectors]:
        errors += ["El sector de empresa elegido no es válido."]
    if company_type.upper() not in company_size:
        errors += ["El tamaño en ingresos de la empresa elegido no es válido."]

    # re-typed password dont match
    if (not settings.DEBUG) and (not password == password2):
        errors += ["Las claves no coinciden."]

    # must accept privacy
    if (not settings.DEBUG) and privacy != "on":
        errors += ["Debes aceptar las políticas de privacidad y protección de datos."]

    # reCaptcha validation
    if not settings.DEBUG:
        if not recaptcha_response:
            errors += ["Falta respuesta del reCaptcha."]

        response = requests.post(
            url=settings.CAPTCHA_SITE_VERIFY_URL,
            data={
                "secret": settings.CAPTCHA_SECRET_KEY,
                "response": recaptcha_response,
            },
        )
        if not response.json().get("success"):
            errors += [
                "Error de captcha: " + ",".join(response.json().get("error-codes"))
            ]

    # user already exists with that email
    if User.objects.filter(Q(email=email) | Q(legal_id=legal_id)).exists():
        errors += [
            mark_safe(
                "Estos datos ya se encuentran registrados.<br>"
                f"¿Deseas <a href=\"{reverse('login')}\">iniciar sesión</a>?"
            )
        ]

    # check the password validity
    user = User(username=email, email=(email or ""))
    try:
        if not settings.DEBUG:
            validate_password(password, user=user)
    except ValidationError as e:
        errs = ", ".join(e.messages)
        errors += [f"Esta clave no es válida, por favor prueba con otra: {errs}"]

    return errors
