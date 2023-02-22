"""
Build for Laravel (backend) application
"""
from rich.traceback import install

from commands.phpunit import phpunit
from flavours.laravel.shared import (
    db_migrate,
    fix_permissions,
    laravel_nova_support,
    setup_permissions,
)
from flavours.shared import composer_install, pull_and_build_images, start_services

install()


def main():
    """Main"""

    laravel_nova_support()
    pull_and_build_images()
    setup_permissions()
    composer_install()
    start_services()
    fix_permissions(recursive_chown=True)
    db_migrate()
    phpunit(raise_exception=True, capture_output=False)
