import hashlib
import random
import re
from argparse import ArgumentParser
from os import mkdir

import flatdict
import hvac
from beaupy import select
from hvac import exceptions as hvac_exceptions
from nltk.corpus import words
from rich.console import Console
from rich.prompt import Confirm
from thefuzz import fuzz

from lib.dekickrc import get_dekickrc_value
from lib.dotenv import dict2env, env2dict
from lib.environments import get_environments
from lib.global_config import get_global_config_value
from lib.hvac import (
    append_policies_to_user,
    create_admin_policy,
    create_mount_point,
    create_or_update_user,
    create_project_policy,
    enable_userpass_auth_method,
    get_all_user_data,
    get_mount_point,
    is_user_exists,
)
from lib.run_func import run_func
from lib.settings import C_CMD, C_CODE, C_END, C_FILE
from lib.words import get_words
from lib.yaml.reader import read_yaml
from lib.yaml.saver import save_flat

console = Console()

VAULT_TOKEN = str(get_global_config_value("hashicorp_vault.token"))
VAULT_ADDR = str(get_dekickrc_value("hashicorp_vault.url"))
HVAC_CLIENT = None
DEKICK_HVAC_ENV_FILE = ".dekick_hvac.yml"
DEKICK_ENVS_DIR = "envs"
DEKICK_HVAC_ROLES = ["developer", "maintainer"]


def get_actions() -> list[tuple[str, str]]:
    """Get available actions for this driver"""
    return [
        ("init", "Initialize Vault for this project"),
        ("create_user", "Create user in Vault"),
        ("list_users", "List all users in Vault"),
        ("search_users", "Search for users in Vault"),
    ]


def info() -> str:
    """Get info about this driver"""
    return "Hashicorp Vault"


def configure():
    """Configure this driver"""
    pass


# pylint: disable=unused-argument
def get_envs(*args, env: str, token: str = "", **kwargs) -> str:
    """Get variables"""
    pass

    return ""


def ui_action_init() -> bool:
    """Initialize Vault for this project"""
    root_token = ui_get_for_root_token_from_cli()
    client = _get_client(root_token)

    ui_create_mount_point(client)
    ui_enable_userpass_auth_method(client)
    create_envs_dir()
    ui_create_dekick_hvac_yaml()
    print("Vault initialized for this project")

    return True


def ui_action_create_user() -> bool:
    root_token = ui_get_for_root_token_from_cli()
    user_data = ui_get_user_data_from_cli()
    password = _generate_word_password()
    client = _get_client(root_token)
    project_name = str(get_dekickrc_value("project.name"))
    project_group = str(get_dekickrc_value("project.group"))

    if not user_data:
        return False

    try:
        username = user_data["username"]
        metadata = user_data["metadata"]
        if is_user_exists(client, username):
            print(f"User {C_CODE}{username}{C_END} already exists")
        else:
            create_or_update_user(client, username, password, metadata)
            print(
                f"User {C_CODE}{username}{C_END} created with password {C_CODE}{password}{C_END}"
            )
    except hvac_exceptions.InvalidPath as exception:
        raise ValueError(
            f"Vault not initialized (use {C_CODE}dekick credentials run init{C_END} to initialize)"
        ) from exception

    if Confirm.ask(
        f"Should this user be given administrative access to Vault, enabling them to manage projects and users?",
        default=False,
    ):
        policy_name = create_admin_policy(client)
        append_policies_to_user(client, username, [policy_name])
    else:
        if Confirm.ask(
            f"Should the user be granted access to this particular project?",
            default=True,
        ):
            console.print(f"\nChoose user's role for this project:")
            role = select(list(DEKICK_HVAC_ROLES), cursor="🢧", cursor_style="cyan")
            console.print(f"Ok, adding role {role} to user policies")
            policy_names = create_project_policy(
                client, project_name, project_group, DEKICK_HVAC_ROLES
            )
            policy_name = policy_names[role]
            append_policies_to_user(client, username, [policy_name])

    return True


def ui_action_list_users() -> bool:
    """List all users in Hashicorp Vault"""
    client = _get_client()

    try:
        user_data = get_all_user_data(client)
        print(f"{C_CODE}Users list:{C_END}")
        for data in user_data:
            console.print(
                f"  {data['username']} ({data['metadata']['firstname']} {data['metadata']['lastname']} {data['metadata']['email']})"
            )
        return True
    except hvac_exceptions.Forbidden as exception:
        raise KeyError(
            f"You don't have access to list users. Check your permissions?"
        ) from exception
    except hvac_exceptions.InvalidPath as exception:
        raise ValueError(
            f"No users to list or vault not initialized (use {C_CODE}dekick credentials run init{C_END} to initialize)"
        ) from exception


def ui_action_search_users() -> bool:
    """Search for users in Hashicorp Vault"""
    client = _get_client()
    try:
        entities = client.secrets.identity.list_entities()
    except hvac_exceptions.InvalidPath as exception:
        raise ValueError(
            f"No users to search or vault not initialized (use {C_CODE}dekick credentials run init{C_END} to initialize)"
        ) from exception

    for entity_id in entities["data"]["key_info"]:
        username = entities["data"]["key_info"][entity_id]["name"]
        entity_info = client.secrets.identity.read_entity(entity_id=entity_id)
        metadata = entity_info["data"]["metadata"]
        entities["data"]["key_info"][entity_id]["metadata"] = metadata
        firstname = (
            metadata["firstname"] if metadata and "firstname" in metadata else ""
        )
        lastname = metadata["lastname"] if metadata and "lastname" in metadata else ""
        email = metadata["email"] if metadata and "email" in metadata else ""
        entities["data"]["key_info"][entity_id][
            "search_str"
        ] = f"{username} {firstname} {lastname} {email}"

    search = input(f"Who do you want to find? ")
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

    print(f"{C_CODE}Users found:{C_END}")
    for entity in matched_entity:
        username = entity["username"]
        firstname = (
            entity["metadata"]["firstname"] if "firstname" in entity["metadata"] else ""
        )
        lastname = (
            entity["metadata"]["lastname"] if "lastname" in entity["metadata"] else ""
        )
        email = entity["metadata"]["email"] if "email" in entity["metadata"] else ""
        hlt = re.sub(
            search,
            f"{C_FILE}{search}{C_END}",
            f"{username} ({firstname} {lastname} {email})",
            flags=re.IGNORECASE,
        )

        print(f" {hlt}")
    return True


def ui_pull() -> bool:
    """Pull all environment variables and save to envs/ dir for further processing"""
    create_envs_dir()
    mount_point = get_mount_point()
    project_name = str(get_dekickrc_value("project.name"))
    project_group = str(get_dekickrc_value("project.group"))
    client = _get_client()

    def get_envs(env: str, id: str) -> str:
        """Get all variables from Hashicorp Vault"""
        path = f"{project_group}/{project_name}/{env}/{id}"

        try:
            secrets = client.secrets.kv.v2.read_secret_version(
                path=path, mount_point=mount_point
            )
            return dict2env(secrets["data"]["data"], env)

        except hvac_exceptions.InvalidPath as exception:
            raise ValueError(
                f"Path {mount_point}{path} not found, check your mount_point"
            ) from exception

        except hvac_exceptions.Forbidden as exception:
            raise KeyError(
                f"You don't have access to path {mount_point}{path}. Do you have proper token?"
            ) from exception

    yaml_flat = read_yaml(DEKICK_HVAC_ENV_FILE)

    for env in yaml_flat["environments"]:
        env_name = env["name"]
        env_id = env["id"]
        env_file = f"{DEKICK_ENVS_DIR}/{env_name}.env"
        with open(env_file, "w", encoding="utf-8") as file:
            file.write(get_envs(env=env_name, id=env_id))

    return True


def ui_push() -> bool:
    """Push all environment variables to Hashicorp Vault"""
    mount_point = get_mount_point()
    project_name = str(get_dekickrc_value("project.name"))
    project_group = str(get_dekickrc_value("project.group"))
    client = _get_client()
    yaml_flat = read_yaml(DEKICK_HVAC_ENV_FILE)

    for env_name in get_environments():
        env_file = f"{DEKICK_ENVS_DIR}/{env_name}.env"

        with open(env_file, "r", encoding="utf-8") as file:
            env_data = dict2env(env2dict(file.read()), env_name)
        with open(env_file, "w", encoding="utf-8") as file:
            file.write(env_data)

        env_id = sha256_checksum(env_file)

        for index, value in enumerate(yaml_flat["environments"]):
            if value["name"] == env_name:
                yaml_flat["environments"][index]["id"] = env_id

        with open(env_file, "r", encoding="utf-8") as file:
            env_data = file.read()
            path = f"{project_group}/{project_name}/{env_name}/{env_id}"
            client.secrets.kv.v2.create_or_update_secret(
                path=path, secret=env2dict(env_data), mount_point=mount_point
            )

    save_flat(DEKICK_HVAC_ENV_FILE, yaml_flat)

    return True


def sha256_checksum(filename, block_size=65536):
    sha256 = hashlib.sha256()
    with open(filename, "rb") as f:
        for block in iter(lambda: f.read(block_size), b""):
            sha256.update(block)
    return sha256.hexdigest()


def ui_create_dekick_hvac_yaml():
    """Create .dekick_hvac.yml file"""

    def wrapper():
        environs = get_environments()
        yaml_flat = {"environments": []}
        for env in environs:
            yaml_flat["environments"].append({"name": env, "id": ""})
        save_flat(DEKICK_HVAC_ENV_FILE, flatdict.FlatDict(yaml_flat))

    return run_func(
        text=f"Creating {C_FILE}{DEKICK_HVAC_ENV_FILE}{C_END} file",
        func=wrapper,
    )


def ui_enable_userpass_auth_method(client):
    """Enable userpass auth method"""

    def wrapper():
        enable_userpass_auth_method(client)

    run_func(text=f"Enabling userpass auth method", func=wrapper)

    return {"success": True}


def ui_create_mount_point(client):
    """Create mount point"""

    def wrapper():
        create_mount_point(client)

    run_func(text=f"Creating mount point {C_CODE}dekick{C_END}", func=wrapper)

    return {"success": True}


def create_envs_dir():
    """Create envs directory"""

    try:
        mkdir(DEKICK_ENVS_DIR)
    except FileExistsError:
        pass


def ui_get_for_root_token_from_cli():
    """Ask for root token"""
    root_token = input(
        f"Enter your Hashicorp Vault ({C_CODE}{VAULT_ADDR}{C_END}) root token: "
    )
    return root_token


def ui_get_user_data_from_cli() -> dict:
    """Ask for username"""
    username = (input(f"Enter username you want to create: ")).strip()
    firstname = (input(f"Enter firstname for {C_CMD}{username}{C_END}: ")).strip()
    lastname = (input(f"Enter lastname for {C_CMD}{username}{C_END}: ")).strip()
    email = (input(f"Enter email for {C_CMD}{username}{C_END}: ")).strip()

    confirm = Confirm.ask(
        f"Should I create user {C_CODE}{username}{C_END} with firstname {C_CODE}{firstname}{C_END}, lastname {C_CODE}{lastname}{C_END} and email {C_CODE}{email}{C_END}?",
        default=True,
    )

    if not confirm:
        print("User creation cancelled")
        return {}

    return {
        "username": username,
        "metadata": {"firstname": firstname, "lastname": lastname, "email": email},
    }


def arguments(sub_command: str, parser: ArgumentParser):
    """Parse arguments for this driver"""
    parser.add_argument(
        "--token",
        required=False,
        help=f"set {info()} token",
    )


def _get_client(vault_token: str = "") -> hvac.Client:
    global HVAC_CLIENT  # pylint: disable=global-statement

    if not vault_token:
        vault_token = VAULT_TOKEN

    if not HVAC_CLIENT:
        HVAC_CLIENT = hvac.Client(url=VAULT_ADDR, token=vault_token or VAULT_TOKEN)

    return HVAC_CLIENT


def _generate_word_password(num_words: int = 5) -> str:
    """Generate a password consisting of random English words and numbers."""
    password = ""
    words = get_words()
    while len(password) > 71 or len(password) == 0:
        selected_words = random.sample(words, num_words)
        password = "-".join(selected_words) + str(random.randint(10, 99))
        num_words -= 1
    return password
