import flatdict
from genericpath import exists
from hvac import exceptions as hvac_exceptions
from rich.console import Console
from rich.prompt import Confirm

from lib.dekickrc import get_dekickrc_value
from lib.drivers.credentials.hashicorp_vault._main import (
    DEKICK_ENVS_DIR,
    DEKICK_HVAC_ENV_FILE,
    DEKICK_HVAC_ROLES,
    _get_client,
    info,
    ui_get_for_root_token,
)
from lib.drivers.credentials.hashicorp_vault.create_deployment_token import (
    ui_action as ui_action_create_deployment_token,
)
from lib.drivers.credentials.hashicorp_vault.create_user import (
    ui_action as ui_action_create_user,
)
from lib.environments import get_environments
from lib.git import is_git_repository
from lib.global_config import set_global_config_value
from lib.hvac import (
    create_admin_policy,
    create_deployment_policy,
    create_mount_point,
    create_project_policy,
    enable_userpass_auth_method,
    get_all_user_data,
)
from lib.run_func import run_func
from lib.settings import C_CMD, C_END, C_FILE, C_WARN, DEKICKRC_GLOBAL_HOST_PATH
from lib.yaml.saver import save_flat

console = Console()
ask = Confirm.ask


def ui_action(root_token: str = "") -> bool:
    """Initialize Vault for this project"""
    try:
        client = _get_client(root_token)
        create_mount_point(client)
        _ui_enable_userpass_auth_method(client)
        _ui_create_dekick_hvac_yaml()
        _ui_create_project_policy()
        _ui_create_deployment_policy()
        _ui_create_admin_policy()
        _ui_check_gitignore()
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
            "Would you like to create a deployment token for CI/CD use for this project?",
            default=False,
        ):
            ui_action_create_deployment_token(root_token)

        if is_git_repository():
            print(
                f"{C_WARN}\nPlease remember to stage and commit all changes to your Git repository!{C_END}"
            )

    except hvac_exceptions.Forbidden:
        global HVAC_CLIENT  # pylint: disable=global-statement
        HVAC_CLIENT = None
        return ui_action(ui_get_for_root_token())

    return True


def _ui_create_dekick_hvac_yaml():
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


def _ui_enable_userpass_auth_method(client):
    """Enable userpass auth method"""
    run_func(
        text=f"Enabling userpass auth method",
        func=lambda: (enable_userpass_auth_method(client), {"success": True})[1],
    )


def _ui_create_project_policy():
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


def _ui_create_admin_policy():
    """Create admin policy"""
    client = _get_client()
    run_func(
        text=f"Creating admin policy",
        func=lambda: (create_admin_policy(client), {"success": True})[1],
    )


def _ui_create_deployment_policy():
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


def _ui_check_gitignore():
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
