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

INSTALLED_APPS = ("cspr_summarization",)