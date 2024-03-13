"""
Runs docker-compose
"""
import sys
from argparse import ArgumentParser, Namespace
from typing import Union

from rich.console import Console
from rich.traceback import install

from commands.docker_compose import docker_compose
from flavours.shared import is_service_running

install()
console = Console()


def arguments(parser: ArgumentParser):
    """Sets arguments for this command

    Args:
        parser (ArgumentParser): parser object that will be used to parse arguments
    """
    parser.add_argument(
        "--container",
        required=False,
        default="web",
        help="Container on which the command will be executed (default: web)",
    )

    parser.add_argument(
        "--shell",
        required=False,
        default="sh",
        help="Shell which will be run in the container (default: sh)",
    )

    parser.add_argument(
        "--user",
        required=False,
        default="",
        help="Which user should run the shell (in the container)",
    )

    parser.set_defaults(func=main)


def main(parser: Namespace, args: list):  # pylint: disable=unused-argument
    """Main entry point for this command

    Args:
        parser (Namespace): parser object that was created by the argparse library
        args (list):
    """
    exit_code = shell(
        container=parser.container,
        shell_cmd=parser.shell,
        user=parser.user,
        args=args,
    )["returncode"]

    sys.exit(exit_code)


def shell(
    container: str,
    shell_cmd: str,
    args: list = [],
    env: Union[dict, None] = None,
    docker_env: dict = {},
    user: str = "",
):  # pylint: disable=too-many-arguments, dangerous-default-value
    """
    It runs a docker-compose command

    Args:
        args (list): _description_
        env (Union[dict, None], optional): This is the environment variables that will be passed
            to the command. Defaults to None.
        raise_exception (bool, optional): If True, raise an exception if the command fails,
            defaults to True.

    Returns:
        : return of the command
    """

    tmp_docker_env = []

    for key, value in docker_env.items():
        tmp_docker_env.append("-e")
        tmp_docker_env.append(f'{key}="{value}"')

    cmd = "run"
    flags = ["-it", "--rm"]

    if is_service_running(service=container):
        cmd = "exec"
        flags = ["-it"]

    if user:
        flags.append("--user")
        flags.append(user)

    return docker_compose(
        cmd=cmd,
        args=flags + tmp_docker_env + [container] + [shell_cmd] + args,
        env=env,
        raise_exception=False,
        raise_error=True,
        capture_output=False,
    )
