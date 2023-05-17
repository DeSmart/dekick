from argparse import ArgumentParser

import hvac
from hvac import exceptions as hvac_exceptions

from lib.dekickrc import get_dekickrc_value
from lib.dotenv import dict2env

VAULT_TOKEN = "hvs.CAESIIshlmka4E28Et7-SkFcViwiY6pZLUpKlUHE44LyuDSaGh4KHGh2cy5oU0Y5ZGhKWlpzamFZeENEbmoyeHJONnk"
VAULT_ADDR = str(get_dekickrc_value("hashicorp_vault.url"))
HVAC_CLIENT = None


def info() -> str:
    """Get info about this driver"""
    return "Hashicorp Vault"


def init():
    """Initialize this driver"""


def create_envs():
    """Creates new secrets inside Hashicorp Vault using mount_point and path from .dekickrc.yml"""


def push_envs():
    """Pushes secrets to Hashicorp Vault using mount_point and path from .dekickrc.yml"""


# pylint: disable=unused-argument
def get_envs(*args, env: str, vault_token: str = "", **kwargs) -> str:
    """Get all variables from Gitlab"""
    hvac_path = str(get_dekickrc_value("hashicorp_vault.path")).rstrip("/")
    hvac_mount_point = str(get_dekickrc_value("hashicorp_vault.mount_point"))

    if hvac_path:
        hvac_path = hvac_path + "/"

    path = f"{hvac_path}{env}/.env"
    client = _hvac_create_client(vault_token)

    try:
        secret = client.secrets.kv.v2.read_secret_version(
            path=path, mount_point=hvac_mount_point
        )
        return dict2env(secret["data"]["data"])

    except hvac_exceptions.InvalidPath as exception:
        raise ValueError(
            f"Path {hvac_mount_point}/{path} not found, check your mount_point and path "
        ) from exception

    except hvac_exceptions.Forbidden as exception:
        raise KeyError(
            f"You don't have access to path {hvac_mount_point}/{path}. Do you have proper token?"
        ) from exception


def arguments(parser: ArgumentParser):
    """Parse arguments for this driver"""
    parser.add_argument(
        "--vault-token",
        required=False,
        help=f"override {info()} token",
    )


def _hvac_create_client(vault_token: str = "") -> hvac.Client:
    global HVAC_CLIENT  # pylint: disable=global-statement

    if not HVAC_CLIENT:
        HVAC_CLIENT = hvac.Client(
            url=VAULT_ADDR, token=vault_token or VAULT_TOKEN)

    return HVAC_CLIENT
