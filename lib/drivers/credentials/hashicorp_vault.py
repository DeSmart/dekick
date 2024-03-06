import hashlib
import random
import re
from argparse import ArgumentParser
from os import mkdir
from time import sleep

import flatdict
import hvac
from beaupy import prompt, select, select_multiple
from beaupy._internals import ValidationError as BeaupyValidationError
from genericpath import exists, isdir
from hvac import exceptions as hvac_exceptions
from requests.exceptions import ConnectionError as RequestConnectionError
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table
from thefuzz import fuzz

from lib.dekickrc import get_dekickrc_value
from lib.dotenv import dict2env, env2dict
from lib.environments import get_environments
from lib.git import is_git_repository
from lib.global_config import get_global_config_value, set_global_config_value
from lib.hvac import (
    add_policies_to_user,
    create_admin_policy,
    create_deployment_policy,
    create_mount_point,
    create_or_update_user,
    create_policy_name,
    create_project_policy,
    create_token,
    create_userpass,
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
    DEKICKRC_GLOBAL_HOST_PATH,
    TERMINAL_COLUMN_WIDTH,
)
from lib.words import get_words
from lib.yaml.reader import read_yaml
from lib.yaml.saver import save_flat

console = Console()
ask = Confirm.ask

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
        ("change_user_password", "Changing user password"),
        (
            "save_user_to_global_config",
            f"Saving username and password to your global config",
        ),
        ("assign_policies", "Assigning policies to user"),
        ("create_deployment_token", "Creating token for CI/CD use"),
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
    client = _get_client(token)
    mount_point = get_mount_point()
    project_name = str(get_dekickrc_value("project.name"))
    project_group = str(get_dekickrc_value("project.group"))
    env_data = read_yaml(DEKICK_HVAC_ENV_FILE, True)["environments"]

    id = next((e["id"] for e in env_data if e["name"] == env), None)

    path = f"{project_group}/{project_name}/{env}/{id}"
    try:
        secrets = client.secrets.kv.v2.read_secret_version(
            path=path, mount_point=mount_point
        )
        return dict2env(secrets["data"]["data"], env)
    except hvac_exceptions.InvalidPath as exception:
        raise ValueError(
            f"Path {mount_point}{path} not found, check your mount_point or initialize Vault with {C_CODE}dekick credentials run init{C_END} command"
        ) from exception
    except hvac_exceptions.Forbidden as exception:
        raise KeyError(
            f"You don't have access to path {mount_point}{path}. Do you have proper access rights?"
        ) from exception

    return ""


def ui_action_init(root_token: str = "") -> bool:
    """Initialize Vault for this project"""
    try:
        client = _get_client(root_token)
        create_mount_point(client)
        ui_enable_userpass_auth_method(client)
        ui_create_dekick_hvac_yaml()
        ui_create_project_policy()
        ui_create_deployment_policy()
        ui_create_admin_policy()
        ui_check_gitignore()
        try:
            get_all_user_data(client)
        except hvac_exceptions.InvalidPath:
            if ask(
                f"Your {info()} does not have any users created yet. Would you like to create a user now?",
                default=False,
            ):
                (username, password) = ui_action_create_user(root_token)
            if ask(
                f"Would you like to save generated user {C_CMD}{username}{C_END} and password to your global {C_FILE}{DEKICKRC_GLOBAL_HOST_PATH}{C_END} config?"
            ):
                set_global_config_value("hashicorp_vault.username", username)
                set_global_config_value("hashicorp_vault.password", password)
        if ask(
            "Would you like to create a deployment token for CI/CD use for this project?"
        ):
            ui_action_create_deployment_token(root_token)
        create_initial_envs()
        print(
            f"Envs directory {C_FILE}{DEKICK_ENVS_DIR}/{C_END} created, please fill it with initial environment variables and run {C_CMD}dekick credentials push{C_END} command to push them to Vault."
        )

        if is_git_repository():
            print(
                f"{C_WARN}\nPlease remember to stage and commit all changes to your Git repository!{C_END}"
            )

    except hvac_exceptions.Forbidden:
        global HVAC_CLIENT  # pylint: disable=global-statement
        HVAC_CLIENT = None
        return ui_action_init(ui_get_for_root_token())

    return True


def create_initial_envs():
    """Create initial environment files"""
    create_envs_dir()
    for env_name in get_environments():
        env_file = f"{DEKICK_ENVS_DIR}/{env_name}.env"
        with open(env_file, "w", encoding="utf-8") as file:
            file.write(dict2env({}, env_name))


def ui_create_project_policy():
    """Create project policy"""
    client = _get_client()
    project_name = str(get_dekickrc_value("project.name"))
    project_group = str(get_dekickrc_value("project.group"))
    run_func(
        text=f"Creating project policies for {C_CMD}{project_group}/{project_name}{C_END}",
        func=lambda: (
            create_project_policy(
                client, project_name, project_group, DEKICK_HVAC_ROLES
            ),
            {"success": True},
        )[1],
    )


def ui_action_create_deployment_token(root_token: str = "") -> bool:
    """Create deployment token in Hashicorp Vault"""
    client = _get_client(root_token)
    try:
        project_group = str(get_dekickrc_value("project.group"))
        project_name = str(get_dekickrc_value("project.name"))
        policy_names = [create_policy_name(project_group, project_name, "deployment")]
        token = create_token(client, policy_names, no_parent=False)
        print(f"Here's your deployment token: {C_CODE}{token}{C_END}")
    except hvac_exceptions.InvalidPath as exception:
        raise ValueError(
            f"Vault not initialized (use {C_CODE}dekick credentials run init{C_END} to initialize)"
        ) from exception
    except hvac_exceptions.Forbidden as exception:
        global HVAC_CLIENT
        HVAC_CLIENT = None
        return ui_action_create_deployment_token(ui_get_for_root_token())

    return True


def ui_action_save_user_to_global_config():
    """Save username and password to global .dekickrc.yml file"""
    username = (
        input(
            "Enter username: ",
        )
    ).strip()
    password = input(
        "Enter password: ",
    ).strip()
    if not ask(
        f"Would you like to save user and password to your global {C_FILE}{DEKICKRC_GLOBAL_HOST_PATH}{C_END} config?\n{C_WARN}Warning: {C_END}Your current settings will be overwritten!"
    ):
        print("Saving cancelled")
        return

    set_global_config_value("hashicorp_vault.username", username)
    set_global_config_value("hashicorp_vault.password", password)
    print("Username and password saved")


def ui_action_change_user_password(root_token: str = "") -> bool:
    """Change user password in Hashicorp Vault"""
    client = _get_client(root_token)

    try:
        username = _ui_select_username(client)
        ask(
            f"Are you sure you want to change password for user {C_CODE}{username}{C_END}?",
            default=False,
        )
        password = _generate_word_password()
        create_userpass(client, username, password)
        print(
            f"Password for user {C_CODE}{username}{C_END} changed to {C_CODE}{password}{C_END}"
            + f"\n{C_BOLD}Remember to inform the user about the new password!{C_END}"
        )
    except hvac_exceptions.InvalidPath as exception:
        raise ValueError(
            f"Vault not initialized (use {C_CODE}dekick credentials run init{C_END} to initialize)"
        ) from exception
    except hvac_exceptions.Forbidden as exception:
        global HVAC_CLIENT
        HVAC_CLIENT = None
        return ui_action_change_user_password(ui_get_for_root_token())

    return True


def ui_create_admin_policy():
    """Create admin policy"""
    client = _get_client()
    run_func(
        text=f"Creating admin policy",
        func=lambda: (create_admin_policy(client), {"success": True})[1],
    )


def ui_create_deployment_policy():
    """Create deployment policy"""
    client = _get_client()
    project_name = str(get_dekickrc_value("project.name"))
    project_group = str(get_dekickrc_value("project.group"))
    run_func(
        text=f"Creating deployment policy for {C_CMD}{project_group}/{project_name}{C_END}",
        func=lambda: (
            create_deployment_policy(client, project_name, project_group),
            {"success": True},
        )[1],
    )


def ui_action_create_user(
    root_token: str = "", user_data: dict = {}, password: str = ""
) -> tuple[str, str]:

    if not user_data:
        user_data = ui_get_user_data()

    if not password:
        password = _generate_word_password()

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
        ui_action_assign_policies(root_token, username)
    except hvac_exceptions.InvalidPath as exception:
        raise ValueError(
            f"Vault not initialized (use {C_CODE}dekick credentials run init{C_END} to initialize)"
        ) from exception
    except hvac_exceptions.Forbidden as exception:
        global HVAC_CLIENT  # pylint: disable=global-statement
        HVAC_CLIENT = None
        return ui_action_create_user(ui_get_for_root_token(), user_data, password)

    return (username, password)


def ui_action_delete_user(root_token: str = "") -> bool:
    """Delete user in Hashicorp Vault"""
    client = _get_client(root_token)

    try:
        username = _ui_select_username(client)
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
        return ui_action_delete_user(ui_get_for_root_token())

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
    ticked_indices = [
        index for index, p in enumerate(policies_filtered) if p in user_policies
    ]

    policy_indexes = select_multiple(
        policies_filtered,
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
        policies_filtered[int(policy_index)] for policy_index in policy_indexes
    ]

    return policy_names


def ui_action_assign_policies(root_token: str = "", username: str = "") -> bool:
    """Assign policies to user in Hashicorp Vault"""
    client = _get_client(root_token)
    try:
        if not username:
            username = _ui_select_username(client)
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
        return ui_action_assign_policies(ui_get_for_root_token())
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

        if not id:
            raise ValueError(
                f"Field {C_CMD}id{C_END} for environment {C_CODE}{env}{C_END} is empty in {C_FILE}{DEKICK_HVAC_ENV_FILE}{C_END} file. Please run {C_CMD}dekick credentials push{C_END} first."
            )

        path = f"{project_group}/{project_name}/{env}/{id}"

        try:
            secrets = client.secrets.kv.v2.read_secret_version(
                path=path, mount_point=mount_point
            )
            return dict2env(secrets["data"]["data"], env)

        except hvac_exceptions.InvalidPath as exception:
            raise ValueError(
                f"Path {mount_point}{path} not found, check your mount_point or initialize Vault with {C_CODE}dekick credentials run init{C_END} command"
            ) from exception

        except hvac_exceptions.Forbidden as exception:
            raise KeyError(
                f"You don't have access to path {mount_point}{path}. Do you have proper access rights?"
            ) from exception

    try:
        yaml_flat = read_yaml(DEKICK_HVAC_ENV_FILE, True)
    except FileNotFoundError:
        print(
            f"{C_ERROR}Error:{C_END} {C_FILE}{DEKICK_HVAC_ENV_FILE}{C_END} file not found. Please run {C_CMD}dekick credentials run init{C_END} to initialize {info()} for this project."
        )
        return False

    for env in yaml_flat["environments"]:
        env_name = env["name"]
        env_id = env["id"]
        env_file = f"{DEKICK_ENVS_DIR}/{env_name}.env"
        with open(env_file, "w", encoding="utf-8") as file:
            file.write(get_envs(env=env_name, id=env_id))

    print(
        f"All environment files pulled and placed in {C_FILE}{DEKICK_ENVS_DIR}/{C_END}{C_WARN} directory.{C_END}"
    )

    return True


def ui_push(root_token: str = "") -> bool:
    """Push all environment variables to Hashicorp Vault"""
    mount_point = get_mount_point()
    project_name = str(get_dekickrc_value("project.name"))
    project_group = str(get_dekickrc_value("project.group"))
    client = _get_client(root_token)

    if not isdir(DEKICK_ENVS_DIR):
        print(
            f"\n{C_BOLD}This is a first run, let me create {C_FILE}{DEKICK_ENVS_DIR}/{C_END} {C_BOLD}dir and all environment files.{C_END}"
        )
        create_envs_dir()

        for env_name in get_environments():
            env_file = f"{DEKICK_ENVS_DIR}/{env_name}.env"
            print(f"Creating file {C_FILE}{env_file}{C_END}")
            with open(env_file, "w", encoding="utf-8") as file:
                file.write("")
            sleep(1)

        print(
            f"\n{C_WARN}Please fill all environment files with proper data and run this command again.{C_END}"
        )
    else:
        try:
            yaml_flat = read_yaml(DEKICK_HVAC_ENV_FILE, True)
        except FileNotFoundError:
            print(
                f"{C_ERROR}Error:{C_END} {C_FILE}{DEKICK_HVAC_ENV_FILE}{C_END} file not found. Please run {C_CMD}dekick credentials run init{C_END} to initialize {info()} for this project."
            )
            return False

        print(f"{C_BOLD}\nPushing environment files to {info()}{C_END}")
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
                print(f"Pushed {C_FILE}{env_file}{C_END} to {C_CMD}{path}{C_END}")

        save_flat(DEKICK_HVAC_ENV_FILE, yaml_flat)
        print(
            f"\n{C_WARN}All environment files pushed, please remember to commit {C_FILE}{DEKICK_HVAC_ENV_FILE}{C_END}{C_WARN} file!{C_END}"
        )

    return True


def ui_check_gitignore():
    """Check if .gitignore file exists"""

    def write_gitignore(mode: str = "w"):
        gitignore_content = (
            f"# DeKick environments\n{DEKICK_ENVS_DIR}/\n{DEKICK_ENVS_DIR}/*\n.env\n"
        )
        with open(".gitignore", mode, encoding="utf-8") as file:
            file.write(gitignore_content)

    if not exists(".gitignore"):
        print(
            f"{C_WARN}Warning:{C_END} {C_FILE}.gitignore{C_END} file not found. I will create one for you."
        )
        write_gitignore("w")
        print(
            f"{C_FILE}.gitignore{C_END} file created and filled, please stage and commit it."
        )
    else:
        with open(".gitignore", "r", encoding="utf-8") as file:
            gitignore = file.read()
            if DEKICK_ENVS_DIR not in gitignore:
                print(
                    f"{C_WARN}Warning:{C_END} {C_FILE}.gitignore{C_END} file exists, does not have a {info()} specific paths in it. I will append it for you."
                )
                write_gitignore("a")


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
    run_func(
        text=f"Enabling userpass auth method",
        func=lambda: (enable_userpass_auth_method(client), {"success": True})[1],
    )


def create_envs_dir():
    """Create envs directory"""
    try:
        mkdir(DEKICK_ENVS_DIR)
    except FileExistsError:
        pass


def ui_get_for_root_token():
    """Ask for root token"""
    try:
        root_token = prompt(
            f"{C_WARN}Warning:{C_END} Current user lacks the necessary privileges to proceed.\nPlease provide your root token to your {info()} ({C_CODE}{VAULT_ADDR}{C_END}) to continue: ",
            secure=True,
            validator=lambda x: len(x) > 0,
        )
    except BeaupyValidationError:
        print(f"{C_ERROR}Error:{C_END} Root token can't be empty")
        return ui_get_for_root_token()
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

    confirm = ask(
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
        username = str(get_global_config_value("hashicorp_vault.username", False))
        password = str(get_global_config_value("hashicorp_vault.password", False))

        if token:
            HVAC_CLIENT = hvac.Client(url=VAULT_ADDR, token=token)
        elif username and password:
            try:
                HVAC_CLIENT = hvac.Client(url=VAULT_ADDR)
                HVAC_CLIENT.auth.userpass.login(username=username, password=password)
            except (
                hvac_exceptions.InvalidRequest,
                hvac_exceptions.Forbidden,
                hvac_exceptions.InternalServerError,
            ):
                HVAC_CLIENT = None
                root_token = ui_get_for_root_token()
                return _get_client(root_token)
            except RequestConnectionError:
                raise RequestConnectionError(
                    f"Can't connect to {info()} using {C_CODE}{VAULT_ADDR}{C_END}. Please check your network connection and try again."
                )
        else:
            HVAC_CLIENT = hvac.Client(url=VAULT_ADDR)

    return HVAC_CLIENT


def _generate_word_password(num_words: int = 8) -> str:
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
