from argparse import ArgumentParser

from lib.glcli import get_project_var, set_project_var
from lib.settings import is_pytest


def get_actions() -> list[tuple[str, str]]:
    """Get available actions for this driver"""
    return []


def info() -> str:
    """Get info about this driver"""
    return "Gitlab"


def configure():
    """Configure this driver"""


def ui_init():
    """Initialize this driver"""
    pass


# pylint: disable=unused-argument
def get_envs(*args, env: str, gitlab_token: str = "", **kwargs) -> str:
    """Get all variables from Gitlab"""

    if is_pytest():
        return ""

    return get_project_var(scope=env, token=gitlab_token)


def set_envs(
    *args,
    env: str,
    gitlab_token: str = "",
    value: str = "",
    variable_name: str = "ENVFILE",
    **kwargs,
) -> str:
    """Put all variables to Gitlab"""

    if is_pytest():
        return ""

    return set_project_var(
        scope=env, value=value, token=gitlab_token, variable_name=variable_name
    )


def arguments(sub_command: str, parser: ArgumentParser):
    """Parse arguments for this driver"""
    parser.add_argument(
        "--gitlab-token",
        required=False,
        help="override Gitlab token",
    )
