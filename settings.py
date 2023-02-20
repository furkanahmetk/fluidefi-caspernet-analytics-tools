import os
from dotenv import load_dotenv 

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_AUTO_FIELD='django.db.models.AutoField'

DATABASES = {
    "default": {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv('DB_CONNECTION_DATABASE'),
        'USER': os.getenv('DB_CONNECTION_USERNAME'),
        'PASSWORD': os.getenv('DB_CONNECTION_PASSWORD'),
        'HOST': os.getenv('DB_CONNECTION_HOST'),
        'PORT': os.getenv('DB_CONNECTION_PORT'),
    }
}

INSTALLED_APPS = ("cspr_summarization",)
