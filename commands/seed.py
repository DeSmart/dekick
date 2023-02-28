"""
Seeds the database with initial data
"""
import logging
import sys
from argparse import ArgumentParser, Namespace

from rich.prompt import Confirm
from rich.traceback import install

from commands.artisan import artisan
from commands.knex import knex
from flavours.shared import is_service_running, start_service
from lib.logger import install_logger, log_exception
from lib.misc import get_flavour
from lib.parser_defaults import parser_default_args, parser_default_funcs
from lib.run_func import run_func
from lib.settings import is_pytest

install()


def arguments(parser: ArgumentParser):
    """Sets arguments for this command

    Args:
        parser (ArgumentParser): parser object that will be used to parse arguments
    """
    parser.set_defaults(func=main)
    parser_default_args(parser)


def main(parser: Namespace, args: list):  # pylint: disable=unused-argument
    """Main entry point for this command

    Args:
        parser (Namespace): parser object that was created by the argparse library
        args (list):
    """
    parser_default_funcs(parser)
    install_logger(parser.log_level, parser.log_filename)
    sys.exit(0 if ui_seed() else 1)


def seed() -> bool:
    """Seed the database with initial data"""
    try:
        flavour = get_flavour()

        if flavour == "laravel":
            artisan(["migrate:fresh"], raise_exception=True, capture_output=True)
            artisan(
                ["db:seed", "--class", "DatabaseSeeder"],
                raise_exception=True,
                capture_output=True,
            )
        elif flavour == "express":
            knex(["migrate:rollback"], raise_exception=True, capture_output=True)
            knex(["migrate:latest"], raise_exception=True, capture_output=True)
            knex(["seed:run"], raise_exception=True, capture_output=True)

        return True
    except Exception as error:  # pylint: disable=broad-except
        logging.error("Message or exit code: %s", error.args[0])
        log_exception(error)
        return False


def ui_seed() -> bool:
    """It runs yarn in a container

    Args:
        args (list): _description_
        env (Union[dict, None], optional): additional env added on top of default one. Defaults to None.
        raise_exception (bool, optional): raise exception if something goes wrong. Defaults to True.
        raise_error (bool, optional): raise error if something goes wrong. Defaults to True.
        capture_output (bool, optional): capture output to return value. Defaults to False.
    """

    def run():
        if seed():
            return {"success": True, "text": "Database seeded successfully"}
        return {"success": False, "text": "Database seeding failed"}

    db_service = "db"

    if not is_service_running(db_service):
        start_service(db_service)

    question = (
        "Do you want to seed database? (it will overwrite all data in the database)"
    )

    if is_pytest() or Confirm.ask(question, default=False) is True:
        run_func(text="Seeding database", func=run)

    return True
