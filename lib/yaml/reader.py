"""Read YAML files as flatdict"""

import sys
from os import path

import flatdict
import yaml

from lib.settings import C_END, C_FILE
from lib.yaml.linter import lint


def read_yaml(file) -> flatdict.FlatDict:
    """Get flattened YAML file"""
    if not path.exists(file):
        print(f"File {C_FILE}{file}{C_END} does not exists")
        sys.exit(1)

    lint(file)

    with open(file, "r", encoding="utf-8") as yaml_file:
        yaml_parsed = yaml.safe_load(yaml_file)
        ret = flatdict.FlatDict(yaml_parsed, delimiter=".")
        return ret
