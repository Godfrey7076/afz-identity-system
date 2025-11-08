"""
Django settings for afz_core project.
"""

import os
from pathlib import Path
from django.contrib.messages import constants as messages

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-afz-identity-system-2025-air-force-zimbabwe-secure-key'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party apps
    'rest_framework',
    'corsheaders',

    # Your apps
    'identity_verification',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'afz_core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'afz_core.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Custom User Model
AUTH_USER_MODEL = 'identity_verification.CustomUser'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login URLs
LOGIN_REDIRECT_URL = '/verification/enhanced-dashboard/'
LOGIN_URL = '/verification/admin-login/'
LOGOUT_REDIRECT_URL = '/verification/admin-login/'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20
}

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

CORS_ALLOW_CREDENTIALS = True

# Session settings
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Security settings (for production, these should be more strict)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Cache settings
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'afz_system.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'identity_verification': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Message tags for Bootstrap
MESSAGE_TAGS = {
    messages.DEBUG: 'secondary',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# Face Recognition settings
FACE_RECOGNITION_SETTINGS = {
    'TOLERANCE': 0.6,
    'MODEL': 'hog',  # or 'cnn' for better accuracy but slower
    'ENCODINGS_FILE': 'face_encodings.pkl',
    'TEMP_IMAGE_DIR': 'temp/',
}

# AFZ System specific settings
AFZ_SYSTEM = {
    'SYSTEM_NAME': 'Air Force of Zimbabwe Identity System',
    'VERSION': '2.1.0',
    'SECURITY_LEVEL': 'TOP SECRET',
    'SUPPORT_EMAIL': 'support@afz.gov.zw',
    'ADMIN_EMAIL': 'admin@afz.gov.zw',
}

# Email settings (configure for production)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # For development
# For production, use:
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.afz.gov.zw'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'noreply@afz.gov.zw'
# EMAIL_HOST_PASSWORD = 'your-email-password'

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB

# Timeout settings
SESSION_COOKIE_AGE = 3600  # 1 hour in seconds
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

# Custom authentication backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# Security middleware settings
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# AFZ Custom configurations
AFZ_IDENTITY_CONFIG = {
    'MAX_LOGIN_ATTEMPTS': 5,
    'LOCKOUT_TIME': 900,  # 15 minutes in seconds
    'PASSWORD_RESET_TIMEOUT': 86400,  # 24 hours
    'SESSION_TIMEOUT': 3600,  # 1 hour
    'FACE_ENROLLMENT_REQUIRED': True,
    'AUTO_LOGOUT_ENABLED': True,
}

# Django Admin Interface customization
ADMIN_SITE_HEADER = "AFZ Identity System Administration"
ADMIN_SITE_TITLE = "AFZ Identity System"
ADMIN_INDEX_TITLE = "Welcome to AFZ Identity System Administration"

# Development-specific settings
if DEBUG:
    # Additional development settings
    INTERNAL_IPS = [
        '127.0.0.1',
        'localhost',
    ]

    # Debug toolbar (optional)
    try:
        import debug_toolbar
        INSTALLED_APPS += ['debug_toolbar']
        MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    except ImportError:
        pass

# Production-specific settings
if not DEBUG:
    # Security settings for production
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True

    # Logging for production
    LOGGING['handlers']['file']['level'] = 'WARNING'
    LOGGING['loggers']['django']['level'] = 'WARNING'

    # Database for production (example with PostgreSQL)
    # DATABASES = {
    #     'default': {
    #         'ENGINE': 'django.db.backends.postgresql',
    #         'NAME': 'afz_identity_db',
    #         'USER': 'afz_user',
    #         'PASSWORD': 'secure_password',
    #         'HOST': 'localhost',
    #         'PORT': '5432',
    #     }
    # }

# Custom template context processors


def afz_system_info(request):
    return {
        'SYSTEM_NAME': AFZ_SYSTEM['SYSTEM_NAME'],
        'SYSTEM_VERSION': AFZ_SYSTEM['VERSION'],
        'SECURITY_LEVEL': AFZ_SYSTEM['SECURITY_LEVEL'],
    }


# Add custom context processor
TEMPLATES[0]['OPTIONS']['context_processors'].append(
    'afz_core.settings.afz_system_info')
