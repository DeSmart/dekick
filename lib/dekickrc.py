"""Check if .dekickrc.yml file is the same as .dekickrc.yml.tmpl file"""
import re
import sys
from os import path

import flatdict
import yaml
from rich.console import Console
from rich.traceback import install

from lib.settings import (
    C_CMD,
    C_END,
    C_FILE,
    DEKICK_VERSION_PATH,
    DEKICKRC_FILE,
    DEKICKRC_PATH,
    DEKICKRC_TMPL_PATH,
)

install()
console = Console()

# DEKICKRC_FLAT_CACHE = {"default": None, "flat": None}


def get_yaml_flat(file):
    """Flatten yaml file"""
    global DEKICKRC_FLAT_CACHE  # pylint: disable=global-statement, global-variable-not-assigned

    # if DEKICKRC_FLAT_CACHE[file] is not None:
    # return DEKICKRC_FLAT_CACHE[file]

    if not path.exists(file):
        print(f"File {C_FILE}{file}{C_END} does not exists")
        sys.exit(1)

    with (open(f"{file}", "r", encoding="utf-8")) as yaml_file:
        yaml_parsed = yaml.safe_load(yaml_file)
        ret = flatdict.FlatDict(yaml_parsed, delimiter=".")

        # DEKICKRC_FLAT_CACHE[file] = ret
        return ret


def is_same_type(dekickrc_flat, tmpl_entry, target_path):
    """Check if type of value is the same as in .dekickrc.yml.tmpl file"""

    tmpl_type = dekickrc_tmpl_parse_value(tmpl_entry)["type"]

    if tmpl_type != type_of(dekickrc_flat[target_path]):
        return False
    return True


def type_of(value):
    """Get type of value"""
    return type(value).__name__


def compare_dekickrc_file():
    """Compare .dekickrc.yml file with .dekickrc.yml.tmpl file"""

    try:
        tmpl_flat = get_yaml_flat(DEKICKRC_TMPL_PATH)
        dekickrc_flat = get_dekickrc_flat()

        for path, tmpl_value in tmpl_flat.items():

            parsed_tmpl_value = dekickrc_tmpl_parse_value(str(tmpl_value))
            tmpl_type = parsed_tmpl_value["type"]

            if path not in dekickrc_flat and parsed_tmpl_value["required"]:
                return {
                    "success": False,
                    "text": f"Key {C_CMD}{path}{C_END} ({C_CMD}{tmpl_type}{C_END}) "
                    + f"is required but does not exists in {C_FILE}{DEKICKRC_FILE}{C_END}",
                }

            if (
                path in dekickrc_flat
                and is_same_type(dekickrc_flat, tmpl_value, path) is False
            ):
                cur_type = type_of(dekickrc_flat[path])

                return {
                    "success": False,
                    "text": f"Key of {C_CMD}{path}{C_END} has incorrect type in "
                    + f"{C_FILE}{DEKICKRC_FILE}{C_END} (is {C_CMD}{cur_type}{C_END}, "
                    + f"should be {C_CMD}{tmpl_type}{C_END})",
                }

        for path, need_type in dekickrc_flat.items():  # pylint: disable=unused-variable
            if path not in tmpl_flat:
                return {
                    "success": False,
                    "text": f"Your {C_FILE}{DEKICKRC_FILE}{C_END} contains unneeded extra key "
                    + f"{C_CMD}{path}{C_END} - please remove it.",
                }

    except TypeError:
        return {
            "success": False,
            "text": f"File {C_FILE}{DEKICKRC_FILE}{C_END} is not valid YAML file.",
        }


def get_dekickrc_value(name: str):
    """Get value from .dekickrc.yml file"""
    dekickrc_flat = get_dekickrc_flat()
    dekickrc_tmpl_flat = get_dekickrc_tmpl_flat()

    tmpl_value = dekickrc_tmpl_parse_value(str(dekickrc_tmpl_flat[name]))
    tmpl_default = tmpl_value["default"]
    tmpl_type = tmpl_value["type"]

    if name not in dekickrc_flat and name in dekickrc_tmpl_flat:
        value = tmpl_default
    else:
        value = dekickrc_flat[name]

    if tmpl_type == "str":
        return str(value)
    if tmpl_type == "bool":
        return bool(value)
    if tmpl_type == "int":
        return int(value)

    return value


def get_dekickrc_flat() -> flatdict.FlatDict:
    return get_yaml_flat(DEKICKRC_PATH)


def get_dekickrc_tmpl_flat() -> flatdict.FlatDict:
    return get_yaml_flat(DEKICKRC_TMPL_PATH)


def get_dekick_version() -> str:
    """Gets current version of DeKick"""
    return open(DEKICK_VERSION_PATH, encoding="utf-8").read().strip()


def version_int(version: str) -> int:
    """Transforms version with format like x.x.x to integer with leading 1 (1.7.2 becomes 100000070002)

    Args:
        version (str): version to transform, should be in semver format (e.g. 1.7.2)

    Returns:
        int: integer representation of version (e.g. 100000070002)
    """

    versions = version.split(".")
    final_version = "1"

    for item in versions:
        final_version += item.zfill(4)

    return int(final_version)


def dekickrc_tmpl_parse_value(value: str) -> dict:
    """Parses default value from .dekickrc.tmpl.yml"""
    if type_of(value) == "list":
        return {"type": "list", "default": value}

    match = re.findall(r"(.*)\(default=(.*),required=(true|false)\)", value)
    var_type = match[0][0]
    default_value = match[0][1]
    required = True if match[0][2] == "true" else False

    if var_type == "str":
        default_value = str(default_value)
    elif var_type == "bool":
        default_value = bool(default_value == "true")
    elif var_type == "int":
        default_value = int(default_value)

    return {"type": var_type, "default": default_value, "required": required}
