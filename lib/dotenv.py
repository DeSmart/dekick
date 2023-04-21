from dotenv import dotenv_values

from lib.settings import C_CMD, C_END, C_FILE


def get_dotenv_var(var: str, default: str = "", path: str = "") -> str:
    """Gets variable var from .env file"""

    path_parsed = path

    if path != "" and not path.endswith("/"):
        path_parsed = f"{path}/"

    config = dotenv_values(f"{path_parsed}.env")

    if var not in config and default == "":
        raise KeyError(
            f"Variable {C_CMD}{var}{C_END} not found in {C_FILE}{path}.env{C_END} file"
        )

    if var not in config and default != "":
        return default

    return str(config[var])


def dict2env(env: dict) -> str:
    """Convert dict `env` to .env format"""

    def parse_value(value: str) -> str:
        """Adds quotes to value if needed"""
        if '"' in value:
            value = f'"{value}"'
        return value

    return "\n".join([f"{key}={parse_value(str(value))}" for key, value in env.items()])
