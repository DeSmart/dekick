from argparse import ArgumentParser

from lib.glcli import get_project_var


def info() -> str:
    """Get info about this driver"""
    return "Gitlab"


def init():
    """Initialize this driver"""


# pylint: disable=unused-argument
def get_envs(*args, env: str, gitlab_token: str = "", **kwargs) -> str:
    """Get all variables from Gitlab"""
    return get_project_var(scope=env, token=gitlab_token)


def arguments(parser: ArgumentParser):
    """Parse arguments for this driver"""
    parser.add_argument(
        "--gitlab-token",
        required=False,
        help="override Gitlab token",
    )
