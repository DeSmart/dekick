"""
Build for Laravel (backend) application
"""
from rich.console import Console
from rich.traceback import install

from commands.phpunit import phpunit
from flavours.laravel.shared import (
    db_migrate,
    laravel_nova_support,
    setup_permissions,
)
from flavours.shared import (
    composer_install,
    pull_and_build_images,
    start_services,
)

install()


def main():
    """Main"""

    laravel_nova_support()
    pull_and_build_images()
    setup_permissions()
    composer_install()
    start_services()
    db_migrate()
    phpunit(raise_exception=True, capture_output=False)
