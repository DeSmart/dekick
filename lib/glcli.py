"""
API for GitLab
"""
import logging
import os

import gitlab
from rich.console import Console
from rich.traceback import install

from lib.dekickrc import get_dekickrc_value

install()
console = Console()


def auth() -> gitlab.Gitlab:
    """Authenticates to Gitlab"""

    token_file = "/tmp/.gitlabrc"
    token = open(token_file, encoding="utf-8").read().replace("token=", "").strip()

    logging.info("Authenticating to Gitlab with a token from %s", token_file)
    logging.debug("Token: %s", token)

    gitlab_url = get_dekickrc_value("gitlab.url")

    gl_client = gitlab.Gitlab(private_token=token, url=gitlab_url)

    gl_client.auth()

    return gl_client


def get_project_var(group: str, project: str, variable: str, scope: str) -> str:
    """Gets a project variable from Gitlab"""

    gl_client = auth()
    group_parsed = group.replace("_", "%2F").replace("/", "%2F")
    project_parsed = project.replace("_", "%2F").replace("/", "%2F")

    url = f"/projects/{group_parsed}%2F{project_parsed}/variables/{variable}?filter[environment_scope]={scope}"
    logging.info("Making a http request to Gitlab %s", url)
    project_var = gl_client.http_get(url)

    return project_var["value"]  # type: ignore
