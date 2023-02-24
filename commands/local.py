"""
Runs the specified command
"""
import logging
import os
import re
import sys
from argparse import ArgumentParser, Namespace
from importlib import import_module
from shutil import move

from rich.console import Console
from rich.prompt import Confirm
from rich.traceback import install

from commands.docker_compose import docker_compose
from commands.stop import stop
from commands.update import update
from lib import logger
from lib.dekickrc import compare_dekickrc_file, get_dekickrc_value
from lib.fs import chown
from lib.glcli import get_project_var
from lib.migration import migrate
from lib.misc import (
    check_command,
    check_file,
    first_run_banner,
    get_colored_diff,
    get_flavour,
    is_port_free,
    run_func,
)
from lib.parser_defaults import parser_default_args, parser_default_funcs
from lib.settings import (
    C_CMD,
    C_CODE,
    C_END,
    C_FILE,
    DEKICK_DOTENV_PATH,
    DEKICK_FLAVOURS,
    DEKICKRC_FILE,
    DEKICKRC_PATH,
    PROJECT_ROOT,
    is_pytest,
)

install()
console = Console()


def arguments(parser: ArgumentParser):
    """Sets arguments for this command

    Args:
        parser (ArgumentParser): parser object that will be used to parse arguments
    """

    parser.set_defaults(func=main)

    parser.add_argument(
        "--migrate-from-version",
        required=False,
        type=str,
        help="What was the previous version of DeKick?",
    )

    parser_default_args(parser)


def main(parser: Namespace, args: list):  # pylint: disable=unused-argument
    """Main entry point for this command

    Args:
        parser (Namespace): parser object that was created by the argparse library
        args (list):
    """
    local(parser)


def local(parser: Namespace) -> int:
    """Starts a local development environment"""

    migrate_from_version = (
        "" if parser.migrate_from_version is None else parser.migrate_from_version
    )

    parser_default_funcs(parser)
    install_logger(parser.log_level, parser.log_filename)
    migrate(migrate_from_version)
    check_dekickrc()
    check_flavour()
    check_command_docker()
    check_command_docker_compose()
    check_ports()
    update_dekick()
    check_gitlabrc()
    check_project_group()
    first_run_banner()
    get_env_from_gitlab()

    return flavour_action(action="local")


def flavour_action(action: str, *args, **kwargs) -> int:
    """Runs the specified action from the current flavour"""
    flavour = get_flavour()
    return import_module(f"flavours.{flavour}.actions.{action}").main(*args, **kwargs)


def check_project_group():
    """Checks if project and group are set in .dekickrc.yml file"""
    project_group = get_dekickrc_value("project.group")
    project_name = get_dekickrc_value("project.name")
    names = []
    if project_group:
        names.append(f"group {C_CODE}{project_group}{C_END}")
    if project_name:
        names.append(f"project {C_CODE}{project_name}{C_END}")
    names_text = ", ".join(names)
    run_func(f"Setting up {names_text}")


def check_gitlabrc():
    """Checks if .gitlabrc file exists"""
    if is_pytest() or not get_dekickrc_value("gitlab.getenv"):
        return
    token_file = "/tmp/.gitlabrc"
    check_file(token_file)


def check_command_docker():
    check_command(
        cmd_linux=["docker"],
        cmd_osx=["docker"],
        hint_linux="Please install docker",
        hint_osx="Please install Docker Desktop",
        skip_if_dockerized=True,
    )


def check_command_docker_compose():
    """Checks if docker compose is installed"""
    check_command(
        cmd_linux=["docker", "compose"],
        cmd_osx=["docker", "compose"],
        hint_linux="Please install docker compose plugin using this instruction https://docs.docker.com/engine/install/",
        hint_osx="Please install Docker Desktop using this instruction https://docs.docker.com/desktop/install/mac-install/",
        arguments=2,
        skip_if_dockerized=True,
    )


def update_dekick():
    """Updates DeKick if needed"""

    if is_pytest() or not get_dekickrc_value("dekick.auto_update"):
        return

    if update() is True:
        sys.exit(255)


def check_flavour():
    """Checks if the flavour is supported"""

    def run():
        flavour = get_flavour()
        if flavour not in DEKICK_FLAVOURS:
            return {
                "success": False,
                "text": f"Flavour {C_CODE}{flavour}{C_END} is not supported",
            }
        return {"success": True, "text": f"Using flavour {C_CODE}{flavour}{C_END}"}

    run_func("Checking flavour", func=run)


def validate_dekickrc():
    """Validates .dekickrc.yml file"""
    run_func(
        text=f"Validating {C_FILE}{DEKICKRC_FILE}{C_END} file",
        func=compare_dekickrc_file,
    )


def check_dekickrc():
    """Checks if .dekickrc.yml file exists and is valid"""
    check_file(file=DEKICKRC_PATH)
    validate_dekickrc()


def install_logger(level, filename):
    """Installs logger"""
    logger.install_logger(level=level, filename=filename)
    logging.debug(locals())


def get_env_from_gitlab() -> bool:
    """Gets .env file from GitLab"""

    if is_pytest() or not get_dekickrc_value("gitlab.getenv"):
        return True

    gitlab_url = get_dekickrc_value("gitlab.url")

    def actual_get():

        if not gitlab_url:
            return {
                "success": False,
                "text": f"GitLab URL is not set in {C_FILE}{DEKICKRC_FILE}{C_END} file",
            }

        project_group = get_dekickrc_value("project.group")
        project_name = get_dekickrc_value("project.name")

        project_vars = get_project_var(
            group=project_group, project=project_name, variable="ENVFILE", scope="local"
        )

        if not os.path.isfile(DEKICK_DOTENV_PATH):
            save_dotenv(project_vars)

        diff = get_colored_diff(
            project_vars, open(f"{PROJECT_ROOT}/.env", encoding="utf-8").read()
        )

        if diff is not False and not is_pytest():
            return {
                "success": True,
                "func": ask_overwrite,
                "func_args": {"diff": diff, "project_vars": project_vars},
            }

    return run_func(
        f"Downloading {C_FILE}.env{C_END} from GitLab {C_CMD}{gitlab_url}{C_END}",
        func=actual_get,
    )


def ask_overwrite(diff: str, project_vars: str):
    """Asks if the local .env file should be overwritten"""
    console.print(f"\n{diff}")

    question = (
        "[green]Local[/green] .env and [red]remote[/red] .env file differs, overwrite?"
    )

    if Confirm.ask(question, default=False) is True:
        return run_func(
            "Overwriting local .env file",
            func=overwrite_dotenv,
            func_args={"project_vars": project_vars},
        )


def overwrite_dotenv(project_vars: str) -> dict:
    """Overwrites the local .env file with the remote one"""

    try:

        env_file = DEKICK_DOTENV_PATH
        env_bak_file = f"{env_file}.bak"

        if os.path.isfile(env_bak_file):
            os.remove(env_bak_file)

        move(
            env_file,
            env_bak_file,
        )

        save_dotenv(project_vars)

        text = f"Installed new .env file from remote, made a backup in {C_CODE}.env.bak{C_END}"

        return {
            "success": True,
            "text": text,
        }
    except Exception as err:
        return {
            "success": False,
            "text": f"Error occured during saving .env file: {err}",
        }


def save_dotenv(project_vars: str):
    """Saves the .env file"""
    with open(DEKICK_DOTENV_PATH, "w", encoding="utf-8") as file:
        file.write(project_vars)
        chown(DEKICK_DOTENV_PATH)


def check_ports():
    """Checks if ports defined in `docker-compose.yaml` are available"""

    def get_first_used_port() -> int:
        for port in get_used_ports():
            if is_port_free(port=port) is False:
                return port
        return 0

    def are_all_ports_free() -> bool:
        return bool(get_first_used_port() == 0)

    def ports_check(recheck: bool = False):

        if are_all_ports_free() is True:
            return {"success": True, "text": "All ports available"}

        first_used_port = get_first_used_port()
        text = (
            f"\nPort {C_CODE}{first_used_port}{C_END} is still in use by another process, please use {C_CMD}docker ps{C_END} to check that"
            if recheck is True
            else f"\nPort {C_CODE}{first_used_port}{C_END} is already in use by another service or process, will try to restart services"
        )
        return {
            "success": False,
            "text": text,
            "type": "warn" if recheck is False else "error",
        }

    if (
        run_func(
            "Checking if ports are available",
            func=ports_check,
            terminate=False,
        )
        is False
    ):
        stop()
        run_func(
            "Rechecking if ports are available",
            func=ports_check,
            func_args={"recheck": True},
        )


def get_used_ports() -> list:
    """Returns a list of host ports that are assigned in docker-compose.yml"""
    config = docker_compose(cmd="config", capture_output=True)["stdout"]

    published = re.findall(r'published: "(\d+)"', str(config), re.MULTILINE)
    published = [int(item) for item in published]

    logging.debug("published ports: %s", published)

    return published
