import os
import sys
from argparse import ArgumentParser, Namespace
from logging import exception

from lib.environments import get_environments
from lib.logger import install_logger
from lib.parser_defaults import parser_default_args, parser_default_funcs
from lib.providers.credentials import get_envs as provider_get_envs
from lib.providers.credentials import get_info, parser_driver_arguments
from lib.run_func import run_func
from lib.settings import C_CMD, C_CODE, C_END, C_FILE, DEKICK_DOTENV_FILE, is_pytest


def parser_help() -> str:
    """Set description for this command, used in arguments parser"""
    return (
        "Get environment credentials from credentials provider "
        + f"defined in {C_FILE}.dekickrc.yml{C_END} and save it to {C_FILE}.env{C_END} file"
    )


def arguments(parser: ArgumentParser):
    """Set arguments for this command."""
    parser.add_argument(
        "--env",
        required=True,
        default="",
        help="Set specific environment to get credentials for.",
        choices=get_environments(),
    )
    parser.set_defaults(func=main)
    parser_default_args(parser)
    sub_command = os.path.splitext(os.path.basename(__file__))[0]
    parser_driver_arguments(sub_command, parser)


def main(parser: Namespace, args: list):  # pylint: disable=unused-argument
    """Main entry point for this command."""
    parser_default_funcs(parser)
    install_logger(parser.log_level, parser.log_filename)
    exit_code = ui_save_dotenv(**vars(parser))
    sys.exit(exit_code)


def ui_save_dotenv(**kwargs):
    """UI wrapper for docker_compose"""
    if is_pytest():
        return

    def wrapper(**kwargs):
        try:
            save_dotenv(**kwargs)
        except Exception as error:  # pylint: disable=broad-except
            exception(error)
            return {"success": False, "text": error.args[0]}

    env = kwargs["env"]
    driver_info = get_info()

    run_func(
        text=f"Saving credentials to {C_FILE}{DEKICK_DOTENV_FILE}{C_END} for "
        + f"environment {C_CMD}{env}{C_END} using {C_CODE}{driver_info}{C_END}",
        func=wrapper,
        func_args=kwargs,
    )
    return 0


def save_dotenv(*args, **kwargs) -> int:
    """Saves credentials to .env file."""
    envs = provider_get_envs(*args, **kwargs)

    try:
        with open(DEKICK_DOTENV_FILE, "w", encoding="utf-8") as file:
            file.write(envs)
    except PermissionError as exception:
        raise PermissionError(
            f"Credentials: Permission denied while writing to file {DEKICK_DOTENV_FILE}"
        ) from exception

    return 0
