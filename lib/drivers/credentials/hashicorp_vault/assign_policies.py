from beaupy import select_multiple
from hvac import exceptions as hvac_exceptions
from rich.console import Console
from rich.prompt import Confirm

from lib.drivers.credentials.hashicorp_vault._main import (
    DEKICK_HVAC_PAGE_SIZE,
    HVAC_CLIENT,
    _get_client,
    ui_get_for_root_token,
    ui_select_username,
)
from lib.hvac import add_policies_to_user, get_user_policies
from lib.settings import C_BOLD, C_CODE, C_END

console = Console()
ask = Confirm.ask


def ui_action(root_token: str = "", username: str = "") -> bool:
    """Assign policies to user in Hashicorp Vault"""
    client = _get_client(root_token)
    try:
        if not username:
            (username, metadata) = ui_select_username(client)
        user_policies = get_user_policies(client, username)

        policy_names = _ui_select_policies(
            client, user_policies, exclude_deployment_policy=True
        )

        if "admin" in policy_names and not ask(
            f"Are you sure you want to assign {C_BOLD}administrative access (admin){C_END} to user {C_CODE}{username}{C_END}?",
            default=False,
        ):
            print("Policy assignment cancelled")
            return False
    except hvac_exceptions.Forbidden as exception:
        global HVAC_CLIENT
        HVAC_CLIENT = None
        return ui_action(ui_get_for_root_token())
    except hvac_exceptions.InvalidPath as exception:
        raise ValueError(
            f"Vault not initialized (use {C_CODE}dekick credentials run init{C_END} to initialize)"
        ) from exception

    try:
        if policy_names:
            add_policies_to_user(client, username, policy_names)
            print(f"Policies assigned to user {C_CODE}{username}{C_END}")
    except hvac_exceptions.InvalidPath as exception:
        raise ValueError(
            f"Vault not initialized (use {C_CODE}dekick credentials run init{C_END} to initialize)"
        ) from exception

    return True


def _ui_select_policies(
    client,
    user_policies: list[str] = [],
    exclude_deployment_policy: bool = False,
):
    policies = client.sys.list_policies()["data"]["policies"]
    policies_filtered = [
        policy
        for policy in policies
        if not policy.startswith("default")
        and not policy.startswith("root")
        and (not exclude_deployment_policy or "deployment" not in policy)
    ]
    policies_sorted = sorted(policies_filtered)
    ticked_indices = [
        index for index, p in enumerate(policies_sorted) if p in user_policies
    ]
    policy_indexes = select_multiple(
        policies_sorted,
        tick_style="cyan",
        preprocessor=lambda x: (
            x.split(":")[0] + " (" + x.split(":")[1] + ")" if x != "admin" else x
        ),
        cursor_style="magenta",
        return_indices=True,
        ticked_indices=ticked_indices,
        pagination=True,
        page_size=DEKICK_HVAC_PAGE_SIZE,
    )

    policy_names = [
        policies_sorted[int(policy_index)] for policy_index in policy_indexes
    ]

    return policy_names
