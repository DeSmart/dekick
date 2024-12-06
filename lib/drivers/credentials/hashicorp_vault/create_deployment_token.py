from beaupy import prompt
from hvac import exceptions as hvac_exceptions
from rich.console import Console
from rich.prompt import Confirm

from lib.dekickrc import get_dekickrc_value
from lib.drivers.credentials.hashicorp_vault._main import (
    DEKICKRC_GITLAB_VAULT_TOKEN_VAR_NAME,
    _get_client,
    ui_get_for_root_token,
)
from lib.glcli import set_project_var
from lib.hvac import create_policy_name, create_token, get_max_ttl_for_token
from lib.settings import C_CODE, C_END, C_ERROR, C_FILE

console = Console()
ask = Confirm.ask


def ui_action(root_token: str = "") -> bool:
    """Create deployment token in Hashicorp Vault"""
    client = _get_client(root_token)
    try:
        project_group = str(get_dekickrc_value("project.group"))
        project_name = str(get_dekickrc_value("project.name"))
        policy_names = [create_policy_name(project_group, project_name, "deployment")]

        while True:
            max_ttl_days = int(get_max_ttl_for_token(client) / 3600 / 24)
            try:
                ttl_days = prompt(
                    f"What would be the expiration time for the token in days (max is {max_ttl_days} days)?",
                    target_type=int,
                    initial_value=str(max_ttl_days),
                )
                ttl_hours = int(ttl_days * 24)
            except Exception:
                print(f"{C_ERROR}Error:{C_END} Please enter a number")
                continue

            if ttl_days > max_ttl_days:
                print(
                    f"{C_ERROR}Error:{C_END} Maximum token expiration time is {max_ttl_days} days"
                )
                continue
            break

        token = create_token(
            client, policy_names, no_parent=True, renewable=True, ttl=f"{ttl_hours}h"
        )

        if ask(
            f"Would you like to store the deployment token in Gitlab under {C_FILE}{DEKICKRC_GITLAB_VAULT_TOKEN_VAR_NAME}{C_END} variable?",
            default=False,
        ):
            set_project_var(
                "*",
                token,
                variable_name=DEKICKRC_GITLAB_VAULT_TOKEN_VAR_NAME,
                raw=True,
                masked=True,
            )
            print(
                f"Deployment token stored in GitLab under {C_FILE}{DEKICKRC_GITLAB_VAULT_TOKEN_VAR_NAME}{C_END} variable"
            )
        else:
            print(f"Ok, here's your deployment token: {C_CODE}{token}{C_END}")
    except hvac_exceptions.InvalidPath as exception:
        raise ValueError(
            f"Vault not initialized (use {C_CODE}dekick credentials run init{C_END} to initialize)"
        ) from exception
    except hvac_exceptions.Forbidden as exception:
        global HVAC_CLIENT
        HVAC_CLIENT = None
        return ui_action(ui_get_for_root_token())

    return True
    return True
