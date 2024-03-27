from hvac import exceptions as hvac_exceptions
from rich.console import Console
from rich.prompt import Confirm

from lib.drivers.credentials.hashicorp_vault._main import (
    _get_client,
    generate_word_password,
    ui_get_for_root_token,
    ui_select_username,
)
from lib.global_config import get_global_config_value, set_global_config_value
from lib.hvac import create_userpass
from lib.settings import C_BOLD, C_CODE, C_END, C_FILE, DEKICKRC_GLOBAL_HOST_PATH

console = Console()
ask = Confirm.ask


def ui_action(root_token: str = "") -> bool:
    """Change user password in Hashicorp Vault"""
    client = _get_client(root_token)

    try:
        (username, metadata) = ui_select_username(client)
        if not ask(
            f"Are you sure you want to change password for user {C_CODE}{username}{C_END}?",
            default=False,
        ):
            print("Change password canceled")
            return False
        password = generate_word_password()
        create_userpass(client, username, password)
        print(
            f"Password for user {C_CODE}{username}{C_END} changed to {C_CODE}{password}{C_END}"
        )

        global_username = get_global_config_value("hashicorp_vault.username", False)

        if global_username == username:
            set_global_config_value("hashicorp_vault.password", password)
            print(
                f"Password for user {C_CODE}{username}{C_END} changed and saved to global {C_FILE}{DEKICKRC_GLOBAL_HOST_PATH}{C_END} config"
            )
        else:
            print(
                f"\n{C_BOLD}Remember to inform the user about the new password!{C_END}"
            )

    except hvac_exceptions.InvalidPath as exception:
        raise ValueError(
            f"Vault not initialized (use {C_CODE}dekick credentials run init{C_END} to initialize)"
        ) from exception
    except hvac_exceptions.Forbidden as exception:
        global HVAC_CLIENT
        HVAC_CLIENT = None
        return ui_action(ui_get_for_root_token())

    return True
