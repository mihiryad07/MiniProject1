import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

APP_NAME = "Personalized Clothing Recommendation System"
APP_VERSION = "1.0.0"
PAGE_ICON = "👕"

DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "data" / "app.db"))
API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
SECRET_KEY = os.getenv("SECRET_KEY", "development-secret-key")
APP_ENV = os.getenv("APP_ENV", "development")

__all__ = [
    "BASE_DIR",
    "APP_NAME",
    "APP_VERSION",
    "PAGE_ICON",
    "DATABASE_PATH",
    "API_KEY",
    "SECRET_KEY",
    "APP_ENV",
]
