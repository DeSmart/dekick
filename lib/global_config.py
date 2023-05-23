"""Global DeKick settings, stored in user's home directory"""
import sys

import flatdict

from lib.settings import (
    C_CMD,
    C_END,
    C_FILE,
    DEKICKRC_GLOBAL_HOST_PATH,
    DEKICKRC_GLOBAL_PATH,
)
from lib.yaml.reader import read_yaml


def get_global_config_value(name: str):
    """Get value from .dekickrc.yml file"""
    dekickrc_flat = __get_dekickrc_global_flat()

    try:
        if not name in dekickrc_flat:
            raise TypeError(
                f"Key {name} does not exists in "
                + f"{C_FILE}{DEKICKRC_GLOBAL_HOST_PATH}{C_END}"
            )
        value = dekickrc_flat[name]
        if value is None:
            return ""
        return value
    except TypeError as exception:
        raise TypeError(
            f"Key {name} does not exists in "
            + f"{C_FILE}{DEKICKRC_GLOBAL_HOST_PATH}{C_END}"
        ) from exception


def __get_dekickrc_global_flat() -> flatdict.FlatDict:
    """Gets flattened .dekickrc.yml file"""
    return read_yaml(DEKICKRC_GLOBAL_PATH)
