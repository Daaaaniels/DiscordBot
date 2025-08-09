import os
from dotenv import load_dotenv

# Load from .env for local dev, no effect on Railway
load_dotenv()
try:
    from dotenv import load_dotenv
    load_dotenv()
except ModuleNotFoundError:
    pass


def _to_int(key: str) -> int | None:
    v = os.getenv(key, "").strip()
    try:
        return int(v) if v else None
    except ValueError:
        return None


DISCORD_TOKEN: str | None = os.getenv("DISCORD_TOKEN")
GENESIS_GUILD_ID: int | None = _to_int("GENESIS_GUILD_ID")
REVIEW_CHANNEL_ID: int | None = _to_int("REVIEW_CHANNEL_ID")
