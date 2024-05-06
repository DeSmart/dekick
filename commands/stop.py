"""
Stops DeKick
"""
import logging
import subprocess
import sys
import time
from argparse import ArgumentParser, Namespace
from sys import stdout

from rich.prompt import Confirm
from rich.traceback import install

from commands.docker_compose import docker_compose
from lib.logger import install_logger, log_exception
from lib.misc import default_env, run_shell
from lib.parser_defaults import parser_default_args, parser_default_funcs
from lib.run_func import run_func

install()


def arguments(parser: ArgumentParser):
    """Sets arguments for this command

    Args:
        parser (ArgumentParser): parser object that will be used to parse arguments
    """

    parser.set_defaults(func=main)
    parser.add_argument("--remove", action="store_true")
    parser_default_args(parser)


def main(parser: Namespace, args: list):  # pylint: disable=unused-argument
    """Main entry point for this command

    Args:
        parser (Namespace): parser object that was created by the argparse libraryz
        args (list):
    """
    parser_default_funcs(parser)

    try:
        install_logger(parser.log_level, parser.log_filename)
        stop(remove=parser.remove)
        sys.exit(0)
    except Exception as error:  # pylint: disable=broad-except
        logging.error("Message or exit code: %s", error.args[0])
        log_exception(error)
        sys.exit(1)


def stop(
    remove: bool = False,
    containers: bool = True,
    volumes: bool = True,
    networks: bool = True,
):
    """Stops all services"""
    run_func("Stopping all services", func=stop_all_services)
    if remove is True:
        if stdout.isatty() and not ask_for_confirmation():
            return
        if remove is True and containers is True:
            run_func("Removing all containers", func=remove_all_containers)
        if remove is True and volumes is True:
            run_func("Removing all volumes", func=remove_all_volumes)
        if remove is True and networks is True:
            run_func("Removing unused networks", func=remove_unused_networks)


def remove_all_volumes():  # pylint: disable=inconsistent-return-statements
    """Removes all volumes that are related to the current project"""
    cmd = ["docker", "volume", "ls", "-q"]
    out = run_shell(
        cmd=cmd, raise_exception=False, raise_error=False, capture_output=True
    )

    volumes = out["stdout"].split("\n")

    compose_project_name = default_env()["COMPOSE_PROJECT_NAME"]

    volumes_filtered = list(
        filter(lambda name: int(name.find(compose_project_name)) != -1, volumes)
    )

    # Assuming that's ok if there are no volumes to remove
    if len(volumes_filtered) == 0:
        time.sleep(1)
        return {"success": True, "text": "No volumes to remove"}

    try:
        cmd = ["docker", "volume", "rm", "-f"] + volumes_filtered
        run_shell(cmd=cmd, raise_exception=True, capture_output=True)
    except subprocess.CalledProcessError:
        return {"success": True}


def stop_all_services() -> dict:
    """Stops all services"""
    docker_compose(
        cmd="down",
        args=["--timeout", "5", "--remove-orphans"],
        raise_exception=False,
        raise_error=False,
        capture_output=True,
    )

    return {"success": True, "text": ""}


def remove_all_containers() -> dict:
    """Removes all containers"""
    cmd = "rm"
    args = ["-svf"]
    docker_compose(
        cmd=cmd,
        args=args,
        raise_exception=False,
        raise_error=False,
        capture_output=True,
    )

    return {"success": True, "text": ""}


def remove_unused_networks():
    """Removes unused networks"""
    cmd = ["docker", "network", "prune", "-f"]
    run_shell(cmd=cmd, raise_exception=False, raise_error=False, capture_output=True)

    return {"success": True, "text": ""}


def ask_for_confirmation():
    """Asks for confirmation before using a flag --remove"""
    question = (
        "Are you sure you want to remove all containers and volumes? "
        + "This could lead to data loss. (e.g. database)"
    )
    if Confirm.ask(question, default=False) is True:
        return True

    return False
