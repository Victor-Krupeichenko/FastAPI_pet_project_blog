import os
from dotenv import load_dotenv

load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")

SECRET_KEY_TOKEN = os.getenv("SECRET_KEY_TOKEN")
ALGORITHM_TOKEN = os.getenv("ALGORITHM_TOKEN")

SECRET_KEY_SESSION = os.getenv("SECRET_KEY_SESSION")

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")

SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = os.getenv("SMTP_PORT")

URL_HOST = os.getenv("URL_HOST")  # Хост приложения
URL_PORT = os.getenv("URL_PORT")  # Порт приложения
