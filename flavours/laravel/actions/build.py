"""
Build for Laravel (backend) application
"""
import logging

from rich.traceback import install

from flavours.laravel.shared import (
    generate_apidoc,
    laravel_nova_support,
    setup_permissions,
)
from flavours.shared import composer_install, pull_and_build_images, start_services
from lib.dind import dind_container
from lib.dotenv import get_dotenv_var

install()


def main():
    """Main"""

    with dind_container():
        laravel_nova_support()
        pull_and_build_images()
        setup_permissions()

        app_env = get_dotenv_var("APP_ENV")
        composer_args = []
        if app_env in ("production", "beta"):
            logging.debug(
                "APP_ENV is %s: running composer install in production mode", app_env
            )
            composer_args = ["--no-dev", "--optimize-autoloader"]

        composer_install(composer_args)
        start_services()
        generate_apidoc()
