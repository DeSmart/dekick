from rich.console import Console
from rich.prompt import Confirm

from lib.global_config import set_global_config_value
from lib.settings import C_END, C_FILE, C_WARN, DEKICKRC_GLOBAL_HOST_PATH

console = Console()
ask = Confirm.ask


def ui_action():
    """Save username and password to global .dekickrc.yml file"""
    username = (
        input(
            "Enter username: ",
        )
    ).strip()
    password = input(
        "Enter password: ",
    ).strip()
    if not ask(
        f"Would you like to save user and password to your global {C_FILE}{DEKICKRC_GLOBAL_HOST_PATH}{C_END} config?\n{C_WARN}Warning: {C_END}Your current settings will be overwritten!"
    ):
        print("Saving cancelled")
        return

    set_global_config_value("hashicorp_vault.username", username)
    set_global_config_value("hashicorp_vault.password", password)
    print("Username and password saved")
