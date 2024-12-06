"""Set of helper functions to interact with HashiCorp Vault."""

from logging import debug
from typing import Union

from hvac import Client
from hvac import exceptions as hvac_exceptions

from lib.dekickrc import get_dekickrc_value
from lib.environments import get_environments


def create_mount_point(client: Client):
    """Create a project (mountpoint) in Vault."""
    mount_point = get_mount_point()
    mounted_secrets_engines = client.sys.list_mounted_secrets_engines()

    if mount_point not in mounted_secrets_engines["data"]:
        client.sys.enable_secrets_engine(
            backend_type="kv",
            path=mount_point,
            options={"version": 2, "max_versions": 1},
            description=f"DeKick environment variables",
        )


def get_mount_point() -> str:
    """Get the mount point from Vault."""
    mount_point = str(get_dekickrc_value("hashicorp_vault.mount_point"))
    if not mount_point.endswith("/"):
        mount_point += "/"
    return mount_point


def create_admin_policy(client: Client) -> str:
    """Create an admin policy in Vault."""
    mount_point = get_dekickrc_value("hashicorp_vault.mount_point")
    admin_policy = f"""
    {{
        "path": {{
            "sys/auth": {{
                "capabilities": ["create", "read", "update", "delete", "list", "sudo"]
            }},
            "sys/auth/*": {{
                "capabilities": ["create", "read", "update", "delete", "list", "sudo"]
            }},
            "sys/mounts": {{
                "capabilities": ["create", "read", "update", "delete", "list", "sudo"]
            }},
            "sys/mounts/*": {{
                "capabilities": ["create", "read", "update", "delete", "list", "sudo"]
            }},
            "auth/*": {{
                "capabilities": ["create", "read", "update", "delete", "list", "sudo"]
            }},
            "{mount_point}/*": {{
                "capabilities": ["create", "read", "update", "delete", "list"]
            }},
            "{mount_point}/data/*": {{
                "capabilities": ["create", "read", "update", "delete", "list"]
            }},
            "{mount_point}/metadata/*": {{
                "capabilities": ["list", "read"]
            }},
            "sys/policy": {{
                "capabilities": ["create", "read", "update", "delete", "list", "sudo"]
            }},
            "sys/policy/*": {{
                "capabilities": ["create", "read", "update", "delete", "list", "sudo"]
            }},
            "sys/policies/*": {{
                "capabilities": ["create", "read", "update", "delete", "list", "sudo"]
            }},
            "identity/*": {{
                "capabilities": ["create", "read", "update", "delete", "list", "sudo"]
            }}
        }}
    }}
    """
    policy_name = "admin"
    client.sys.create_or_update_policy(name=policy_name, policy=admin_policy)
    return policy_name


def create_project_policy(
    client, project_name: str, project_group: str, roles: list
) -> dict:
    """Create a policy in Vault."""
    path = _create_path(project_name, project_group)
    mount_point = get_dekickrc_value("hashicorp_vault.mount_point")
    environs = get_environments()
    policy_names = {}

    for role in roles:

        policy = f"""
            path "{mount_point}/*" {{
                capabilities = ["list"]
            }}
            path "{mount_point}/{path}/*" {{
                capabilities = ["list"]
            }}
        """

        for env in environs:
            if role == "developer" and env == "production":
                continue

            policy += f"""
            path "{mount_point}/data/{path}/{env}/*" {{
                capabilities = ["read", "update", "list", "create", "patch"]
            }}
        """
        policy_name = create_policy_name(project_group, project_name, role)
        policy_names[role] = policy_name
        client.sys.create_or_update_policy(name=policy_name, policy=policy)

    return policy_names


def create_deployment_policy(
    client: Client, project_name: str, project_group: str
) -> str:
    """Create a deployment policy in Vault."""
    path = _create_path(project_name, project_group)
    mount_point = get_dekickrc_value("hashicorp_vault.mount_point")
    policy = f"""
    path "{mount_point}/*" {{
        capabilities = ["list"]
    }}
    path "{mount_point}/{path}/*" {{
        capabilities = ["list"]
    }}
    path "{mount_point}/data/{path}/*" {{
        capabilities = ["read", "list"]
    }}
    """
    policy_name = create_policy_name(project_group, project_name, "deployment")
    client.sys.create_or_update_policy(name=policy_name, policy=policy)
    return policy_name


def get_max_ttl_for_token(client: Client) -> int:
    """Get the maximum TTL for a token in Vault."""
    return int(client.sys.read_auth_method_tuning(path="token")["max_lease_ttl"])


def create_token(
    client: Client,
    policies: list,
    ttl="768h",
    no_parent: bool = False,
    renewable: bool = True,
) -> str:
    """Create a token in Vault and return it"""

    debug(
        f"Creating token with policies: {policies}, ttl: {ttl}, renewable: {renewable}, no_parent: {no_parent}"
    )
    res = client.auth.token.create(
        policies=policies, ttl=ttl, renewable=renewable, no_parent=no_parent
    )
    debug(f"Token created: {res['auth']['client_token']}")

    return res["auth"]["client_token"]


def append_policies_to_user(client: Client, username: str, policies: list[str]):
    """Append policies to a user in Vault."""
    try:
        user_policies = get_user_policies(client, username)
        combined_policies = list(set(user_policies + policies))
    except hvac_exceptions.InvalidPath:
        combined_policies = policies

    add_policies_to_user(client, username, combined_policies)


def add_policies_to_user(client: Client, username: str, policies: list[str]):
    """Add policies to a user in Vault."""
    entity_id = get_entity_by_username(client, username)["id"]
    client.secrets.identity.create_or_update_entity(
        name=username, entity_id=entity_id, policies=policies
    )


def get_all_user_data(client: Client) -> list[dict]:
    """Get all user names from Vault."""
    entities = client.secrets.identity.list_entities()
    user_data = []
    for entity_id in entities["data"]["keys"]:
        entity_info = client.secrets.identity.read_entity(entity_id=entity_id)
        metadata = entity_info["data"]["metadata"]
        entities["data"]["key_info"][entity_id]["metadata"] = metadata
        user_data.append(
            {
                "username": entities["data"]["key_info"][entity_id]["name"],
                "entity_id": entity_id,
                "metadata": metadata,
            }
        )
    return user_data


def is_user_exists(client: Client, username: str) -> bool:
    """Check if a user exists in Vault."""
    try:
        get_entity_by_username(client, username)
        return True
    except hvac_exceptions.InvalidPath:
        return False


def get_user_policies(client: Client, username: str) -> list[str]:
    """Read policies for an entity in Vault."""
    entity = get_entity_by_username(client, username)
    return entity["policies"]


def get_entity_by_username(client: Client, username: str):
    """Read an entity by name in Vault."""
    entity_response = client.secrets.identity.read_entity_by_name(name=username)
    return entity_response["data"]


def enable_userpass_auth_method(client: Client):
    """Enable userpass auth method in Vault."""
    # Check if userpass auth method is already enabled
    auth_methods = client.sys.list_auth_methods()
    userpass_enabled = any(
        auth_method
        for auth_method, details in auth_methods["data"].items()
        if details["type"] == "userpass"
    )

    # Enable userpass auth method if not already enabled
    if not userpass_enabled:
        client.sys.enable_auth_method(method_type="userpass")
        debug("Userpass auth method has been enabled.")
    else:
        debug("Userpass auth method is already enabled.")


def create_entity_by_username(client: Client, username: str, metadata: dict) -> str:
    """Create an entity in Vault."""
    entity_response = client.secrets.identity.create_or_update_entity_by_name(
        name=username, metadata=metadata
    )

    if isinstance(entity_response, dict):
        return entity_response["data"]["id"]

    return ""


def create_or_update_user(
    client: Client, username: str, password: Union[str, None], metadata: dict
):
    """Create or update a user in Vault."""
    if not is_user_exists(client, username):
        create_userpass(client, username, password)

        entity_id = create_entity_by_username(client, username, metadata)
        if entity_id:
            create_alias(client, username, entity_id)
    else:
        client.secrets.identity.create_or_update_entity_by_name(
            name=username, metadata=metadata
        )


def create_userpass(client: Client, username: str, password: Union[str, None]):
    """Create a user in Vault."""
    client.auth.userpass.create_or_update_user(
        username=username, password=password, policies=["default"]
    )


def create_alias(client: Client, username: str, entity_id: str):
    """Create an alias for an entity in Vault."""
    userpass_mount_accessor = _get_userpass_mount_accessor(client)
    client.secrets.identity.create_or_update_entity_alias(
        name=username,
        canonical_id=entity_id,
        mount_accessor=userpass_mount_accessor,
    )


def create_policy_name(project_group: str, project_name: str, role: str) -> str:
    """Create a policy name for the project."""
    return f"{project_group}/{project_name}:{role}"


def _get_userpass_mount_accessor(client: Client) -> str:
    """Get the accessor for the userpass auth method."""
    auth_methods = client.sys.list_auth_methods()
    return next(
        (
            details["accessor"]
            for auth_method, details in auth_methods["data"].items()
            if details["type"] == "userpass"
        ),
        "",
    )


def _create_path(project_name: str, project_group: str) -> str:
    """Create a path for the project."""
    return f"{project_group}/{project_name}"
