from argparse import ArgumentParser
from os.path import exists

from lib.dekickrc import get_dekickrc_value
from lib.glcli import get_project_var
from lib.settings import C_END, C_FILE, DEKICKRC_FILE, is_pytest

GITLABRC_TOKEN_FILE = "/tmp/.gitlabrc"
GITLAB_URL = get_dekickrc_value("gitlab.url")


def info() -> str:
    return f"GitLab {C_FILE}{GITLAB_URL}{C_END}"


def init():
    """Initialize this driver"""
    if not GITLAB_URL:
        raise ValueError(
            f"GitLab URL is not set in {C_FILE}{DEKICKRC_FILE}{C_END} file"
        )

    check_gitlabrc()


def check_gitlabrc():
    """Checks if .gitlabrc file exists"""
    if is_pytest() or not get_dekickrc_value("gitlab.getenv"):
        return

    if not exists(GITLABRC_TOKEN_FILE):
        raise FileNotFoundError(
            f"File {C_FILE}{GITLABRC_TOKEN_FILE}{C_END} does not exist"
        )


def get_envs(env: str) -> str:
    """Get all variables from Gitlab"""

    project_group = str(get_dekickrc_value("project.group"))
    project_name = str(get_dekickrc_value("project.name"))

    return get_project_var(
        group=project_group, project=project_name, variable="ENVFILE", scope=env
    )


def update_envs(env: str, vars: dict) -> None:
    """Updates all project variables in Gitlab"""
    return


def arguments(parser: ArgumentParser):
    """Parse arguments for this driver"""
    parser.add_argument(
        "--gitlab-token",
        required=False,
        help="override Gitlab token",
    )
