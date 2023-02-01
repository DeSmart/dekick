from dotenv import dotenv_values

from lib.settings import C_CMD, C_END, C_FILE


def get_dotenv_var(var: str, default: str = "") -> str:
    """Gets variable var from .env file"""
    config = dotenv_values(".env")

    if var not in config and default == "":
        raise KeyError(
            f"Variable {C_CMD}{var}{C_END} not found in {C_FILE}.env{C_END} file"
        )

    if var not in config and default != "":
        return default

    return str(config[var])
