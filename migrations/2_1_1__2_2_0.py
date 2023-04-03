"""Migration from version 2.1.1 to 2.2.0"""
import logging

from migrations.shared import dekickrc_add_default_values, dekickrc_remove_unused_values


def main():
    """Migrates .dekickrc to .dekickrc.yaml"""
    try:
        dekickrc_add_default_values()
        dekickrc_remove_unused_values()
    except Exception as error:  # pylint: disable=broad-except
        logging.exception(error)
        return {"success": False, "text": "Migration failed"}
