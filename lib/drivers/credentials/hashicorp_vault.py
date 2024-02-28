import hashlib
import random
import re
import sys
from argparse import ArgumentParser
from os import mkdir

import flatdict
import hvac
from beaupy import prompt, select, select_multiple
from hvac import exceptions as hvac_exceptions
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table
from thefuzz import fuzz

from lib.dekickrc import get_dekickrc_value
from lib.dotenv import dict2env, env2dict
from lib.environments import get_environments
from lib.global_config import get_global_config_value
from lib.hvac import (
    add_policies_to_user,
    append_policies_to_user,
    create_admin_policy,
    create_mount_point,
    create_or_update_user,
    create_project_policy,
    enable_userpass_auth_method,
    get_all_user_data,
    get_entity_by_username,
    get_mount_point,
    get_user_policies,
    is_user_exists,
)
from lib.run_func import run_func
from lib.settings import (
    C_BOLD,
    C_CMD,
    C_CODE,
    C_END,
    C_ERROR,
    C_FILE,
    C_WARN,
    TERMINAL_COLUMN_WIDTH,
)
from lib.words import get_words
from lib.yaml.reader import read_yaml
from lib.yaml.saver import save_flat

console = Console()

VAULT_ADDR = str(get_dekickrc_value("hashicorp_vault.url"))
HVAC_CLIENT = None
DEKICK_HVAC_ENV_FILE = ".dekick_hvac.yml"
DEKICK_ENVS_DIR = "envs"
DEKICK_HVAC_ROLES = ["developer", "maintainer"]
DEKICK_HVAC_PAGE_SIZE = 30


def get_actions() -> list[tuple[str, str]]:
    """Get available actions for this driver"""
    return [
        ("init", "Initializing Vault for this project"),
        ("create_user", "Creating user"),
        ("delete_user", "Deleting user"),
        ("assign_policies", "Assigning policies to user"),
        ("list_users", "Listing users"),
        ("search_users", "Searching for users"),
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


def ui_action_init(root_token: str = "") -> bool:
    """Initialize Vault for this project"""
    try:
        client = _get_client(root_token)
        create_mount_point(client)
        ui_enable_userpass_auth_method(client)
        create_envs_dir()
        ui_create_dekick_hvac_yaml()
        ui_create_project_policy()
        ui_create_admin_policy()
    except hvac_exceptions.Forbidden:
        global HVAC_CLIENT  # pylint: disable=global-statement
        HVAC_CLIENT = None
        return ui_action_init(ui_get_for_root_token())

    return True


def ui_create_project_policy() -> bool:
    """Create project policy"""
    client = _get_client()
    project_name = str(get_dekickrc_value("project.name"))
    project_group = str(get_dekickrc_value("project.group"))

    def wrapper():
        create_project_policy(client, project_name, project_group, DEKICK_HVAC_ROLES)
        return {"success": True}

    run_func(
        text=f"Creating project policies for {C_CMD}{project_group}/{project_name}{C_END}",
        func=wrapper,
    )

    return True


def ui_create_admin_policy() -> bool:
    """Create admin policy"""
    client = _get_client()

    def wrapper():
        create_admin_policy(client)
        return {"success": True}

    run_func(
        text=f"Creating admin policy",
        func=wrapper,
    )

    return True


def ui_action_create_user(root_token: str = "") -> bool:
    user_data = ui_get_user_data()
    password = _generate_word_password()
    client = _get_client(root_token)

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
                f"User {C_FILE}{username}{C_END} created with password {C_FILE}{password}{C_END}"
            )
        print(f"\n{C_BOLD}Choose policies for user {C_CODE}{username}{C_END}")
        ui_action_assign_policies(root_token, username)
    except hvac_exceptions.InvalidPath as exception:
        raise ValueError(
            f"Vault not initialized (use {C_CODE}dekick credentials run init{C_END} to initialize)"
        ) from exception
    except hvac_exceptions.Forbidden as exception:
        global HVAC_CLIENT  # pylint: disable=global-statement
        HVAC_CLIENT = None
        return ui_action_init(ui_get_for_root_token())

    return True


def ui_action_delete_user(root_token: str = "") -> bool:
    """Delete user in Hashicorp Vault"""
    client = _get_client(root_token)

    try:
        username = _ui_select_username(client)
        current_username = str(get_global_config_value("hashicorp_vault.username"))

        if username == current_username:
            raise ValueError(
                f"You can't delete user {C_CODE}{username}{C_END} that you are currently using to manage Vault. Please use another user to delete this user."
            )

        if not Confirm.ask(
            f"Are you sure you want to delete user {C_CODE}{username}{C_END}?",
            default=False,
        ) or not Confirm.ask(
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
        return ui_action_delete_user(ui_get_for_root_token())

    return True


def ui_action_assign_policies(root_token: str = "", username: str = "") -> bool:
    """Assign policies to user in Hashicorp Vault"""
    client = _get_client(root_token)
    try:
        if not username:
            username = _ui_select_username(client)
        user_policies = get_user_policies(client, username)

        policies = client.sys.list_policies()["data"]["policies"]
        policies_filtred = [
            policy
            for policy in policies
            if not policy.startswith("default") and not policy.startswith("root")
        ]
        ticked_indices = [
            index for index, p in enumerate(policies_filtred) if p in user_policies
        ]

        policy_indexes = select_multiple(
            policies_filtred,
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

        policy_names = []
        for policy_index in policy_indexes:
            policy_names.append(policies_filtred[int(policy_index)])

        if "admin" in policy_names and not Confirm.ask(
            f"Are you sure you want to assign {C_BOLD}administrative access (admin){C_END} to user {C_CODE}{username}{C_END}?",
            default=False,
        ):
            print("Policy assignment cancelled")
            return False
    except hvac_exceptions.Forbidden as exception:
        global HVAC_CLIENT
        HVAC_CLIENT = None
        return ui_action_assign_policies(ui_get_for_root_token())

    try:
        if policy_names:
            add_policies_to_user(client, username, policy_names)
            print(f"Policies assigned to user {C_CODE}{username}{C_END}")
    except hvac_exceptions.InvalidPath as exception:
        raise ValueError(
            f"Vault not initialized (use {C_CODE}dekick credentials run init{C_END} to initialize)"
        ) from exception

    return True


def ui_action_list_users(root_token: str = "") -> bool:
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
            users_table.add_row(
                data["username"],
                data["metadata"]["firstname"],
                data["metadata"]["lastname"],
                data["metadata"]["email"],
                data["metadata"]["companyname"],
                "\n".join(groups),
                "\n".join(projects),
                "\n".join(roles),
            )
        console.print(users_table)
        return True
    except hvac_exceptions.Forbidden as exception:
        global HVAC_CLIENT  # pylint: disable=global-statement
        HVAC_CLIENT = None
        return ui_action_list_users(ui_get_for_root_token())
    except hvac_exceptions.InvalidPath as exception:
        raise ValueError(
            f"No users to list or vault not initialized (use {C_CODE}dekick credentials run init{C_END} to initialize)"
        ) from exception


def ui_action_search_users() -> bool:
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
        metadata = entity_info["data"]["metadata"]
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
        firstname = entity["metadata"]["firstname"]
        lastname = entity["metadata"]["lastname"]
        companyname = entity["metadata"]["companyname"]
        email = entity["metadata"]["email"] if "email" in entity["metadata"] else ""
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
            firstname,
            lastname,
            email,
            companyname,
            "\n".join(groups),
            "\n".join(projects),
            "\n".join(roles),
        )

    console.print(users_table)

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
                f"You don't have access to path {mount_point}{path}. Do you have proper access rights?"
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


def create_envs_dir():
    """Create envs directory"""

    try:
        mkdir(DEKICK_ENVS_DIR)
    except FileExistsError:
        pass


def ui_get_for_root_token():
    """Ask for root token"""
    root_token = prompt(
        f"{C_WARN}Warning:{C_END} Current user lacks the necessary privileges to proceed.\nPlease provide your root token to your Vault ({C_CODE}{VAULT_ADDR}{C_END}) to continue: ",
        secure=True,
        validator=lambda x: len(x) > 0,
    )
    return root_token


def ui_get_user_data(
    username: str = "",
    firstname: str = "",
    lastname: str = "",
    companyname: str = "",
    email: str = "",
) -> dict:
    """Ask for username"""

    if not username:
        username = (input(f"Enter username you want to create: ")).strip()
        if not username:
            print(f"{C_ERROR}Error:{C_END} Username can't be empty")
            return ui_get_user_data()

    if not firstname:
        firstname = (input(f"Enter firstname for {C_CMD}{username}{C_END}: ")).strip()
        if not firstname:
            print(f"{C_ERROR}Error:{C_END} Firstname can't be empty")
            return ui_get_user_data(username)

    if not lastname:
        lastname = (input(f"Enter lastname for {C_CMD}{username}{C_END}: ")).strip()
        if not lastname:
            print(f"{C_ERROR}Error:{C_END} Lastname can't be empty")
            return ui_get_user_data(username, firstname)

    if not companyname:
        companyname = (
            input(f"Enter company name for {C_CMD}{username}{C_END}: ")
        ).strip()
        if not companyname:
            print(f"{C_ERROR}Error:{C_END} Company name can't be empty")
            return ui_get_user_data(username, firstname, lastname)

    if not email:
        email = (input(f"Enter email for {C_CMD}{username}{C_END}: ")).strip()
        if not email:
            print(f"{C_ERROR}Error:{C_END} Email can't be empty")
            return ui_get_user_data()
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            print(f"{C_ERROR}Error:{C_END} Invalid email format!")
            return ui_get_user_data(username, firstname, lastname, companyname)

    confirm = Confirm.ask(
        f"""Is this ok?
    User name: {C_CODE}{username}{C_END}
    First name: {C_CODE}{firstname}{C_END}
    Last name: {C_CODE}{lastname}{C_END}
    Company name: {C_CODE}{companyname}{C_END}
    E-mail: {C_CODE}{email}{C_END}
""",
        default=True,
    )

    if not confirm:
        print("User creation cancelled")
        return {}

    return {
        "username": username,
        "metadata": {
            "firstname": firstname,
            "lastname": lastname,
            "email": email,
            "companyname": companyname,
        },
    }


def arguments(sub_command: str, parser: ArgumentParser):
    """Parse arguments for this driver"""
    parser.add_argument(
        "--token",
        required=False,
        help=f"set {info()} token",
    )


def _get_client(token: str = "") -> hvac.Client:
    global HVAC_CLIENT  # pylint: disable=global-statement

    if not HVAC_CLIENT:
        username = str(get_global_config_value("hashicorp_vault.username"))
        password = str(get_global_config_value("hashicorp_vault.password"))

        if token:
            HVAC_CLIENT = hvac.Client(url=VAULT_ADDR, token=token)
        elif username and password:
            try:
                HVAC_CLIENT = hvac.Client(url=VAULT_ADDR)
                HVAC_CLIENT.auth.userpass.login(username=username, password=password)
            except (hvac_exceptions.InvalidRequest, hvac_exceptions.Forbidden):
                HVAC_CLIENT = None
                root_token = ui_get_for_root_token()
                return _get_client(root_token)
        else:
            HVAC_CLIENT = hvac.Client(url=VAULT_ADDR)

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


def _ui_select_username(
    client, page_size: int = DEKICK_HVAC_PAGE_SIZE, pagination: bool = True
) -> str:
    """Select username from list of users"""
    user_data = get_all_user_data(client)
    sorted_user_data = sorted(user_data, key=lambda x: x["username"])
    users = []
    for user in sorted_user_data:
        users.append(
            f"{user['username']} ({user['metadata']['firstname']} {user['metadata']['lastname']}, {user['metadata']['email']})"
        )

    user_index = select(
        users,
        cursor="🢧",
        cursor_style="cyan",
        return_index=True,
        page_size=page_size,
        pagination=pagination,
    )
    username = sorted_user_data[int(user_index)]["username"]
    print(f"{C_CMD}{C_BOLD}{username}{C_END}")
    return username


def _create_users_table(permissions: bool = True):
    """Create a table for listing users."""
    table = Table(
        show_header=True,
        header_style="bold",
        width=TERMINAL_COLUMN_WIDTH,
    )
    table.add_column("Username", style="white")
    table.add_column("First name", style="magenta")
    table.add_column("Last name", style="magenta")
    table.add_column("Email", style="blue")
    table.add_column("Company", style="blue")

    if permissions:
        table.add_column("Group", style="green", justify="center")
        table.add_column("Project", style="green", justify="center")
        table.add_column("Role", style="green", justify="center")
    return table
