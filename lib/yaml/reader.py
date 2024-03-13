"""Read YAML files as flatdict"""

import sys
from os import path

import flatdict
import yaml

from lib.settings import C_END, C_FILE
from lib.yaml.linter import lint


def read_yaml(file, raise_exception: bool = False) -> flatdict.FlatDict:
    """Get flattened YAML file"""
    if not path.exists(file) and raise_exception is False:
        print(f"File {C_FILE}{file}{C_END} does not exists")
        sys.exit(1)
    elif not path.exists(file) and raise_exception is True:
        raise FileNotFoundError(f"File {file} does not exists")

    lint(file)

    with open(file, "r", encoding="utf-8") as yaml_file:
        yaml_parsed = yaml.safe_load(yaml_file)
        ret = flatdict.FlatDict(yaml_parsed, delimiter=".")
        return ret
