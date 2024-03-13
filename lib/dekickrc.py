"""Check if .dekickrc.yml file is the same as .dekickrc.yml.tmpl file"""

import re
import sys
from ast import literal_eval

import flatdict
from rich.console import Console
from rich.traceback import install

import lib.dekickrc_validators as validators
from lib.settings import (
    C_CMD,
    C_END,
    C_FILE,
    DEKICK_PATH,
    DEKICK_VERSION_PATH,
    DEKICKRC_FILE,
    DEKICKRC_PATH,
    DEKICKRC_TMPL_FILE,
)
from lib.yaml.reader import read_yaml

install()
console = Console()


def get_dekickrc_value(name: str, check_with_template: bool = True):
    """Get value from .dekickrc.yml file"""
    dekickrc_flat = get_dekickrc_flat()

    if not check_with_template:
        if name not in dekickrc_flat:
            raise KeyError(f"Key {name} not found in {DEKICKRC_FILE}")
        return dekickrc_flat[name]

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

    return value


def get_dekickrc_flat() -> flatdict.FlatDict:
    """Gets flattened .dekickrc.yml file"""
    return read_yaml(DEKICKRC_PATH)


def get_dekickrc_tmpl_flat() -> flatdict.FlatDict:
    """Gets flattened .dekickrc.yml.tmpl file.
    Files are located in flavours directory"""
    flavour = str(get_dekickrc_value("dekick.flavour", check_with_template=False))
    tmpl_path = f"{DEKICK_PATH}/flavours/{flavour}/{DEKICKRC_TMPL_FILE}"
    return read_yaml(tmpl_path)


def get_dekick_version() -> str:
    """Gets current version of DeKick"""
    return open(DEKICK_VERSION_PATH, encoding="utf-8").read().strip()


def version_int(version: str) -> int:
    """Transforms version with format like
       x.x.x to integer with leading 1 (1.7.2 becomes 100000070002)

    Args:
        version (str): version to transform, should be in semver format (e.g. 1.7.2)

    Returns:
        int: integer representation of version (e.g. 100000070002)
    """

    if re.match(r"^\d+\.\d+\.\d+$", version) is None:
        return sys.maxsize

    versions = version.split(".")
    final_version = "1"

    for item in versions:  # type: ignore
        final_version += item.zfill(4)

    return int(final_version)


def dekickrc_tmpl_parse_value(value: str) -> dict:
    """Parses type, default, validation, required from .dekickrc.tmpl.yml"""

    tokens_pattern = r'(\w+)="([^"]*)"'
    matches = re.findall(tokens_pattern, value)

    var = {}
    for match in matches:
        token_type, token_value = match
        var[token_type] = token_value

    if set(var.keys()) != {"default", "type", "validation", "required"}:
        raise ValueError(f"Not all tokens where parsed in .dekickrc.yml.tmpl ({value})")

    required = var["required"] == "true"
    default_value = var["default"]

    if var["type"] == "str":
        default_value = str(var["default"])
    elif var["type"] == "bool":
        default_value = bool(var["default"] == "true")
    elif var["type"] == "int":
        default_value = int(var["default"])
    elif var["type"] == "list":
        try:
            default_value = "" if var["default"] == "" else literal_eval(var["default"])
        except SyntaxError as exception:
            raise ValueError(
                f"Default value for list is not valid Python syntax: {var['default']}"
            ) from exception

    return {
        "type": var["type"],
        "validation": var["validation"],
        "default": default_value,
        "required": required,
    }


def ui_validate_dekickrc():
    """Compare .dekickrc.yml file with .dekickrc.yml.tmpl file"""

    try:
        tmpl_flat = get_dekickrc_tmpl_flat()
        dekickrc_flat = get_dekickrc_flat()

        for path, tmpl_value in tmpl_flat.items():
            parsed_tmpl = dekickrc_tmpl_parse_value(str(tmpl_value))
            tmpl_type = parsed_tmpl["type"]
            tmpl_validation = parsed_tmpl["validation"]
            is_required = parsed_tmpl["required"]
            path_present = path in dekickrc_flat

            if not path_present and is_required:
                return {
                    "success": False,
                    "text": f"Key {C_CMD}{path}{C_END} ({C_CMD}{tmpl_type}{C_END}) "
                    + f"is required but does not exists in {C_FILE}{DEKICKRC_FILE}{C_END}",
                }

            value = ""
            if not path_present and not is_required:
                value = parsed_tmpl["default"]
            else:
                value = dekickrc_flat[path]

            if path_present and not __is_same_type(dekickrc_flat, tmpl_value, path):
                cur_type = __type_of(value)
                return {
                    "success": False,
                    "text": f"Key of {C_CMD}{path}{C_END} has incorrect type in "
                    + f"{C_FILE}{DEKICKRC_FILE}{C_END} (is {C_CMD}{cur_type}{C_END}, "
                    + f"should be {C_CMD}{tmpl_type}{C_END})",
                }

            # Validation
            def call_validator(validator: str, value: str, is_required: bool):
                if not is_required and value == "":
                    return True

                validator_function = getattr(
                    validators, f"validator_{validator.replace('()', '')}"
                )
                return validator_function(value)

            validate = True

            if isinstance(value, (str, bool, int)):
                validate = call_validator(tmpl_validation, str(value), is_required)

            if isinstance(value, list):
                for item in value:
                    if isinstance(item, (str, bool, int)):
                        validate = call_validator(
                            tmpl_validation, str(item), is_required
                        )
                    elif isinstance(item, dict):
                        validator_value = literal_eval(tmpl_validation)

                        for key, val in item.items():
                            if not key in validator_value:
                                return {
                                    "success": False,
                                    "text": f"Key {C_CMD}{key}{C_END} is not allowed in {C_CMD}{path}{C_END}"
                                    + f" in {C_FILE}{DEKICKRC_FILE}{C_END}",
                                }

                            validate = call_validator(
                                validator_value[key], str(val), is_required
                            )

                        for key in validator_value.keys():
                            if not key in item:
                                return {
                                    "success": False,
                                    "text": f"Key {C_CMD}{key}{C_END} is not present in {C_CMD}{path}{C_END}"
                                    + f" in {C_FILE}{DEKICKRC_FILE}{C_END}",
                                }

                    if not validate:
                        break

            if not validate:
                return {
                    "success": False,
                    "text": f"Key {C_CMD}{path}{C_END} has incorrect value in "
                    + f"{C_FILE}{DEKICKRC_FILE}{C_END} (is {C_CMD}{value}{C_END}), "
                    + f"should pass validation {C_CMD}{tmpl_validation}{C_END}",
                }

        for path, value in dekickrc_flat.items():  # pylint: disable=unused-variable
            if path not in tmpl_flat:
                return {
                    "success": False,
                    "text": f"Your {C_FILE}{DEKICKRC_FILE}{C_END} contains unnecessary extra key "
                    + f"{C_CMD}{path}{C_END} - please remove it.",
                }

    except TypeError:
        return {
            "success": False,
            "text": f"File {C_FILE}{DEKICKRC_FILE}{C_END} is not valid YAML file.",
        }


def __is_same_type(dekickrc_flat, tmpl_entry, target_path):
    """Check if type of value is the same as in .dekickrc.yml.tmpl file"""

    tmpl_type = dekickrc_tmpl_parse_value(tmpl_entry)["type"]

    if tmpl_type != __type_of(dekickrc_flat[target_path]):
        return False
    return True


def __type_of(value):
    """Get type of value"""
    return type(value).__name__
