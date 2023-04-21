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

    if not name in dekickrc_flat:
        print(
            f"Key {C_CMD}{name}{C_END} does not exists in "
            + f"{C_FILE}{DEKICKRC_GLOBAL_HOST_PATH}{C_END}")
        sys.exit(1)

    if dekickrc_flat[name] is None:
        return ""

    return dekickrc_flat[name]


def __get_dekickrc_global_flat() -> flatdict.FlatDict:
    """Gets flattened .dekickrc.yml file"""
    return read_yaml(DEKICKRC_GLOBAL_PATH)
