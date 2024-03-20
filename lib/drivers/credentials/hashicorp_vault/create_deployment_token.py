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
from lib.hvac import create_policy_name, create_token
from lib.settings import C_CODE, C_END, C_FILE

console = Console()
ask = Confirm.ask


def ui_action(root_token: str = "") -> bool:
    """Create deployment token in Hashicorp Vault"""
    client = _get_client(root_token)
    try:
        project_group = str(get_dekickrc_value("project.group"))
        project_name = str(get_dekickrc_value("project.name"))
        policy_names = [create_policy_name(project_group, project_name, "deployment")]
        token = create_token(client, policy_names, no_parent=True, renawable=True)

        if ask(
            f"Would you like to store the deployment token in Gitlab under {C_FILE}{DEKICKRC_GITLAB_VAULT_TOKEN_VAR_NAME}{C_END} variable?",
            default=False,
        ):
            set_project_var(
                "*", token, variable_name=DEKICKRC_GITLAB_VAULT_TOKEN_VAR_NAME, raw=True
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
