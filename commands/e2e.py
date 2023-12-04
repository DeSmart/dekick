"""
Runs the specified command
"""
import ipaddress
import logging
import re
import sys
from argparse import ArgumentParser, Namespace
from os import getcwd, getenv
from os.path import isfile

from rich.traceback import install

from commands.local import install_logger
from lib.misc import get_platform
from lib.parser_defaults import parser_default_args, parser_default_funcs
from lib.rbash import rbash
from lib.run_func import run_func
from lib.settings import C_CMD, C_END, C_FILE

install()


def arguments(parser: ArgumentParser):
    """Sets arguments for this command

    Args:
        parser (ArgumentParser): parser object that will be used to parse arguments
    """
    parser.set_defaults(func=main)

    parser.add_argument(
        "--mode",
        choices=["run", "open"],
        required=False,
        default="run",
        type=str,
        help="Runs the tests (run) or opens (open) the Cypress GUI",
    )

    parser.add_argument(
        "--spec",
        required=False,
        type=str,
        help="Spec file to be run",
    )

    parser_default_args(parser)


def main(parser: Namespace, args: list):  # pylint: disable=unused-argument
    """Main entry point for this command

    Args:
        parser (Namespace): parser object that was created by the argparse library
        args (list):
    """
    parser_default_funcs(parser)

    sys.exit(
        e2e(
            log_level=parser.log_level or "INFO",
            log_filename=parser.log_filename or "dekick-e2e.log",
            mode=parser.mode,
            spec=parser.spec,
            args=args,
        )
    )


# pylint: disable=too-many-arguments
def e2e(log_level: str, log_filename: str, mode: str, spec: str, args: list) -> int:
    """
    Run unit test for specific flavour
    """
    install_logger(log_level, log_filename)

    platform = get_platform()
    pwd = getcwd()
    docker_cmd = "docker run"
    cypress_image = "desmart/cypress-included:13.6.0-1"
    cypress_envs = f"-v {pwd}/cypress:/cypress -v /tmp/.X11-unix:/tmp/.X11-unix --env-file {pwd}/.env"
    cypress_args = "--browser electron --project /e2e --e2e"

    def cypress_open():
        """Open Cypress GUI"""
        cmd = ""
        cypress_cmd = "cypress open"

        if platform == "linux":
            cmd += f"{docker_cmd} {cypress_envs} -e DISPLAY "
            cmd += f"{cypress_image} {cypress_cmd} {args}"
        elif platform == "osx":
            host_ip = getenv("HOST_IP")
            cmd += f"{docker_cmd} {cypress_envs} -e DISPLAY={host_ip}:0 "
            cmd += f"{cypress_image} {cypress_cmd} {args}"

        rbash(
            info_desc="Opening Cypress GUI",
            cmd=cmd,
        )
        return {"success": True}

    def cypress_run():
        cmd = ""
        cypress_cmd = "cypress run"

        if spec is not None:
            nonlocal cypress_args
            cypress_args += f" --spec {spec}"

        if platform == "linux":
            cmd += f"{docker_cmd} {cypress_envs} {cypress_image} {cypress_cmd} {cypress_args}"

        out = rbash(
            info_desc="Running e2e tests",
            cmd=cmd,
        )

        return {"success": True, "text": out["stdout"]}

    def check_cypress_config_template():
        if not isfile("cypress/cypress.config.template.js"):
            return {
                "success": False,
                "text": f"Missing {C_FILE}cypress.config.template.js{C_END}",
            }

        return {"success": True}

    ret = run_func(
        text="Checking Cypress config template",
        func=check_cypress_config_template,
        terminate=False,
    )
    if ret is False:
        return 1

    text = "Running e2e tests"

    if spec is not None:
        text += f" for {C_CMD}{spec}{C_END}"

    ret = run_func(
        text=text if mode == "run" else "Opening Cypress GUI",
        func=cypress_run if mode == "run" else cypress_open,
        terminate=False,
    )

    if ret is False:
        return 1

    return 0
