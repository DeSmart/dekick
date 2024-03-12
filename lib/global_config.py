"""Global DeKick settings, stored in user's home directory"""

import flatdict
from genericpath import isfile

from lib.settings import (
    C_CODE,
    C_END,
    C_FILE,
    DEKICKRC_GLOBAL_HOST_PATH,
    DEKICKRC_GLOBAL_PATH,
)
from lib.yaml.reader import read_yaml
from lib.yaml.saver import save_flat


def get_global_config_value(name: str, raise_exception: bool = True):
    """Get value from .dekickrc.yml file"""
    global_flat = __get_dekickrc_global_flat()

    try:
        if not name in global_flat:
            raise TypeError(
                f"{C_CODE}Key{C_END} {name} does not exists in "
                + f"{C_FILE}{DEKICKRC_GLOBAL_HOST_PATH}{C_END}"
            )
        value = global_flat[name]
        if value is None:
            return ""
        return value
    except TypeError as exception:
        if raise_exception:
            raise TypeError(
                f"Key {C_CODE}{name}{C_END} does not exists in "
                + f"{C_FILE}{DEKICKRC_GLOBAL_HOST_PATH}{C_END}"
            ) from exception
        else:
            return ""


def set_global_config_value(name: str, value: str):
    """Set value in global file and save the file"""
    dekickrc = __get_dekickrc_global_flat()
    dekickrc[name] = value
    __save_dekickrc_global_flat(dekickrc)


def __get_dekickrc_global_flat() -> flatdict.FlatDict:
    """Gets flattened file"""

    if not isfile(DEKICKRC_GLOBAL_PATH):
        return flatdict.FlatDict()

    return read_yaml(DEKICKRC_GLOBAL_PATH)


def __save_dekickrc_global_flat(global_flat: flatdict.FlatDict):
    """Saves flattened file"""
    if not isfile(DEKICKRC_GLOBAL_PATH):
        return
    save_flat(DEKICKRC_GLOBAL_PATH, global_flat)
