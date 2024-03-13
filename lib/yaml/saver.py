"""Flat to yaml saver"""

import flatdict
from yaml import dump


def save_flat(filename: str, flat: flatdict.FlatDict):
    """Saves flat dict to .dekickrc.yml file"""
    with open(filename, "w", encoding="utf-8") as yaml_file:
        dump(
            flat.as_dict(),
            yaml_file,
            default_flow_style=False,
            allow_unicode=True,
            indent=2,
            sort_keys=False,
            width=1000,
        )
