from hvac import exceptions as hvac_exceptions
from rich.console import Console
from rich.prompt import Confirm
from thefuzz import fuzz

from lib.drivers.credentials.hashicorp_vault._main import (
    _create_users_table,
    _get_client,
    _prepare_metadata,
)
from lib.hvac import get_user_policies
from lib.settings import C_CODE, C_END

console = Console()
ask = Confirm.ask


def ui_action() -> bool:
    """Search for users in Hashicorp Vault"""
    client = _get_client()
    users_table = _create_users_table()
    try:
        entities = client.secrets.identity.list_entities()
    except hvac_exceptions.InvalidPath as exception:
        raise ValueError(
            f"No users to search or vault not initialized (use {C_CODE}dekick credentials run init{C_END} to initialize)"
        ) from exception

    for entity_id in entities["data"]["key_info"]:
        username = entities["data"]["key_info"][entity_id]["name"]
        entity_info = client.secrets.identity.read_entity(entity_id=entity_id)
        metadata = _prepare_metadata(entity_info["data"]["metadata"])
        entities["data"]["key_info"][entity_id]["metadata"] = metadata
        entities["data"]["key_info"][entity_id][
            "search_str"
        ] = f"{username} {metadata['firstname']} {metadata['lastname']} {metadata['email']} {metadata['companyname']}"

    search = input(
        f"Who do you want to find (you can search by username, first name, last name, email and company name)? "
    )
    matched_entity = []
    for entity_id, entity in entities["data"]["key_info"].items():
        username = entity["name"]
        metadata = entity["metadata"] or {}
        search_str = entity["search_str"]
        ratio = fuzz.partial_ratio(search, search_str)
        if ratio >= 85:
            matched_entity.append(
                {
                    "username": username,
                    "id": entity_id,
                    "entity": entity,
                    "metadata": metadata,
                }
            )

    for entity in matched_entity:
        username = entity["username"]
        metadata = _prepare_metadata(entity["metadata"])
        user_policies = get_user_policies(client, username)
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

        users_table.add_row(
            username,
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
