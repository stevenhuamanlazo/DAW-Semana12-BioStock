"""
Configuración del proyecto BioStock
Gestión de Inventario de Suministros Médicos y Reactivos de Laboratorio.

Semana 12 - Desarrollo de Aplicaciones Web (IS093A)
Formularios, Django Admin, Middleware, Sesiones, Autenticación y Autorización.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# SEGURIDAD BÁSICA
# La SECRET_KEY y DEBUG se leen del entorno para poder rotar la clave y para
# nunca dejar DEBUG=True en producción (requisito de la Fase 5 de la guía).
#   Desarrollo (por defecto):  DEBUG=True
#   Producción / auditoría:    DJANGO_DEBUG=0 y DJANGO_SECRET_KEY=<clave larga>
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-solo-para-desarrollo-biostock-cambiar-en-produccion",
)
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")

# ---------------------------------------------------------------------------
# APLICACIONES
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_extensions",  # shell_plus para probar queries y sesiones
    "inventario",
]

# ---------------------------------------------------------------------------
# MIDDLEWARE
# El orden importa: en la petición se ejecuta de arriba hacia abajo y en la
# respuesta de abajo hacia arriba (modelo "cebolla"/LIFO).
# Los dos middlewares propios van al final de la cadena de seguridad:
#   - AuditoriaMiddleware        -> registra usuario, ruta, IP, estado y tiempo
#   - CabecerasSeguridadMiddleware -> añade CSP, Referrer-Policy, etc.
# ---------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "inventario.middleware.AuditoriaMiddleware",
    "inventario.middleware.CabecerasSeguridadMiddleware",
]

ROOT_URLCONF = "biostock.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "biostock.wsgi.application"

# ---------------------------------------------------------------------------
# BASE DE DATOS
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# INTERNACIONALIZACIÓN
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "es"
TIME_ZONE = "America/Lima"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# AUTENTICACIÓN
# @login_required redirige a LOGIN_URL cuando no hay sesión.
# ---------------------------------------------------------------------------
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "login"

# ---------------------------------------------------------------------------
# SESIONES (Fase 4)
#  - Motor en base de datos: la cookie solo guarda el id de sesión firmado.
#  - Duración de 30 minutos con renovación en cada petición (inactividad).
#  - HttpOnly: JavaScript no puede leer la cookie (mitiga robo por XSS).
#  - SameSite=Lax: la cookie no se envía en POST de otros sitios (mitiga CSRF).
# ---------------------------------------------------------------------------
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 60 * 30
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# Las cookies "Secure" solo viajan por HTTPS. En desarrollo local (http) se
# desactivan; cuando DEBUG=False se activan automáticamente.
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

# ---------------------------------------------------------------------------
# CABECERAS Y TRANSPORTE SEGURO (solo efectivas con DEBUG=False)
# ---------------------------------------------------------------------------
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ---------------------------------------------------------------------------
# LOGS DE AUDITORÍA (los escribe AuditoriaMiddleware)
# ---------------------------------------------------------------------------
LOG_DIR = BASE_DIR / "logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "auditoria": {"format": "%(asctime)s | %(levelname)s | %(message)s"},
    },
    "handlers": {
        "archivo_auditoria": {
            "class": "logging.FileHandler",
            "filename": LOG_DIR / "auditoria.log",
            "formatter": "auditoria",
            "encoding": "utf-8",
        },
        "consola": {"class": "logging.StreamHandler", "formatter": "auditoria"},
    },
    "loggers": {
        "biostock.auditoria": {
            "handlers": ["archivo_auditoria", "consola"],
            "level": "INFO",
            "propagate": False,
        },
    },
}