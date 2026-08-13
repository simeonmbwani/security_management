"""
Django settings for the SGMIS (Security Guard Management Information System).
"""
from pathlib import Path
from datetime import timedelta
from decouple import config, Csv
from celery.schedules import crontab
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY", default="dev-insecure-secret-key-change-me")
DEBUG = 'RENDER' not in os.environ
ALLOWED_HOSTS = ['.onrender.com', 'localhost', '127.0.0.1']

RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # third party
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_filters",
    "django_celery_beat",
    "drf_yasg",

    # local apps
    "core",
    "apps.accounts",
    "apps.occurrence_book",
    "apps.patrols",
    "apps.shifts",
    "apps.leave_management",
    "apps.exam_management",
    "apps.escort_management",
    "apps.incidents",
    "apps.visitors",
    "apps.registers",
    "apps.notifications",
    "apps.reports",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    'whitenoise.middleware.WhiteNoiseMiddleware',
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "sgmis_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "sgmis_project.wsgi.application"
ASGI_APPLICATION = "sgmis_project.asgi.application"

import os
import dj_database_url

# Get the URL, defaulting to local SQLite if not found
db_url = os.environ.get('DATABASE_URL', f"sqlite:///{BASE_DIR / 'db.sqlite3'}")

DATABASES = {
    'default': dj_database_url.config(
        default=db_url,
        conn_max_age=600,
        # Only require SSL if we are connecting to a PostgreSQL database
        ssl_require=db_url.startswith('postgres'),
    )
}
AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Harare"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# DRF / JWT
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=8),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", default="", cast=Csv())

# ---------------------------------------------------------------------------
# Celery
# ---------------------------------------------------------------------------
CELERY_BROKER_URL = config("REDIS_URL", default="redis://127.0.0.1:6379/0")
CELERY_RESULT_BACKEND = config("REDIS_URL", default="redis://127.0.0.1:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_IMPORTS = ("sgmis_project.tasks",)
CELERY_BEAT_SCHEDULE = {
    "send-two-day-duty-reminders": {
        "task": "sgmis_project.tasks.send_two_day_duty_change_reminders",
        "schedule": crontab(hour=8, minute=0),
    },
}

# django-celery-beat periodic task schedule (created via a data migration,
# see apps/accounts/migrations or run `python manage.py setup_periodic_tasks`
# if you add that management command). Kept here for reference:
CELERY_BEAT_SCHEDULE_REFERENCE = {
    "generate-tomorrow-roster": {"task": "sgmis_project.tasks.generate_tomorrow_roster", "schedule": "daily @ 20:00"},
    "run-monthly-leave-accrual": {"task": "sgmis_project.tasks.run_monthly_leave_accrual", "schedule": "monthly, 1st @ 00:05"},
    "flag-overdue-patrols": {"task": "sgmis_project.tasks.flag_overdue_patrols", "schedule": "every 15 minutes"},
    "send-start-patrol-reminders": {"task": "sgmis_project.tasks.send_start_patrol_reminders", "schedule": "every 30 minutes"},
    "send-shift-change-reminders": {"task": "sgmis_project.tasks.send_shift_change_reminders", "schedule": "daily @ 17:30"},
    "send-two-day-duty-reminders": {"task": "sgmis_project.tasks.send_two_day_duty_change_reminders", "schedule": "daily @ 08:00"},
}

# ---------------------------------------------------------------------------
# SGMIS business-rule constants (tweak per organisation policy)
# ---------------------------------------------------------------------------
SGMIS_SETTINGS = {
    "SHIFT_CYCLE_DAYS": 4,               # each pair works 4 days before rotating
    "CASUAL_LEAVE_PER_MONTH": 1,
    "CASUAL_LEAVE_MAX": 12,
    "CASUAL_LEAVE_EXPIRY_MONTHS": 12,
    "VACATION_LEAVE_PER_MONTH": 2.5,
    "VACATION_LEAVE_MAX": 90,
    "HOLIDAY_COMPENSATION_DAYS": 2,
    "EXAM_ESCORT_SHIFT_DAYS": 5,
    "PATROL_OVERDUE_MINUTES": 90,
}
