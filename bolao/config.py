"""Configuracao central lida de variaveis de ambiente."""
import os
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()


def _ids(raw: str) -> set[int]:
    return {int(x) for x in raw.replace(" ", "").split(",") if x}


TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GRUPO_CHAT_ID = int(os.environ.get("GRUPO_CHAT_ID", "0") or "0")
ADMIN_IDS = _ids(os.environ.get("ADMIN_IDS", ""))

BIGBASE_URL = os.environ.get("BIGBASE_URL", "https://bigbase.click").rstrip("/")
BIGBASE_EMAIL = os.environ["BIGBASE_EMAIL"]
BIGBASE_PASSWORD = os.environ["BIGBASE_PASSWORD"]

RESULTS_PROVIDER = os.environ.get("RESULTS_PROVIDER", "").strip().lower()
APIFOOTBALL_KEY = os.environ.get("APIFOOTBALL_KEY", "")
APIFOOTBALL_LEAGUE_ID = os.environ.get("APIFOOTBALL_LEAGUE_ID", "1")
APIFOOTBALL_SEASON = os.environ.get("APIFOOTBALL_SEASON", "2026")

TZ = ZoneInfo(os.environ.get("TIMEZONE", "America/Sao_Paulo"))


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS
