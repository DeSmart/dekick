"""
Runs phpunit
"""
import json
import re
import sys
from argparse import ArgumentParser, Namespace
from typing import Union

from rich.traceback import install

from commands.docker_compose import docker_compose
from lib.logger import install_logger
from lib.misc import get_flavour_container
from lib.parser_defaults import parser_default_args, parser_default_funcs
from lib.run_func import run_func
from lib.settings import C_CMD, C_END, CURRENT_UID

install()

# Cache for PHPUnit version to avoid running --version multiple times
_phpunit_version_cache = None

def get_phpunit_version():
    """Get PHPUnit version by running phpunit --version

    Returns:
        float: PHPUnit major.minor version (e.g., 11.0, 10.5)
    """
    global _phpunit_version_cache

    # Return cached version if already determined
    if _phpunit_version_cache is not None:
        return _phpunit_version_cache

    try:
        container = get_flavour_container()

        # Run phpunit --version in the container with minimal output
        result = docker_compose(
            cmd="run",
            args=[
                "--rm",
                "--user",
                CURRENT_UID,
                container,
                "vendor/bin/phpunit",
                "--version"
            ],
            capture_output=True,
            raise_exception=False
        )

        if result["returncode"] == 0 and result["stdout"]:
            # Parse version output like "PHPUnit 11.5.7 by Sebastian Bergmann and contributors."
            version_output = result["stdout"].strip()
            version_match = re.search(r'PHPUnit (\d+\.\d+)', version_output)
            if version_match:
                version_str = version_match.group(1)
                _phpunit_version_cache = float(version_str)
                return _phpunit_version_cache

        # Fallback to composer.json if direct version check fails
        _phpunit_version_cache = get_phpunit_version_from_composer()
        return _phpunit_version_cache
    except Exception:
        # Final fallback to composer.json
        _phpunit_version_cache = get_phpunit_version_from_composer()
        return _phpunit_version_cache


def get_phpunit_version_from_composer():
    """Get PHPUnit version from composer.json as fallback

    Returns:
        float: PHPUnit major.minor version (e.g., 11.0, 10.5)
    """
    try:
        with open('composer.json', 'r') as f:
            composer_data = json.load(f)

        phpunit_constraint = composer_data.get('require-dev', {}).get('phpunit/phpunit', '')

        # Extract version from constraint like "^11.0", "~10.5.3", etc.
        version_match = re.search(r'[\^~]?\s*(\d+\.\d+)', phpunit_constraint)
        if version_match:
            version_str = version_match.group(1)
            return float(version_str)

        # Default to a high version if we can't determine
        return 11.0
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        # Default to a high version if we can't determine
        return 11.0


def get_cache_option():
    """Get appropriate cache option based on PHPUnit version

    Returns:
        str: Cache option string for PHPUnit command
    """
    phpunit_version = get_phpunit_version()

    if phpunit_version >= 10.0:
        return "--cache-directory=/tmp/.phpunit.cache"
    else:
        return "--cache-result-file=/tmp/.phpunit.result.cache"


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
    exit_code = 0

    if parser.log_filename:
        install_logger(parser.log_level, parser.log_filename)
        exit_code = ui_phpunit(args=args)
    else:
        exit_code = phpunit(args=args, raise_exception=False, capture_output=False)[
            "returncode"
        ]

    sys.exit(exit_code)


def ui_phpunit(**kwargs):
    """UI wrapper for phpunit"""

    def wrapper(**kwargs):
        phpunit(raise_exception=True, **kwargs)

    args = kwargs["args"][0] if "args" in kwargs else ""

    return run_func(
        text=f"Running phpunit {C_CMD}{args}{C_END}", func=wrapper, func_args=kwargs
    )


def phpunit(
    args: list = [],
    env: Union[dict, None] = None,
    raise_exception: bool = True,
    raise_error: bool = True,
    capture_output: bool = True,
):  # pylint: disable=dangerous-default-value
    """It runs phpunit in a container

    Args:
        args (list): _description_
        env (Union[dict, None], optional): additional env added on top of default one. Defaults to None.
        raise_exception (bool, optional): raise exception if something goes wrong. Defaults to True.
        raise_error (bool, optional): raise error if something goes wrong. Defaults to True.
        capture_output (bool, optional): capture output to return value. Defaults to False.
    """

    container = get_flavour_container()

    cmd = "run"
    args = [
        "--rm",
        "--user",
        CURRENT_UID,
        container,
        "vendor/bin/phpunit",
        get_cache_option(),
    ] + args

    ret = docker_compose(
        cmd=cmd,
        args=args,
        env=env,
        raise_exception=raise_exception,
        raise_error=raise_error,
        capture_output=capture_output,
    )

    return ret
