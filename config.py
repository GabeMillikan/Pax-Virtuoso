import os
from contextlib import suppress

from dotenv import load_dotenv

load_dotenv()


def getenv_string(environment_variable: str) -> str:
    if s := os.getenv(environment_variable):
        return s
    msg = f"Required environment variable {environment_variable!r} is not set. Please read ./ENVIRONMENT.md"
    raise OSError(msg)


def getenv_int(environment_variable: str) -> int:
    if s := os.getenv(environment_variable):
        with suppress(ValueError):
            return int(s)

    msg = f"Required environment variable {environment_variable!r} is not set. Please read ./ENVIRONMENT.md"
    raise OSError(msg)


api_token = getenv_string("API_TOKEN")
spotify_client_id = getenv_string("SPOTIFY_CLIENT_ID")
spotify_client_secret = getenv_string("SPOTIFY_CLIENT_SECRET")
dev_guild_id = getenv_int("DEV_GUILD_ID")
