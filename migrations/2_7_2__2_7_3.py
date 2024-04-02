"""Migration from version 2.7.2 to 2.7.3"""

import logging
from time import sleep

from lib.settings import C_END, C_FILE
from lib.yaml.reader import read_yaml
from lib.yaml.saver import save_flat


def main():
    try:
        docker_compose = read_yaml("docker-compose.yml")
        try:
            del docker_compose["version"]
        except Exception:
            pass
        sleep(3)
        save_flat("docker-compose.yml", docker_compose)
        return {
            "success": True,
            "text": f"Migration successful, please stage and commit file {C_FILE}docker-compose.yml{C_END}",
        }
    except Exception as error:  # pylint: disable=broad-except
        logging.exception(error)
        return {"success": False, "text": "Migration failed"}
