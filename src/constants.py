"""WEBSCRAPING PAGES CONSTANTS"""

from decouple import config

SOURCE_ONE = "https://do512.com"
SOURCE_TWO = "https://heyaustin.com/austin-events/"
SOURCE_THREE = "https://austin.culturemap.com/events/?tags=20240920"

DATABASE_URL = config("DATABASE_URL")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

SECRET_KEY = config("SECRET_KEY")

EVENTS_API_URL = config("EVENTS_API_URL", default="https://atx-events-api-7423eb0d8c65.herokuapp.com/")
MAX_EVENTS_LIMIT = 50

PREDICT_API = config("PREDICT_API")
ACCESS_TOKEN = config("EVENTS_HQ_TOKEN")
