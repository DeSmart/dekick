"""Migration from version 2.1.1 to 2.2.0"""
import logging
from os import path

import flatdict

from lib.settings import C_END, C_FILE, DEKICKRC_GLOBAL_HOST_PATH, DEKICKRC_GLOBAL_PATH
from lib.yaml.reader import read_yaml
from lib.yaml.saver import save_flat
from migrations.shared import dekickrc_add_default_values, dekickrc_remove_unused_values


def main():
    """Migration main"""
    try:
        dekickrc_add_default_values()
        dekickrc_remove_unused_values()
        __move_gitlab_token_from_gitlabrc_to_global_yml()
        return {
            "success": True, 
            "text": "Migration successfull! Gitlab token "
                + f"moved to {C_FILE}{DEKICKRC_GLOBAL_HOST_PATH}{C_END}"
        }
    except Exception as error:  # pylint: disable=broad-except
        logging.exception(error)
        return {"success": False, "text": "Migration failed"}

def __move_gitlab_token_from_gitlabrc_to_global_yml():
    """Move gitlab token from .gitlabrc to [user]/.config/dekick/global.yml"""
    gitlab_token = __get_gitlabrc_token()
    if not gitlab_token:
        return

    global_yml = __get_global_yml()
    global_yml["gitlab"]["token"] = gitlab_token
    __save_global_yml(global_yml)

def __get_global_yml():
    """Reads global.yml to flatdict"""
    return read_yaml(DEKICKRC_GLOBAL_PATH)

def __save_global_yml(flat: flatdict.FlatDict):
    """Save flatdict to global.yml"""
    save_flat(DEKICKRC_GLOBAL_PATH, flat)

def __get_gitlabrc_token() -> str:
    """Reads gitlab token from .gitlabrc"""
    gitlabrc_file = "/tmp/homedir/.gitlabrc"
    if not path.exists(gitlabrc_file):
        return ""

    with open(gitlabrc_file, encoding="utf-8") as file:
        for line in file:
            if "token" in line:
                return line.split("=")[1].strip()
    return ""
