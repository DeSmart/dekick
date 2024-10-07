from hvac import exceptions as hvac_exceptions
from rich.console import Console
from rich.prompt import Confirm

from lib.drivers.credentials.hashicorp_vault._main import (
    _get_client,
    generate_word_password,
    ui_get_for_root_token,
    ui_get_user_data,
)
from lib.drivers.credentials.hashicorp_vault.assign_policies import (
    ui_action as assign_policies_ui_action,
)
from lib.hvac import create_or_update_user, is_user_exists
from lib.settings import (
    C_BOLD,
    C_CODE,
    C_END,
    C_FILE,
    DEKICKRC_GLOBAL_HOST_PATH,
    HOST_HOME,
)

console = Console()
ask = Confirm.ask


def ui_action(
    root_token: str = "", user_data: dict = {}, password: str = ""
) -> tuple[str, str]:

    if not user_data:
        user_data = ui_get_user_data()

    if not password:
        password = generate_word_password()

    client = _get_client(root_token)

    if not user_data:
        return ("", "")

    try:
        username = user_data["username"]
        metadata = user_data["metadata"]
        if is_user_exists(client, username):
            print(f"User {C_CODE}{username}{C_END} already exists")
        else:
            create_or_update_user(client, username, password, metadata)
            print(
                f"User {C_FILE}{username}{C_END} created with password {C_FILE}{password}{C_END}"
            )
        print(f"\n{C_BOLD}Choose policies for user {C_CODE}{username}{C_END}")
        assign_policies_ui_action(root_token, username)
        global_host_path = DEKICKRC_GLOBAL_HOST_PATH.replace(HOST_HOME, "~")
        print(
            f"\n{C_BOLD}The user should create a file {global_host_path} with the following content:"
        )
        print(f"\nhashicorp_vault:")
        print(f"  password: {password}")
        print(f"  username: {username}\n")
    except hvac_exceptions.InvalidPath as exception:
        raise ValueError(
            f"Vault not initialized (use {C_CODE}dekick credentials run init{C_END} to initialize)"
        ) from exception
    except hvac_exceptions.Forbidden as exception:
        global HVAC_CLIENT  # pylint: disable=global-statement
        HVAC_CLIENT = None
        return ui_action(ui_get_for_root_token(), user_data, password)

    return (username, password)
