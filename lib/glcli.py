"""
Wrapper for GitLab library
"""
import logging
from os.path import exists

import gitlab
from rich.console import Console
from rich.traceback import install

from lib.dekickrc import get_dekickrc_value
from lib.settings import DEKICKRC_FILE, is_pytest

install()
console = Console()

GITLABRC_TOKEN_FILE = "/tmp/.gitlabrc"


def auth(token: str = "") -> gitlab.Gitlab:
    """Authenticates to Gitlab"""

    token = (
        token
        if token
        else (
            open(GITLABRC_TOKEN_FILE, encoding="utf-8")
            .read()
            .replace("token=", "")
            .strip()
        )
    )

    if not exists(GITLABRC_TOKEN_FILE):
        raise FileNotFoundError(f"Gitlab: File {GITLABRC_TOKEN_FILE} does not exist")

    logging.info("Authenticating to Gitlab with a token from %s", GITLABRC_TOKEN_FILE)
    logging.debug("Using token: %s", token.replace(token[1:-1], "**********"))

    gitlab_url = str(get_dekickrc_value("gitlab.url"))  # type: ignore
    if not gitlab_url:
        raise ValueError(f"Gitlab URL (gitlab.url) is not set in {DEKICKRC_FILE} file")

    gl_client = gitlab.Gitlab(private_token=token, url=gitlab_url)

    try:
        gl_client.auth()
    except gitlab.GitlabAuthenticationError as exception:
        raise gitlab.GitlabAuthenticationError(
            "Gitlab: Authentication failed, check your token"
        ) from exception

    return gl_client


def get_project_var(scope: str, token: str = "") -> str:
    """Gets a project variable from Gitlab"""

    if is_pytest() or not get_dekickrc_value("gitlab.getenv"):
        return ""

    gl_client = auth(token)
    variable = "ENVFILE"
    group = str(get_dekickrc_value("project.group"))
    project = str(get_dekickrc_value("project.name"))

    if not group or not project:
        raise ValueError(
            f"Gitlab: Group and/or project is not set in {DEKICKRC_FILE} file"
        )

    group_parsed = group.replace("_", "%2F").replace("/", "%2F")
    project_parsed = project.replace("_", "%2F").replace("/", "%2F")

    url = f"/projects/{group_parsed}%2F{project_parsed}/variables/{variable}?filter[environment_scope]={scope}"
    logging.debug("Gitlab: Making a http request to Gitlab (%s)", url)

    try:
        project_var = gl_client.http_get(url)
        return project_var["value"]  # type: ignore
    except gitlab.GitlabHttpError as exception:
        error = f"Gitlab: {exception.args[0][4:]}"
        http_codes = {
            "403": f"Gitlab: Access denied to project {group}/{project}. Check your permissions.",
            "404": f"Gitlab: Project {group}/{project} does not exist.",
        }
        http_code = exception.args[0][:3]

        if http_code in http_codes:
            raise gitlab.GitlabHttpError(http_codes[http_code]) from exception

        raise gitlab.GitlabHttpError(error) from exception
