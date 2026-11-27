"""Create a project-local environment file without displaying the access token."""

from getpass import getpass
from pathlib import Path

from dotenv import set_key

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
DEFAULT_MODEL = "system.ai.gpt-oss-120b"


def write_project_env(
    host: str, token: str, model: str, path: Path | None = None
) -> None:
    if not host.strip():
        raise ValueError("The Databricks workspace URL must not be empty")
    if not token.strip():
        raise ValueError("The access token must not be empty")
    if not model.strip():
        raise ValueError("The model must not be empty")
    if path is None:
        path = ENV_PATH
    set_key(path, "APP_DATABRICKS_HOST", host)
    set_key(path, "APP_DATABRICKS_TOKEN", token)
    set_key(path, "APP_DATABRICKS_MODEL", model)


def main() -> None:
    host = input("Databricks workspace URL (for example https://adb-123.4.azuredatabricks.net): ").strip()
    token = getpass("Databricks access token (input hidden): ")
    model = input(f"Model service [{DEFAULT_MODEL}]: ").strip() or DEFAULT_MODEL
    write_project_env(host, token, model)
    print(f"Project settings saved to {ENV_PATH.name}.")


if __name__ == "__main__":
    main()
