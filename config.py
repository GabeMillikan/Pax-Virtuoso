import os

from dotenv import load_dotenv

load_dotenv()


def must_getenv_string(environment_variable: str) -> str:
    s = os.getenv(environment_variable)

    if not s:
        raise Exception(
            f"Required environment variable {environment_variable!r} is not set. Please read ./ENVIRONMENT.md"
        )

    return s


api_token = must_getenv_string("API_TOKEN")
# TODO: the bot will _probably_ have more configuration options
