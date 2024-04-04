from hvac import exceptions as hvac_exceptions
from rich.console import Console
from rich.prompt import Confirm

from lib.drivers.credentials.hashicorp_vault._main import (
    _get_client,
    ui_get_for_root_token,
    ui_select_username,
)
from lib.global_config import get_global_config_value
from lib.hvac import get_entity_by_username
from lib.settings import C_CODE, C_END

console = Console()
ask = Confirm.ask


def ui_action(root_token: str = "") -> bool:
    """Delete user in Hashicorp Vault"""
    client = _get_client(root_token)

    try:
        (username, metadata) = ui_select_username(client)
        current_username = str(
            get_global_config_value("hashicorp_vault.username", False)
        )

        if username == current_username:
            raise ValueError(
                f"You can't delete user {C_CODE}{username}{C_END} that you are currently using to manage Vault. Please use another user to delete this user."
            )

        if not ask(
            f"Are you sure you want to delete user {C_CODE}{username}{C_END}?",
            default=False,
        ) or not ask(
            "Are you really sure? This action is irreversible!", default=False
        ):
            print("User deletion cancelled")
            return False

        entity = get_entity_by_username(client, username)
        client.secrets.identity.delete_entity(entity_id=entity["id"])
        print(f"User {C_CODE}{username}{C_END} deleted")
    except hvac_exceptions.InvalidPath as exception:
        raise ValueError(
            f"Vault not initialized (use {C_CODE}dekick credentials run init{C_END} to initialize)"
        ) from exception
    except hvac_exceptions.Forbidden as exception:
        global HVAC_CLIENT
        HVAC_CLIENT = None
        return ui_action(ui_get_for_root_token())

    return True
