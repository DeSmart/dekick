"""
Runs docker-compose
"""

import logging
import sys
from argparse import ArgumentParser, Namespace
from subprocess import CalledProcessError
from time import sleep
from typing import Union

from rich.console import Console
from rich.traceback import install

from lib.logger import get_log_level, install_logger
from lib.misc import run_shell
from lib.parser_defaults import parser_default_args, parser_default_funcs
from lib.run_func import run_func
from lib.settings import C_CMD, C_CODE, C_END, C_ERROR, get_seconds_since_dekick_start

install()
console = Console()


def arguments(parser: ArgumentParser):
    """Sets arguments for this command

    Args:
        parser (ArgumentParser): parser object that will be used to parse arguments
    """

    parser.set_defaults(func=main)
    parser_default_args(parser)


def main(parser: Namespace, args: list):  # pylint: disable=unused-argument
    """Main entry point for this command

    Args:
        parser (Namespace): parser object that was created by the argparse library
        args (list):
    """
    parser_default_funcs(parser)

    cmd = args[0]
    additional_args = args[1:]
    exit_code = 0

    if parser.log_filename:
        install_logger(parser.log_level, parser.log_filename)
        exit_code = ui_docker_compose(cmd=cmd, args=additional_args)
    else:
        exit_code = docker_compose(
            cmd, additional_args, raise_exception=False, capture_output=False
        )["returncode"]

    sys.exit(exit_code)


def ui_docker_compose(**kwargs):
    """UI wrapper for docker_compose"""

    def wrapper(**kwargs):
        docker_compose(raise_exception=True, **kwargs)

    cmd = kwargs["cmd"]

    text = (
        f"Running docker-compose {C_CMD}{cmd}{C_END}"
        if not kwargs["text"]
        else kwargs["text"]
    )

    del kwargs["text"]

    return run_func(text=text, func=wrapper, func_args=kwargs)


def docker_compose(
    cmd: str,
    args: list = [],
    env: Union[dict, None] = None,
    docker_env: dict = {},
    raise_exception: bool = True,
    raise_error: bool = True,
    capture_output: bool = True,
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

    shell_cmd = ["docker", "compose", cmd] + tmp_docker_env + args

    if get_log_level() == "DEBUG":
        logging.debug(locals())
    else:
        logging.info("Running docker-compose(%s)", [cmd] + args)

    # Catching docker compose `network not found` error
    try:
        ret = run_shell(
            cmd=shell_cmd,
            env=env,
            raise_exception=raise_exception,
            raise_error=raise_error,
            capture_output=capture_output,
        )
        return ret
    except CalledProcessError as error:  # pylint: disable=broad-except
        if "network" in str(error.stdout) and "not found" in str(error.stdout):
            # Go down with services if network not found, should fix
            # the issue with `network not found` docker-compose error
            logging.warning(
                "Catched `network not found` error, going down with services and retrying"
            )
            run_shell(
                cmd=[
                    "docker",
                    "compose",
                    "down",
                ],
                env=env,
                raise_exception=False,
                raise_error=False,
                capture_output=True,
            )
            # Retry docker-compose command
            return docker_compose(
                cmd=cmd,
                args=args,
                env=env,
                docker_env=docker_env,
                raise_exception=raise_exception,
                raise_error=raise_error,
                capture_output=capture_output,
            )

        raise CalledProcessError(
            returncode=error.returncode,
            cmd=error.cmd,
            output=error.output,
            stderr=error.stderr,
        ) from error


def wait_for_log(
    container_name: str,
    search_string: Union[str, list],
    failed_string: str,
    timeout: int = 60,
):
    """Reads container logs every second and returns True if the log contains
    search_string within specified timeout time

    Args:
        container (): Container name
        search_string (Union[str, list]): String or list of strings to search for in the container logs
        timeout (int, optional): Timeout. Defaults to 60.

    Returns:
        bool: True if the log contains search_string within specified timeout time, False otherwise
    """

    timer = 0

    # If search_string is a string, make it a list
    if isinstance(search_string, str):
        search_string = [search_string]

    while timer < timeout:
        log = get_container_log(container_name, get_seconds_since_dekick_start())
        if failed_string and failed_string in log:
            raise Exception()
        if any(string in log for string in search_string):
            if failed_string and failed_string in log:
                raise Exception()
            elif not failed_string or failed_string not in log:
                return
        (exit_code, status) = get_container_exit_code(container_name)

        if status == "exited" and exit_code != 0:
            raise RuntimeError(
                f"Container {C_CMD}{container_name}{C_END} exited with code "
                + f"{C_ERROR}{exit_code}{C_END}. "
                + f"Log:\n\n{C_ERROR}{log}{C_END}"
            )

        sleep(1)
        timer = timer + 1

    raise TimeoutError(
        f"Timeout when waiting for {C_CODE}{search_string}{C_END} in a container "
        + f"{C_CMD}{container_name}{C_END} after {timeout} seconds"
    )


def get_container_exit_code(container_name: str) -> tuple:
    """Gets container exit code and status"""
    container_id = get_container_id_by_name(container_name)
    inspect = (
        run_shell(
            cmd=[
                "docker",
                "inspect",
                container_id,
                "--format",
                "{{ .State.ExitCode }}:{{ .State.Status }}",
            ],
            capture_output=True,
            raise_exception=False,
            raise_error=False,
        )["stdout"]
        .strip()
        .split(":")
    )

    return (int(inspect[0]), inspect[1])


def get_container_log(
    container_name: str, since: float = 0, capture_output: bool = True
) -> str:
    """Gets container log since seconds ago, if since is 0, it will return the whole log"""

    since_formatted = f"{since}s"

    args_since = ["--since", since_formatted] if since > 0 else []

    return docker_compose(
        cmd="logs",
        args=[
            *args_since,
            "--no-log-prefix",
            "--no-color",
            container_name,
        ],
        capture_output=capture_output,
    )["stdout"]


def get_container_id_by_name(container_name: str) -> str:
    """Gets container id by name"""
    return docker_compose(cmd="ps", args=["-q", container_name], capture_output=True)[
        "stdout"
    ].strip()
