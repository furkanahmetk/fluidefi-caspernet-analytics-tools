import os
from dotenv import load_dotenv 

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
DEFAULT_AUTO_FIELD='django.db.models.AutoField'

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

DEBUG = True

ALLOWED_HOSTS = ['*', ]


# Application definition

INSTALLED_APPS = [
    'cspr_api',
    'rest_framework',
    'rest_framework.authtoken',
    'drf_spectacular',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'middleware.DisableClientCachingMiddleware.DisableClientCachingMiddleware',
]

ROOT_URLCONF = 'cspr_api.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'cspr_api/templates/'),
            os.path.join(BASE_DIR, 'cspr_api/templates/liquidity_pools/'),
            os.path.join(BASE_DIR, 'cspr_api/templates/portfolio_models/'),
            ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            # 'libraries': {
            #     'string_replace': 'templatetags.string_replace',
            #     'has_group': 'templatetags.group_filter_tag',
            #     'escape_string': 'templatetags.escape_tag',
            #     'account_initialized': 'templatetags.account_init_tag',
            #     'allow_product_subscription': 'templatetags.allow_product_subscription',
            #     'account_configured': 'templatetags.account_configured_tag',
            #     'max_calls': 'templatetags.max_calls_tag',
            #     'multiplication': 'templatetags.multiplication_tag',
            #     'allow_local_host': 'templatetags.local_host_tag',
            # }
        },
    },
]

WSGI_APPLICATION = 'cspr_api.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    "default": {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv('API_READ_DB_CONNECTION_DATABASE'),
        'USER': os.getenv('API_READ_DB_CONNECTION_USERNAME'),
        'PASSWORD': os.getenv('API_READ_DB_CONNECTION_PASSWORD'),
        'HOST': os.getenv('API_READ_DB_CONNECTION_HOST'),
        'PORT': os.getenv('API_READ_DB_CONNECTION_PORT'),
    },
    "writer": {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv('API_WRITE_DB_CONNECTION_DATABASE'),
        'USER': os.getenv('API_WRITE_DB_CONNECTION_USERNAME'),
        'PASSWORD': os.getenv('API_WRITE_DB_CONNECTION_PASSWORD'),
        'HOST': os.getenv('API_WRITE_DB_CONNECTION_HOST'),
        'PORT': os.getenv('API_WRITE_DB_CONNECTION_PORT'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field


REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'STRICT_JSON': False,
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'FLUIDEFI API Documentation',
    'VERSION': '0.10',
    'AUTHENTICATION_WHITELIST': ['rest_framework.authentication.TokenAuthentication'],
}