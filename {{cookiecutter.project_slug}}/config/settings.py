import logging
import pathlib
from email.utils import getaddresses

{%- if cookiecutter.use_sentry == 'y' %}
import sentry_sdk
{%- endif %}
from django.urls import reverse_lazy
from django.utils.csp import CSP  # type: ignore[reportMissingTypeStubs]
from environs import Env
{%- if cookiecutter.use_opentelemetry == 'y' %}
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
{%- endif %}
{%- if cookiecutter.use_sentry == 'y' %}
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import ignore_logger
{%- endif %}

BASE_DIR = pathlib.Path(__file__).resolve(strict=True).parents[1]

env = Env()
env.read_env()

DEBUG = env.bool("DEBUG", default=False)

SECRET_KEY = env(
    "SECRET_KEY",
    default="django-insecure-change-me-in-production",
)

SECRET_KEY_FALLBACKS = env.list("SECRET_KEY_FALLBACKS", default=[])

INSTALLED_APPS: list[str] = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.humanize",
    "django.contrib.messages",
    "django.contrib.postgres",
    "django.contrib.sessions",
    "django.contrib.sitemaps",
    "django.contrib.sites",
    "django.contrib.staticfiles",
    "django.forms",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.github",
    "allauth.socialaccount.providers.google",
    "django_htmx",
    "django_http_compression",
    "django_linear_migrations",
    "django_tailwind_cli",
    "django_tasks_db",
    "health_check",
    "heroicons",
    "widget_tweaks",
    "{{cookiecutter.package_name}}.users",
]


MIDDLEWARE: list[str] = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django_permissions_policy.PermissionsPolicyMiddleware",
    "django.contrib.sites.middleware.CurrentSiteMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django_http_compression.middleware.HttpCompressionMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "{{cookiecutter.package_name}}.middleware.HtmxCacheMiddleware",
    "{{cookiecutter.package_name}}.middleware.HtmxMessagesMiddleware",
    "{{cookiecutter.package_name}}.middleware.HtmxRedirectMiddleware",
    "{{cookiecutter.package_name}}.middleware.SearchMiddleware",
]

# Databases
#
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DATABASES = {
    "default": env.dj_db_url(
        "DATABASE_URL",
        default="postgresql://postgres:password@127.0.0.1:5432/postgres",  # pragma: allowlist secret
    )
}

if env.bool("USE_CONNECTION_POOL", default=True):
    # Connection pool settings
    # https://www.psycopg.org/psycopg3/docs/api/pool.html#psycopg_pool.ConnectionPool
    DATABASES["default"]["CONN_MAX_AGE"] = 0
    DATABASES["default"]["OPTIONS"] = {
        "pool": (
            {
                "min_size": env.int("CONN_POOL_MIN_SIZE", 2),
                "max_size": env.int("CONN_POOL_MAX_SIZE", 10),
                "max_lifetime": env.int("CONN_POOL_MAX_LIFETIME", 1800),
                "max_idle": env.int("CONN_POOL_MAX_IDLE", 120),
                "max_waiting": env.int("CONN_POOL_MAX_WAITING", 200),
                # assumes 30s statement_timeout in PostgreSQL
                "timeout": env.int("CONN_POOL_TIMEOUT", default=20),
            }
        ),
    }

# Caches

DEFAULT_CACHE_TIMEOUT = env.int("DEFAULT_CACHE_TIMEOUT", 360)

CACHES = {
    "default": env.dj_cache_url("REDIS_URL", default="redis://127.0.0.1:6379/0")
    | {
        "TIMEOUT": DEFAULT_CACHE_TIMEOUT,
    }
}


# Required for health check
REDIS_URL = CACHES["default"]["LOCATION"]

# Templates

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "DIRS": [BASE_DIR / "templates"],
        "OPTIONS": {
            "builtins": [
                "{{cookiecutter.package_name}}.templatetags",
            ],
            "debug": env.bool("TEMPLATE_DEBUG", default=DEBUG),
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                "{{cookiecutter.package_name}}.context_processors.cache_timeout",
                "{{cookiecutter.package_name}}.context_processors.csrf_header",
            ],
        },
    }
]


# Server settings

ROOT_URLCONF = "config.urls"

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

SITE_ID = 1

USE_HTTPS = env.bool("USE_HTTPS", default=True)

# Session and cookies

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

# Store CSRF tokens in the session rather than a cookie. This closes the
# subdomain cookie-injection attack vector, where a compromised subdomain
# could overwrite the CSRF cookie for the parent domain.
CSRF_USE_SESSIONS = True

CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[]) or []

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = USE_HTTPS


# Email configuration

# Mailgun
# https://anymail.dev/en/v9.0/esps/mailgun/

if MAILGUN_API_KEY := env("MAILGUN_API_KEY", default=None):
    INSTALLED_APPS += ["anymail"]

    EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"

    # For European domains: https://api.eu.mailgun.net/v3
    MAILGUN_API_URL = env("MAILGUN_API_URL", default="https://api.mailgun.net/v3")
    MAILGUN_SENDER_DOMAIN = EMAIL_HOST = env("MAILGUN_SENDER_DOMAIN")

    ANYMAIL = {
        "MAILGUN_API_KEY": MAILGUN_API_KEY,
        "MAILGUN_API_URL": MAILGUN_API_URL,
        "MAILGUN_SENDER_DOMAIN": MAILGUN_SENDER_DOMAIN,
    }
else:
    EMAIL_CONFIG = env.dj_email_url("EMAIL_URL", default="smtp://localhost:1025")

    EMAIL_BACKEND = EMAIL_CONFIG["EMAIL_BACKEND"]
    EMAIL_FILE_PATH = EMAIL_CONFIG["EMAIL_FILE_PATH"]
    EMAIL_HOST = EMAIL_CONFIG["EMAIL_HOST"]
    EMAIL_HOST_PASSWORD = EMAIL_CONFIG["EMAIL_HOST_PASSWORD"]
    EMAIL_HOST_USER = EMAIL_CONFIG["EMAIL_HOST_USER"]
    EMAIL_PORT = EMAIL_CONFIG["EMAIL_PORT"]
    EMAIL_TIMEOUT = EMAIL_CONFIG["EMAIL_TIMEOUT"]
    EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)
    EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=False)

ADMINS = getaddresses([admins]) if (admins := env("ADMINS", default="")) else []

MANAGERS = (
    getaddresses([managers]) if (managers := env("MANAGERS", default="")) else ADMINS
)

SERVER_EMAIL = env("SERVER_EMAIL", default=f"no-reply@{EMAIL_HOST}")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default=SERVER_EMAIL)
CONTACT_EMAIL = env("CONTACT_EMAIL", default=SERVER_EMAIL)

# authentication settings
# https://docs.djangoproject.com/en/dev/ref/settings/#authentication-backends

AUTH_USER_MODEL = "users.User"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

AUTH_PASSWORD_VALIDATORS: list[dict[str, str]] = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_REDIRECT_URL = reverse_lazy("index")
LOGIN_URL = reverse_lazy("account_login")

# https://django-allauth.readthedocs.io/en/latest/configuration.html

ACCOUNT_SIGNUP_FIELDS = [
    "email*",
    "username*",
    "password1*",
    "password2*",
]

ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_EMAIL_VERIFICATION_BY_CODE_ENABLED = True
ACCOUNT_EMAIL_VERIFICATION_SUPPORTS_RESEND = True
ACCOUNT_LOGIN_METHODS = {"username", "email"}
ACCOUNT_LOGIN_ON_PASSWORD_RESET = True
ACCOUNT_PASSWORD_RESET_BY_CODE_ENABLED = True
ACCOUNT_SIGNUP_FORM_HONEYPOT_FIELD = "phone_number"
ACCOUNT_PREVENT_ENUMERATION = True
ACCOUNT_UNIQUE_EMAIL = True

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": [
            "profile",
            "email",
        ],
        "AUTH_PARAMS": {
            "access_type": "online",
        },
    },
}

# admin settings

ADMIN_URL = env("ADMIN_URL", default="admin/")

# Internationalization/Localization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = "en"

USE_TZ = True
TIME_ZONE = "UTC"

USE_I18N = True

FORMAT_MODULE_PATH = ["config.formats"]

# Static files

# Ephemeral static files required for build only
STATIC_SRC = BASE_DIR / "static"

STATIC_URL = env("STATIC_URL", default="/static/")
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [STATIC_SRC]

# Tailwind CLI
# https://django-tailwind-cli.andrich.me/settings/#settings

TAILWIND_CLI_SRC_CSS = BASE_DIR / "tailwind" / "app.css"
TAILWIND_CLI_DIST_CSS = "app.css"

# Whitenoise
# https://whitenoise.readthedocs.io/en/latest/django.html
#

if env.bool("USE_COLLECTSTATIC", default=True):
    STORAGES = {
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
else:
    # for development only
    INSTALLED_APPS += ["whitenoise.runserver_nostatic"]


# Templates
# https://docs.djangoproject.com/en/1.11/ref/forms/renderers/

FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

# Secure settings
# https://docs.djangoproject.com/en/4.1/topics/security/

SECURE_CONTENT_TYPE_NOSNIFF = True

if USE_X_FORWARDED_HOST := env.bool("USE_X_FORWARDED_HOST", default=True):
    SECURE_PROXY_SSL_HEADER = tuple(
        env.list(
            "SECURE_PROXY_SSL_HEADER",
            default=["HTTP_X_FORWARDED_PROTO", "https"],
        )
        or []
    )

SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=USE_HTTPS)

SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False
)
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=False)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)

# Permissions Policy
# https://pypi.org/project/django-permissions-policy/

PERMISSIONS_POLICY: dict[str, list] = {
    "accelerometer": [],
    "camera": [],
    "encrypted-media": [],
    "fullscreen": [],
    "geolocation": [],
    "gyroscope": [],
    "magnetometer": [],
    "microphone": [],
    "payment": [],
}

# Content-Security-Policy
# https://docs.djangoproject.com/en/dev/ref/csp/

CSP_SCRIPT_WHITELIST = env.list("CSP_SCRIPT_WHITELIST", default=[])

# NOTE: HTMX and Alpine require 'unsafe-inline' and 'unsafe-eval'
SCRIPT_SCP = [
    CSP.SELF,
    CSP.UNSAFE_EVAL,
    CSP.UNSAFE_INLINE,
    *CSP_SCRIPT_WHITELIST,
]

CSP_DATA = f"data: {'https' if USE_HTTPS else 'http'}:"

SECURE_CSP = {
    "default-src": [CSP.SELF],
    "style-src": [
        CSP.SELF,
        CSP.UNSAFE_INLINE,
    ],
    "script-src": SCRIPT_SCP,
    "script-src-elem": SCRIPT_SCP,
    "img-src": [CSP.SELF, CSP_DATA],
    "media-src": [CSP.SELF],
}

# Tasks
# https://docs.djangoproject.com/en/6.0/topics/tasks/
# https://pypi.org/project/django-tasks-db/

TASKS = {
    "default": {
        "BACKEND": "django_tasks_db.DatabaseBackend",
        "QUEUES": ["default"],
    }
}

# Logging
# https://docs.djangoproject.com/en/5.0/howto/logging/

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "%(message)s",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "null": {
            "level": "DEBUG",
            "class": "logging.NullHandler",
            "formatter": "simple",
        },
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
        },
    },
    "loggers": {
        "root": {
            "handlers": ["console"],
            "level": "INFO",
        },
        "{{cookiecutter.package_name}}": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.server": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.security.DisallowedHost": {
            "handlers": ["null"],
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console", "mail_admins"],
            "propagate": False,
        },
        "environ": {
            "handlers": ["console"],
            "level": "CRITICAL",
            "propagate": False,
        },
        "httpx": {
            "handlers": ["console"],
            "level": "CRITICAL",
            "propagate": False,
        },
        "httpcore": {
            "handlers": ["console"],
            "level": "CRITICAL",
            "propagate": False,
        },
    },
}

{%- if cookiecutter.use_opentelemetry == 'y' %}

# OpenTelemetry
# https://opentelemetry.io/docs/instrumentation/python/automatic/

if OPEN_TELEMETRY_URL := env("OPEN_TELEMETRY_URL", default=None):
    # Configure OTLP exporter - OTLPSpanExporter uses the endpoint as-is, so
    # we must include the signal-specific path explicitly.
    otlp_exporter = OTLPSpanExporter(
        endpoint=f"{OPEN_TELEMETRY_URL.rstrip('/')}/v1/traces"
    )

    resource = Resource.create(
        {
            "service.name": env(
                "OPEN_TELEMETRY_SERVICE_NAME",
                default="{{cookiecutter.project_slug}}",
            ),
            "deployment.environment": env(
                "OPEN_TELEMETRY_ENVIRONMENT", default="production"
            ),
            "service.version": env("OPEN_TELEMETRY_VERSION", default="0.0.0"),
        }
    )

    # Configure tracer provider
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    trace.set_tracer_provider(tracer_provider)

    # Instrument Django and Redis
    DjangoInstrumentor().instrument()
    PsycopgInstrumentor().instrument()
    RedisInstrumentor().instrument()
    RequestsInstrumentor().instrument()

    # Suppress noise from OpenTelemetry libraries
    logging.getLogger("opentelemetry").setLevel(logging.WARNING)
    logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
{%- endif %}

{%- if cookiecutter.use_sentry == 'y' %}

# Sentry
# https://docs.sentry.io/platforms/python/guides/django/

if SENTRY_URL := env("SENTRY_URL", default=None):
    ignore_logger("django.security.DisallowedHost")

    sentry_sdk.init(
        dsn=SENTRY_URL,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.5,
        # If you wish to associate users to errors (assuming you are using
        # django.contrib.auth) you may enable sending PII data.
        send_default_pii=env.bool("SENTRY_SEND_PII", default=False),
    )
{%- endif %}

# Dev tools

# Watchfiles
# https://github.com/adamchainz/django-watchfiles

if env.bool("USE_WATCHFILES", default=False):
    INSTALLED_APPS += ["django_watchfiles"]

# Django browser reload
# https://github.com/adamchainz/django-browser-reload

if env.bool("USE_BROWSER_RELOAD", default=False):
    INSTALLED_APPS += ["django_browser_reload"]

    MIDDLEWARE += ["django_browser_reload.middleware.BrowserReloadMiddleware"]

# Debug toolbar
# https://github.com/jazzband/django-debug-toolbar

if env.bool("USE_DEBUG_TOOLBAR", default=False):
    INSTALLED_APPS += ["debug_toolbar"]

    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]

    DEBUG_TOOLBAR_CONFIG = {
        "ROOT_TAG_EXTRA_ATTRS": "hx-preserve",
        "UPDATE_ON_FETCH": True,
    }

    # INTERNAL_IPS required for debug toolbar
    INTERNAL_IPS = env.list("INTERNAL_IPS", default=["127.0.0.1"])

# PROJECT-SPECIFIC SETTINGS

# Cookie used to check user accepts cookies

GDPR_COOKIE_NAME = "accept-cookies"

# Default page size for paginated views

DEFAULT_PAGE_SIZE = 30

# HTMX configuration
# https://htmx.org/docs/#config

HTMX_CONFIG = {
    "globalViewTransitions": False,
    "scrollBehavior": "instant",
    "scrollIntoViewOnBoost": False,
    "useTemplateFragments": True,
}

# Site meta configuration

META_TAGS = {
    "author": env("META_AUTHOR", default="{{cookiecutter.author}}"),
    "description": env("META_DESCRIPTION", default="{{cookiecutter.description}}"),
    "keywords": env("META_KEYWORDS", default=""),
}

# i18n

LOCALE_PATHS = [BASE_DIR / "locale"]

LANGUAGES = [
    ("en", "English"),
]
{% if cookiecutter.use_storage == 'y' %}

# Media files / Object Storage

MEDIA_URL = env("MEDIA_URL", default="/media/")
MEDIA_ROOT = BASE_DIR / "media"

if env.bool("USE_S3_STORAGE", default=False):
    _base_storages = vars().get("STORAGES", {})
    STORAGES = {
        **_base_storages,
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        },
    }
    AWS_ACCESS_KEY_ID = env("HETZNER_STORAGE_ACCESS_KEY")
    AWS_SECRET_ACCESS_KEY = env("HETZNER_STORAGE_SECRET_KEY")
    AWS_STORAGE_BUCKET_NAME = env("HETZNER_STORAGE_BUCKET")
    AWS_S3_ENDPOINT_URL = env("HETZNER_STORAGE_ENDPOINT")
    AWS_S3_REGION_NAME = env("HETZNER_STORAGE_REGION", default="fsn1")
    AWS_DEFAULT_ACL = "public-read"
    MEDIA_URL = f"{AWS_S3_ENDPOINT_URL.rstrip('/')}/{AWS_STORAGE_BUCKET_NAME}/"
{%- endif %}
{%- if cookiecutter.use_pwa == 'y' %}

# PWA

PWA_CONFIG = {
    "background_color": env("PWA_BACKGROUND_COLOR", default="#ffffff"),
    "description": env("PWA_DESCRIPTION", default="{{cookiecutter.description}}"),
    "theme_color": env("PWA_THEME_COLOR", default="#000000"),
    "assetlinks": {
        "package_name": env("PWA_PACKAGE_NAME", default=""),
        "sha256_fingerprints": env.list("PWA_SHA256_FINGERPRINTS", default=[]),
    },
}
{%- endif %}
