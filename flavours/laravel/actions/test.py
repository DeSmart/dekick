"""
Build for Laravel (backend) application
"""
from rich.console import Console
from rich.traceback import install

from commands.phpunit import phpunit
from commands.seed import ui_seed
from flavours.laravel.shared import (
    db_migrate,
    fix_permissions,
    laravel_nova_support,
    setup_permissions,
)
from flavours.shared import (
    composer_install,
    pull_and_build_images,
    start_services,
    wait_for_database,
)
from lib.dind import dind_container

install()


def main():
    """Main"""

    with dind_container():
        laravel_nova_support()
        pull_and_build_images()
        setup_permissions()
        composer_install()
        start_services()
        fix_permissions()
        wait_for_database()
        db_migrate()
        phpunit(raise_exception=True, capture_output=False)
