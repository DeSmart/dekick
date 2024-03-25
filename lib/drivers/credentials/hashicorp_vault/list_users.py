from hvac import exceptions as hvac_exceptions
from rich.console import Console
from rich.prompt import Confirm

from lib.drivers.credentials.hashicorp_vault._main import (
    _create_users_table,
    _get_client,
    _prepare_metadata,
    ui_get_for_root_token,
)
from lib.hvac import get_all_user_data, get_user_policies
from lib.settings import C_CODE, C_END

console = Console()
ask = Confirm.ask


def ui_action(root_token: str = "") -> bool:
    """List all users in Hashicorp Vault"""
    client = _get_client(root_token)

    users_table = _create_users_table()
    try:
        user_data = get_all_user_data(client)
        for data in user_data:
            user_policies = get_user_policies(client, data["username"])
            groups = []
            projects = []
            roles = []

            for user_policy in user_policies:
                if user_policy == "admin":
                    groups.append("-")
                    projects.append("-")
                    roles.append("admin")
                else:
                    groups.append(user_policy.split("/")[0])
                    projects.append(user_policy.split("/")[1].split(":")[0])
                    roles.append(user_policy.split(":")[1])
            metadata = _prepare_metadata(data["metadata"])
            users_table.add_row(
                data["username"],
                metadata["firstname"],
                metadata["lastname"],
                metadata["email"],
                metadata["companyname"],
                "\n".join(groups),
                "\n".join(projects),
                "\n".join(roles),
            )
        console.print(users_table)
        return True
    except hvac_exceptions.Forbidden as exception:
        global HVAC_CLIENT  # pylint: disable=global-statement
        HVAC_CLIENT = None
        return ui_action(ui_get_for_root_token())
    except hvac_exceptions.InvalidPath as exception:
        raise ValueError(
            f"No users to list or vault not initialized (use {C_CODE}dekick credentials run init{C_END} to initialize)"
        ) from exception
