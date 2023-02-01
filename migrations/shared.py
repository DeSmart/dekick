"""Shared functions for migrations"""
import flatdict
from yaml import dump

from lib.dekickrc import dekickrc_tmpl_parse_value, get_yaml_flat
from lib.fs import chown
from lib.settings import DEKICKRC_PATH, DEKICKRC_TMPL_PATH


def dekickrc_save_flat(dekickrc_flat: flatdict.FlatDict):
    """Saves flat dict to .dekickrc.yml file"""
    with open(DEKICKRC_PATH, "w", encoding="utf-8") as yaml_file:
        dump(dekickrc_flat.as_dict(), yaml_file)
        chown(DEKICKRC_PATH)


def dekickrc_add_default_values():
    """Adds missing fields to the .dekickrk.yml file based on .dekickrc.tmpl.yml"""

    dekickrc_flat = get_yaml_flat(DEKICKRC_PATH)
    tmpl_flat = get_yaml_flat(DEKICKRC_TMPL_PATH)

    for key, value in tmpl_flat.items():
        if key not in dekickrc_flat:
            dekickrc_flat[key] = dekickrc_tmpl_parse_value(str(value))["default"]

    dekickrc_save_flat(dekickrc_flat)


def dekickrc_remove_unused_values():
    """Removes unused fields from the .dekickrk.yml file"""

    dekickrc_flat = get_yaml_flat(DEKICKRC_PATH)
    tmpl_flat = get_yaml_flat(DEKICKRC_TMPL_PATH)

    for key in dekickrc_flat.keys():  # pylint: disable=consider-using-dict-items
        if key not in tmpl_flat:
            del dekickrc_flat[key]

    dekickrc_save_flat(dekickrc_flat)
