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

from commands.local import get_envs_from_credentials_provider, install_logger
from lib.misc import get_platform, get_subsystem, run_shell
from lib.parser_defaults import parser_default_args, parser_default_funcs
from lib.run_func import run_func
from lib.settings import C_END, C_ERROR, C_FILE

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

    if get_subsystem() == "wsl":
        print(f"{C_ERROR}Error:{C_END} E2E tests doesn't work under Windows WSL2")
        sys.exit(1)

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
    get_envs_from_credentials_provider()

    platform = get_platform()
    pwd = getcwd()
    docker_cmd = ["docker", "run", "--rm", "-it"]
    cypress_image = ["desmart/cypress-included:13.6.0-1"]
    cypress_envs = [
        "-v",
        f"{pwd}/cypress:/cypress",
        "-v",
        "/tmp/.X11-unix:/tmp/.X11-unix",
        "--env-file",
        f"{pwd}/.env",
    ]
    cypress_args = ["--browser", "electron", "--project", "/e2e", "--e2e"]

    def cypress_open() -> int:
        """Open Cypress GUI"""
        cmd = ""
        cypress_cmd = ["cypress", "open"]
        cmd = docker_cmd + cypress_envs

        if platform == "linux":
            display = getenv("DISPLAY")
            print(display)
            cmd += ["-e", "DISPLAY=:0"]
        elif platform == "osx":
            host_ip = getenv("HOST_IP")
            cmd += ["-e", f"DISPLAY={host_ip}:0"]

        cmd += cypress_image + cypress_cmd + cypress_args
        return run_shell(
            cmd=cmd, capture_output=False, raise_error=False, raise_exception=False
        )["returncode"]

    def cypress_run() -> int:
        cypress_cmd = ["cypress", "run"]

        if spec is not None:
            nonlocal cypress_args
            cypress_args += ["--spec", spec]

        cmd = docker_cmd + cypress_envs + cypress_image + cypress_cmd + cypress_args
        return run_shell(
            cmd=cmd, capture_output=False, raise_error=False, raise_exception=False
        )["returncode"]

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

    if mode == "run":
        ret = cypress_run()
    else:
        ret = cypress_open()

    return ret
