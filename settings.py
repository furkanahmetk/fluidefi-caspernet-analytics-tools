import os
from dotenv import load_dotenv 

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_AUTO_FIELD='django.db.models.AutoField'

DATABASES = {
    "default": {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv('READ_DB_CONNECTION_DATABASE'),
        'USER': os.getenv('READ_DB_CONNECTION_USERNAME'),
        'PASSWORD': os.getenv('READ_DB_CONNECTION_PASSWORD'),
        'HOST': os.getenv('READ_DB_CONNECTION_HOST'),
        'PORT': os.getenv('READ_DB_CONNECTION_PORT'),
    },
    "writer": {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv('WRITE_DB_CONNECTION_DATABASE'),
        'USER': os.getenv('WRITE_DB_CONNECTION_USERNAME'),
        'PASSWORD': os.getenv('WRITE_DB_CONNECTION_PASSWORD'),
        'HOST': os.getenv('WRITE_DB_CONNECTION_HOST'),
        'PORT': os.getenv('WRITE_DB_CONNECTION_PORT'),
    }
}

ALLOWED_HOSTS = ['*', ]

INSTALLED_APPS = [
    'cspr_summarization',
    'rest_framework',
    'rest_framework.authtoken',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'drf_spectacular',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'middleware.DisableClientCachingMiddleware.DisableClientCachingMiddleware',
]


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'cspr_summarization/templates/'),
            os.path.join(BASE_DIR, 'cspr_summarization/templates/liquidity_pools/'),
            os.path.join(BASE_DIR, 'cspr_summarization/templates/portfolio_models/'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'libraries': {
                'string_replace': 'templatetags.string_replace',
                'has_group': 'templatetags.group_filter_tag',
                'escape_string': 'templatetags.escape_tag',
                'account_initialized': 'templatetags.account_init_tag',
                'allow_product_subscription': 'templatetags.allow_product_subscription',
                'account_configured': 'templatetags.account_configured_tag',
                'max_calls': 'templatetags.max_calls_tag',
                'multiplication': 'templatetags.multiplication_tag',
                'allow_local_host': 'templatetags.local_host_tag',
            }
        },
    },
]

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


