"""
Wrapper for GitLab library
"""

import logging

import gitlab
from rich.console import Console
from rich.traceback import install

from lib.dekickrc import get_dekickrc_value
from lib.global_config import get_global_config_value
from lib.settings import DEKICKRC_FILE, DEKICKRC_GLOBAL_HOST_PATH, is_pytest

install()
console = Console()


def auth(token: str = "") -> gitlab.Gitlab:
    """Authenticates to Gitlab"""
    token = __get_token(token)
    gitlab_url = str(get_dekickrc_value("gitlab.url"))  # type: ignore

    if not gitlab_url:
        raise ValueError(f"URL (gitlab.url) is not set in {DEKICKRC_FILE} file")

    logging.info("Authenticating to Gitlab with a token")
    logging.debug("Using token: %s", token.replace(token[1:-1], "**********"))

    gitlab_url = __get_gitlab_url()
    gl_client = gitlab.Gitlab(private_token=token, url=gitlab_url)

    try:
        gl_client.auth()
    except gitlab.GitlabAuthenticationError as exception:
        raise gitlab.GitlabAuthenticationError(
            "Gitlab: Authentication failed, check your token "
            + f"in {DEKICKRC_GLOBAL_HOST_PATH} or token argument"
        ) from exception

    return gl_client


def get_project_var(scope: str, token: str = "", variable_name="ENVFILE") -> str:
    """Gets a project variable from Gitlab"""
    gl_client = auth(token)
    group = str(get_dekickrc_value("project.group"))
    project = str(get_dekickrc_value("project.name"))

    if not group or not project:
        raise ValueError(f"Group and/or project is not set in {DEKICKRC_FILE} file")

    group_parsed = group.replace("_", "%2F").replace("/", "%2F")
    project_parsed = project.replace("_", "%2F").replace("/", "%2F")

    url = f"/projects/{group_parsed}%2F{project_parsed}/variables/{variable_name}?filter[environment_scope]={scope}"
    logging.debug("Gitlab: Making a http request to Gitlab (%s)", url)

    try:
        project_var = gl_client.http_get(url)
        return project_var["value"]  # type: ignore
    except gitlab.GitlabHttpError as exception:
        error = f"Gitlab: {exception.args[0][4:]}"
        http_codes = {
            "403": f"Access denied to project {group}/{project}. Check your permissions.",
            "404": f"Project {group}/{project} does not exist.",
        }
        http_code = exception.args[0][:3]

        if http_code in http_codes:
            raise gitlab.GitlabHttpError(http_codes[http_code]) from exception

        raise gitlab.GitlabHttpError(error) from exception


def set_project_var(
    scope: str,
    value: str,
    token: str = "",
    variable_name: str = "ENVFILE",
    raw: bool = False,
    update: bool = False,
    expand: bool = False,
    masked: bool = False,
) -> str:
    """Sets a project variable in Gitlab"""
    gl_client = auth(token)
    group = str(get_dekickrc_value("project.group"))
    project = str(get_dekickrc_value("project.name"))

    if not group or not project:
        raise ValueError(f"Group and/or project is not set in {DEKICKRC_FILE} file")

    group_parsed = group.replace("_", "%2F").replace("/", "%2F")
    project_parsed = project.replace("_", "%2F").replace("/", "%2F")

    url = f"/projects/{group_parsed}%2F{project_parsed}/variables"
    logging.debug("Gitlab: Making a http request to Gitlab (%s)", url)

    try:
        data = {
            "key": variable_name,
            "value": value,
            "environment_scope": scope,
            "raw": raw,
            "masked": masked,
            "expand": expand,
        }

        if update:
            url += f"/{variable_name}"
            gl_client.http_put(url, post_data=data)
        else:
            gl_client.http_post(url, post_data=data)
    except gitlab.GitlabHttpError as exception:

        if (
            exception.args[0]
            and "key" in exception.args[0]
            and "has already been taken" in str(exception.args[0]["key"])
        ):
            return set_project_var(scope, value, token, variable_name, update=True)

        error = f"Gitlab: {exception.args[0][4:]}"
        http_codes = {
            "403": f"Access denied to project {group}/{project}. Check your permissions.",
            "404": f"Project {group}/{project} does not exist.",
        }
        http_code = exception.args[0][:3]

        if http_code in http_codes:
            raise gitlab.GitlabHttpError(http_codes[http_code]) from exception

        raise gitlab.GitlabHttpError(error) from exception

    return value


def __get_token(token: str) -> str:
    """Gets a token from global config or from token argument"""
    if not token:
        token = str(get_global_config_value("gitlab.token"))
    if not token:
        raise ValueError(
            f"Gitlab: Token is empty, set it in {DEKICKRC_GLOBAL_HOST_PATH} file"
        )
    return token


def __get_gitlab_url() -> str:
    gitlab_url = str(get_dekickrc_value("gitlab.url"))  # type: ignore
    if not gitlab_url:
        raise ValueError(f"Gitlab: URL (gitlab.url) is not set in {DEKICKRC_FILE} file")
    return gitlab_url
