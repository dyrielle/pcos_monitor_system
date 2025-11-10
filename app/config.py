import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    # Core
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")

    # DB
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///pcos_dev.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Mail
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "1") in ("1", "true", "True")
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get(
        "MAIL_DEFAULT_SENDER",
        f"University Research Portal — PCOS Monitor <{MAIL_USERNAME or 'no-reply@example.com'}>"
    )