"""Migration from version 1.8.3 to 2.0.0"""
import logging
from json import load as load_json
from os import path, remove

from yaml import dump

from lib.dotenv import get_dotenv_var
from lib.fs import chown
from lib.settings import C_END, C_FILE, DEKICK_PATH, DEKICKRC_PATH, PROJECT_ROOT
from migrations.shared import dekickrc_add_default_values, dekickrc_remove_unused_values

OLD_DEKICKRC_PATH = path.join(PROJECT_ROOT, ".dekickrc")


def main():
    """Migrates .dekickrc to .dekickrc.yaml"""
    try:
        migrate_dekickrc_to_yaml()
        dekickrc_add_default_values()
        dekickrc_remove_unused_values()
    except FileNotFoundError as error:
        logging.exception(error)

        if error.filename == OLD_DEKICKRC_PATH:
            return {
                "success": False,
                "text": f"File {C_FILE}{OLD_DEKICKRC_PATH}{C_END} "
                + "not found, maybe you already migrated?",
            }

        return {
            "success": False,
            "text": f"File {C_FILE}{error.filename}{C_END} not found",
        }

    except Exception as error:  # pylint: disable=broad-except
        logging.exception(error)
        return {"success": False, "text": "Migration failed"}


def migrate_dekickrc_to_yaml():
    """Migrates .dekickrc to .dekickrc.yaml"""

    if convert_dekickrc_to_yaml() is True:
        remove_old_dekickrc()
        return True

    return False


def convert_dekickrc_to_yaml():
    """Convert .dekickrc to .dekickrc.yaml"""
    logging.debug("Opening %s file", OLD_DEKICKRC_PATH)
    with open(OLD_DEKICKRC_PATH, "r", encoding="utf-8") as file:
        configuration = load_json(file)

    configuration["dekick"]["flavour"] = map_flavour(configuration["dekick"]["flavour"])
    configuration["project"] = {
        "group": configuration["gitlab"]["group"],
        "name": configuration["gitlab"]["project"],
    }

    gitlab_url = get_dotenv_var(
        "GITLAB_URL", path=DEKICK_PATH, default="https://git.desmart.com/"
    )

    if gitlab_url != "":
        configuration["gitlab"]["url"] = gitlab_url
        configuration["gitlab"]["getenv"] = True

    logging.debug("Writing to %s file", DEKICKRC_PATH)
    with open(DEKICKRC_PATH, "w", encoding="utf-8") as yaml_file:
        logging.debug(configuration)
        dump(configuration, yaml_file)
        chown(DEKICKRC_PATH)

    if path.exists(DEKICKRC_PATH) is True:
        return True

    return False


def remove_old_dekickrc() -> bool:
    """Remove .dekickrc file"""
    if path.exists(OLD_DEKICKRC_PATH) is True:

        logging.debug("Removing %s file", OLD_DEKICKRC_PATH)
        remove(OLD_DEKICKRC_PATH)

        if path.exists(OLD_DEKICKRC_PATH) is False:
            return True

    return False


def map_flavour(old_value: str) -> str:
    """Map old flavours to new flavours"""
    fl_map = {
        "node": "express",
        "php": "laravel",
        "react": "react",
        "vue": "vue",
    }
    return fl_map[old_value]
