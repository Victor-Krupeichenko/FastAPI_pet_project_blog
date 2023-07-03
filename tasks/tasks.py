import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from celery import Celery
from src.settings_env import REDIS_HOST, REDIS_PORT, SMTP_HOST, SMTP_USER, SMTP_PASSWORD, SMTP_PORT, URL_HOST, URL_PORT

celery = Celery("tasks", broker=f"redis://{REDIS_HOST}:{REDIS_PORT}/0", broker_connection_retry_on_startup=True)

url_address = f"http://{URL_HOST}:{URL_PORT}"


@celery.task
def send_email_login(username: str, user_email):
    """Отправляет письмо на email указанный пользователем при регистрации"""
    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = user_email
    msg["Subject"] = f"Registration on the site FastAPI app"

    # Форматирование текста письма с использованием HTML
    message = f"Admin: {username.title()}, Thank you for registering on the site. "
    message += f"Click <a href='{url_address}'>here</a> to visit the site."

    # Добавление текста письма как HTML-части
    msg.attach(MIMEText(message, "html"))
    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(msg["From"], msg["To"], msg.as_string())
        return {"message": "sent email"}
    except smtplib.SMTPException as ex:
        return {'Sending error email:': f"{ex}"}
