from hvac import exceptions as hvac_exceptions
from rich.console import Console
from rich.prompt import Confirm

from lib.drivers.credentials.hashicorp_vault._main import (
    _get_client,
    ui_get_for_root_token,
    ui_get_user_data,
    ui_select_username,
)
from lib.hvac import create_or_update_user, is_user_exists
from lib.settings import C_BOLD, C_CODE, C_END, C_FILE

console = Console()
ask = Confirm.ask


def ui_action(
    root_token: str = "", user_data: dict = {}, password: str = ""
) -> tuple[str, str]:

    client = _get_client(root_token)
    if not user_data:
        (username, metadata) = ui_select_username(client)
        user_data = ui_get_user_data(
            username,
            metadata["firstname"],
            metadata["lastname"],
            metadata["companyname"],
            metadata["email"],
        )
    else:
        username = user_data["username"]

    if not user_data:
        return ("", "")

    try:
        metadata = user_data["metadata"]
        create_or_update_user(client, username, None, metadata)
        print(f"User {C_FILE}{username}{C_END} updated")
    except hvac_exceptions.InvalidPath as exception:
        raise ValueError(
            f"Vault not initialized (use {C_CODE}dekick credentials run init{C_END} to initialize)"
        ) from exception
    except hvac_exceptions.Forbidden as exception:
        global HVAC_CLIENT  # pylint: disable=global-statement
        HVAC_CLIENT = None
        return ui_action(ui_get_for_root_token(), user_data, password)

    return (username, password)
