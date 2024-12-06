import hashlib
import random
import re
from argparse import ArgumentParser
from logging import debug
from os import mkdir
from os.path import isfile
from shutil import copyfile
from time import sleep

import hvac
from beaupy import prompt, select
from beaupy._internals import ValidationError as BeaupyValidationError
from genericpath import exists, isdir
from hvac import exceptions as hvac_exceptions
from requests.exceptions import ConnectionError as RequestConnectionError
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

from lib.dekickrc import get_dekickrc_value
from lib.dotenv import dict2env, env2dict
from lib.environments import get_environments
from lib.git import is_git_repository
from lib.global_config import get_global_config_value
from lib.hvac import get_all_user_data, get_mount_point, get_user_policies
from lib.logger import get_log_level
from lib.misc import run_shell
from lib.settings import (
    C_BOLD,
    C_CMD,
    C_CODE,
    C_END,
    C_ERROR,
    C_FILE,
    C_WARN,
    DEKICKRC_GLOBAL_HOST_PATH,
    HOST_HOME,
    TERMINAL_COLUMN_WIDTH,
)
from lib.words import get_words
from lib.yaml.reader import read_yaml
from lib.yaml.saver import save_flat

console = Console()
ask = Confirm.ask

HVAC_CLIENT = None
HVAC_USERNAME = None
DEKICK_HVAC_ENV_FILE = ".dekick_hvac.yml"
DEKICK_ENVS_DIR = "envs"
DEKICK_HVAC_ROLES = ["developer", "maintainer"]
DEKICK_HVAC_PAGE_SIZE = 20
DEKICKRC_GITLAB_VAULT_TOKEN_VAR_NAME = "VAULT_TOKEN"
MAINTAINER_CACHE = None


def arguments(sub_command: str, parser: ArgumentParser):
    """Parse arguments for this driver"""
    parser.add_argument(
        "--token",
        required=False,
        help=f"set {info()} token",
    )


def get_actions() -> list[tuple[str, str]]:
    """Get available actions for this driver"""

    dekickrc_global_without_home = DEKICKRC_GLOBAL_HOST_PATH.replace(HOST_HOME, "~")

    return [
        ("Init", "Initializing Vault for this project"),
        ("Create_user", "Creating user"),
        ("Delete_user", "Deleting user"),
        ("Edit_user", "Editing user"),
        ("Change_user_password", "Changing user's password"),
        (
            "Save_user_to_global_config",
            f"Saving user and password to global config {dekickrc_global_without_home}",
        ),
        ("Assign_policies", "Assigning policies to user"),
        ("Create_deployment_Token", "Creating token for CI/CD use"),
        ("List_users", "Listing users"),
        ("Search_users", "Searching for users"),
        ("Migrate_from_Gitlab", f"Migrating the project from GitLab to {info()}"),
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

    if not id:
        raise ValueError(
            f"I can't get env variables because field {C_CMD}id{C_END} for environment {C_CODE}{env}{C_END} is empty in {C_FILE}{DEKICK_HVAC_ENV_FILE}{C_END} file."
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


def ui_pull(root_token: str = "") -> bool:
    """Pull all environment variables and save to envs/ dir for further processing"""
    mount_point = get_mount_point()
    project_name = str(get_dekickrc_value("project.name"))
    project_group = str(get_dekickrc_value("project.group"))
    client = _get_client(root_token)

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

    environments = yaml_flat["environments"]
    create_envs_dir()

    for env in environments:
        env_name = env.get("name")
        env_id = env.get("id")
        env_prev_id = env.get("prev_id", "")

        if _is_maintainer() and env_name == "production" and env_prev_id:
            env_id = env_prev_id

        if _is_developer() and env_name == "production":
            env_id = ""

        if exists(f"{DEKICK_ENVS_DIR}/{env_name}.env") and _is_maintainer():
            if ask(
                f"{C_WARN}Warning:{C_END} Overwrite existing {C_FILE}{DEKICK_ENVS_DIR}/{env_name}.env{C_END} file?",
                default=False,
            ):
                copy_from = f"{DEKICK_ENVS_DIR}/{env_name}.env"
                copy_to = f"{DEKICK_ENVS_DIR}/{env_name}.env.bak"
                print(
                    f"  Overwriting {C_FILE}{copy_from}{C_END}, but nonethless created a copy for you here {C_FILE}{copy_to}{C_END} :)"
                )
                copyfile(copy_from, copy_to)
            else:
                print(f"  Skipping {C_FILE}{DEKICK_ENVS_DIR}/{env_name}.env{C_END}")
                continue

        if env_id == "":
            envs_content = dict2env({}, env_name)
            if _is_maintainer() or env_name != "production":
                print(
                    f"{C_WARN}Warning:{C_END} Creating initial, empty {C_FILE}{DEKICK_ENVS_DIR}/{env_name}.env{C_END} file."
                )
        else:
            envs_content = get_envs(env=env_name, id=env_id)

        if _is_maintainer() or env_name != "production":
            env_file = f"{DEKICK_ENVS_DIR}/{env_name}.env"
            with open(env_file, "w", encoding="utf-8") as file:
                file.write(envs_content)

    print(
        f"\nAll environment files pulled and placed in {C_FILE}{DEKICK_ENVS_DIR}/{C_END}{C_WARN} directory.{C_END}"
        + f"\nFill it with proper data and run {C_CMD}dekick credentials push{C_END} command to push them to {info()}."
    )

    return True


def ui_push(root_token: str = "", no_confirm: bool = False) -> bool:
    """Push all environment variables to Hashicorp Vault"""
    mount_point = get_mount_point()
    project_name = str(get_dekickrc_value("project.name"))
    project_group = str(get_dekickrc_value("project.group"))
    client = _get_client(root_token)

    try:
        yaml_flat = read_yaml(DEKICK_HVAC_ENV_FILE, True)
    except FileNotFoundError:
        print(
            f"{C_ERROR}Error:{C_END} {C_FILE}{DEKICK_HVAC_ENV_FILE}{C_END} file not found. Please run {C_CMD}dekick credentials run init{C_END} to initialize {info()} for this project."
        )
        return False

    all_ids_filled = all(env.get("id") for env in yaml_flat["environments"])

    if not isdir(DEKICK_ENVS_DIR) and not all_ids_filled:
        print(
            f"\n{C_BOLD}This is a first run, let me create {C_FILE}{DEKICK_ENVS_DIR}/{C_END} {C_BOLD}dir and all environment files.{C_END}"
        )
        create_envs_dir()

        for env_name in get_environments():
            env_file = f"{DEKICK_ENVS_DIR}/{env_name}.env"
            print(f"Creating file {C_FILE}{env_file}{C_END}")
            with open(env_file, "w", encoding="utf-8") as file:
                file.write(dict2env({}, env_name))
            sleep(1)

        if isfile(".env") and ask(
            f"Would you like to copy your local .env file to {C_FILE}{DEKICK_ENVS_DIR}/local.env{C_END}?"
        ):
            copyfile(".env", f"{DEKICK_ENVS_DIR}/local.env")

        print(
            f"\n{C_WARN}Please fill all environment files in {C_FILE}{DEKICK_ENVS_DIR}/{C_END}{C_WARN} dir with proper data and run this command again.{C_END}"
        )
    else:

        if not isdir(DEKICK_ENVS_DIR):
            print(
                f"{C_ERROR}Error:{C_END} {C_FILE}{DEKICK_ENVS_DIR}/{C_END} directory not found. Please run {C_CMD}dekick credentials pull{C_END} first."
            )
            return False

        environments = get_environments()

        if no_confirm is False and not ask(
            f"Are you sure you want to push environment files to {info()}?",
            default=False,
        ):
            return True

        print(f"{C_BOLD}\nPushing environment files to {info()}{C_END}")
        for env_name in environments:
            env_file = f"{DEKICK_ENVS_DIR}/{env_name}.env"

            if _is_maintainer() or env_name != "production":
                with open(env_file, "r", encoding="utf-8") as file:
                    env_data = dict2env(env2dict(file.read()), env_name)
                with open(env_file, "w", encoding="utf-8") as file:
                    file.write(env_data)
                env_id = sha256_checksum(env_file)
            else:
                env_id = ""

            for index, value in enumerate(yaml_flat["environments"]):
                if value["name"] == env_name:
                    prev_id = yaml_flat["environments"][index]["id"]
                    if env_id == "" and prev_id != "":
                        yaml_flat["environments"][index]["prev_id"] = prev_id
                    if _is_maintainer() and yaml_flat["environments"][index].get(
                        "prev_id"
                    ):
                        del yaml_flat["environments"][index]["prev_id"]
                    yaml_flat["environments"][index]["id"] = env_id

            if _is_maintainer() or env_name != "production":
                with open(env_file, "r", encoding="utf-8") as file:
                    env_data = file.read()
                    path = f"{project_group}/{project_name}/{env_name}/{env_id}"
                    client.secrets.kv.v2.create_or_update_secret(
                        path=path, secret=env2dict(env_data), mount_point=mount_point
                    )
                    print(f"Pushing {C_FILE}{env_file}{C_END} to {C_CMD}{path}{C_END}")

        save_flat(DEKICK_HVAC_ENV_FILE, yaml_flat)

        if is_git_repository():
            if not ask(
                f"\nDo you want to stage {C_FILE}{DEKICK_HVAC_ENV_FILE}{C_END} file?",
                default=False,
            ):
                print(
                    f"\n{C_WARN}Remember to add and commit {C_FILE}{DEKICK_HVAC_ENV_FILE}{C_END} file manually!{C_END}"
                )
                remove_envs_dir()
                return True
            run_shell(["git", "add", DEKICK_HVAC_ENV_FILE], {})

        print(
            f"\n{C_WARN}All environment files pushed, please remember to commit {C_FILE}{DEKICK_HVAC_ENV_FILE}{C_END}{C_WARN} file!{C_END}"
        )

        remove_envs_dir()

    return True


def remove_envs_dir():
    """Remove envs directory"""
    try:
        run_shell(["rm", "-rf", DEKICK_ENVS_DIR], {})
    except FileNotFoundError:
        pass


def sha256_checksum(filename, block_size=65536):
    sha256 = hashlib.sha256()
    with open(filename, "rb") as f:
        for block in iter(lambda: f.read(block_size), b""):
            sha256.update(block)
    return sha256.hexdigest()


def create_envs_dir():
    """Create envs directory"""
    try:
        mkdir(DEKICK_ENVS_DIR)
    except FileExistsError:
        pass


def ui_get_for_root_token(retries: int = 1):
    """Ask for root token"""
    MAX_RETRIES = 5
    try:
        root_token = prompt(
            f"{C_WARN}Warning:{C_END} Current user lacks the necessary privileges to proceed.\nPlease provide your root token to your {info()} ({C_CODE}{_get_vault_url()}{C_END}) to continue: ",
            secure=True,
            validator=lambda x: len(x) > 0 and "hvs" in x,
        )
    except BeaupyValidationError:
        if retries >= MAX_RETRIES:
            raise ValueError(f"You have exceeded the maximum number of retries.")
        print(
            f"{C_ERROR}Error:{C_END} Root token can't be empty and has to contain hvs"
        )
        retries += 1
        return ui_get_for_root_token(retries)
    return root_token


def ui_get_user_data(
    username: str = "",
    firstname: str = "",
    lastname: str = "",
    companyname: str = "",
    email: str = "",
    skip_fields: list = [],
) -> dict:
    """Ask for user data and validate it."""

    fields = {
        "username": {
            "validator": lambda x: len(x) > 0,
            "name": "Username",
            "value": username,
        },
        "firstname": {
            "validator": lambda x: len(x) > 0,
            "name": "First name",
            "value": firstname,
        },
        "lastname": {
            "validator": lambda x: len(x) > 0,
            "name": "Last name",
            "value": lastname,
        },
        "companyname": {
            "validator": lambda x: len(x) > 0,
            "name": "Company name",
            "value": companyname,
        },
        "email": {
            "validator": lambda x: bool(re.match(r"[^@]+@[^@]+\.[^@]+", x)),
            "name": "E-mail",
            "value": email,
        },
    }

    for varname in fields:
        try:
            if skip_fields and varname in skip_fields:
                continue

            fields[varname]["value"] = prompt(
                fields[varname]["name"],
                initial_value=fields[varname]["value"],
                raise_validation_fail=False,
            )

            if fields[varname]["validator"](fields[varname]["value"]) is False:
                raise BeaupyValidationError()

            fields[varname]["value"] = fields[varname]["value"].strip()

            skip_fields.append(varname)
        except BeaupyValidationError:
            print(f"{C_ERROR}Error:{C_END} Wrong {fields[varname]['name']}.")
            return ui_get_user_data(
                fields["username"]["value"],
                fields["firstname"]["value"],
                fields["lastname"]["value"],
                fields["companyname"]["value"],
                fields["email"]["value"],
                skip_fields=skip_fields,
            )

    confirm = ask(
        f"""Is this ok?
    User name: {C_CODE}{fields['username']['value']}{C_END}
    First name: {C_CODE}{fields['firstname']['value']}{C_END}
    Last name: {C_CODE}{fields['lastname']['value']}{C_END}
    Company name: {C_CODE}{fields['companyname']['value']}{C_END}
    E-mail: {C_CODE}{fields['email']['value']}{C_END}
""",
        default=True,
    )

    if not confirm:
        print("User creation/edit cancelled")
        return {}

    return {
        "username": fields["username"]["value"],
        "metadata": {
            "firstname": fields["firstname"]["value"],
            "lastname": fields["lastname"]["value"],
            "email": fields["email"]["value"],
            "companyname": fields["companyname"]["value"],
        },
    }


def _get_client(token: str = "") -> hvac.Client:
    global HVAC_CLIENT, HVAC_USERNAME  # pylint: disable=global-statement

    try:
        if HVAC_CLIENT:
            try:
                token_info = HVAC_CLIENT.auth.token.lookup_self()
                debug(
                    f"Token info - renewable: {token_info['renewable']}, ttl: {token_info['ttl']}"
                )
            except Exception as e:
                debug(f"Error looking up token: {str(e)}")

            _renew_token_self(HVAC_CLIENT)
            return HVAC_CLIENT

        username = str(get_global_config_value("hashicorp_vault.username", False))
        password = str(get_global_config_value("hashicorp_vault.password", False))

        HVAC_CLIENT = hvac.Client(url=_get_vault_url())
        if token:
            HVAC_CLIENT.token = token
            HVAC_USERNAME = None
        elif username and password:
            HVAC_CLIENT.auth.userpass.login(username=username, password=password)
            HVAC_USERNAME = username

        _renew_token_self(HVAC_CLIENT)
        return HVAC_CLIENT
    except (
        hvac_exceptions.InvalidRequest,
        hvac_exceptions.Forbidden,
        hvac_exceptions.InternalServerError,
    ) as exception:

        if "lease is not renewable" in str(exception) or "invalid lease ID" in str(
            exception
        ):
            return HVAC_CLIENT

        HVAC_CLIENT = None
        HVAC_USERNAME = None
        if not token:
            root_token = ui_get_for_root_token()
            return _get_client(root_token)
        raise ValueError("Invalid token or token expired.")
    except RequestConnectionError:
        raise RequestConnectionError(
            f"Can't connect to {info()} using {C_CODE}{_get_vault_url()}{C_END}. Please check your network connection and try again."
        )


def _get_loggedin_user() -> str:
    if HVAC_USERNAME:
        return HVAC_USERNAME
    return ""


def _renew_token_self(client: hvac.Client):
    auto_token_renewal = get_dekickrc_value("hashicorp_vault.auto_token_renewal")
    if bool(auto_token_renewal) is False:
        return

    debug("Renewing token")
    client.auth.token.renew_self()

    if get_log_level() == "DEBUG":
        token = client.auth.token.lookup_self()
        debug("Token: %s" % (token))


def generate_word_password(num_words: int = 8) -> str:
    """Generate a password consisting of random English words and numbers."""
    password = ""
    words = get_words()
    while len(password) > 71 or len(password) == 0:
        selected_words = random.sample(words, num_words)
        password = "-".join(selected_words) + str(random.randint(10, 99))
        num_words -= 1
    return password


def ui_select_username(
    client, page_size: int = DEKICK_HVAC_PAGE_SIZE, pagination: bool = True
) -> tuple[str, dict]:
    """Select username from list of users"""
    user_data = get_all_user_data(client)
    sorted_user_data = sorted(user_data, key=lambda x: x["username"])
    users = []
    for user in sorted_user_data:
        metadata = _prepare_metadata(user["metadata"])
        users.append(
            f"{user['username']} ({metadata['firstname']} {metadata['lastname']}, {metadata['email']})"
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
    return (
        username,
        _prepare_metadata(sorted_user_data[int(user_index)]["metadata"]),
    )


def _prepare_metadata(metadata: dict) -> dict:
    """Process metadata, return always every field even if metadata is empty"""
    keys = ["firstname", "lastname", "email", "companyname"]
    return {
        key: metadata.get(key, "") if metadata and key in metadata else ""
        for key in keys
    }


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


def _is_maintainer() -> bool:

    global MAINTAINER_CACHE  # pylint: disable=global-statement

    if MAINTAINER_CACHE is not None:
        return MAINTAINER_CACHE

    client = _get_client()
    username = _get_loggedin_user()

    if not username:
        return True

    user_policies = get_user_policies(client, username)
    project_group = str(get_dekickrc_value("project.group"))
    project_name = str(get_dekickrc_value("project.name"))
    is_maintainer = (
        False
        if "admin" not in user_policies
        and not f"{project_group}/{project_name}:maintainer" in user_policies
        else True
    )
    MAINTAINER_CACHE = is_maintainer
    return is_maintainer


def _is_developer() -> bool:
    return not _is_maintainer()


def _get_vault_url() -> str:
    return str(get_dekickrc_value("hashicorp_vault.url"))
