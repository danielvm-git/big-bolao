"""Configuracao central lida de variaveis de ambiente."""
import os
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv(override=True)


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
APIFOOTBALL_LEAGUE_ID = os.environ.get("APIFOOTBALL_LEAGUE_ID", "")
APIFOOTBALL_SEASON = os.environ.get("APIFOOTBALL_SEASON", "2026")

def validate_config(
    provider: str = RESULTS_PROVIDER,
    key: str = APIFOOTBALL_KEY,
    league_id: str = APIFOOTBALL_LEAGUE_ID,
) -> None:
    """Validates API config. Called at startup and directly in tests."""
    if provider == "apifootball":
        if not key:
            raise RuntimeError(
                "RESULTS_PROVIDER=apifootball mas APIFOOTBALL_KEY nao esta definida no .env")
        if not league_id:
            raise RuntimeError(
                "RESULTS_PROVIDER=apifootball mas APIFOOTBALL_LEAGUE_ID nao esta definida no .env "
                "(use get_leagues para descobrir o ID correto)")
        if league_id == "1":
            import warnings
            warnings.warn(
                "APIFOOTBALL_LEAGUE_ID=1 parece ser o valor padrao antigo. "
                "Verifique se e o ID correto para a Copa 2026 (esperado: 28).",
                stacklevel=2,
            )


# Run at startup — catches misconfiguration before the bot connects to Telegram.
validate_config()

TZ = ZoneInfo(os.environ.get("TIMEZONE", "America/Sao_Paulo"))


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS
