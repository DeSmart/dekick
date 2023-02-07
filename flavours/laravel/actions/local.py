"""
Local run for Laravel (backend) application
"""
from rich.console import Console
from rich.traceback import install

from commands.seed import ui_seed
from flavours.laravel.shared import (
    api_is_ready,
    fix_permissions,
    generate_apidoc,
    laravel_nova_support,
    setup_permissions,
)
from flavours.shared import (
    composer_install,
    pull_and_build_images,
    start_services,
    wait_for_database,
)

install()
console = Console()


def main():
    """Main"""

    laravel_nova_support()
    pull_and_build_images()
    # setup_permissions()
    composer_install()
    start_services()
    # fix_permissions()
    wait_for_database()
    ui_seed()
    generate_apidoc()
    api_is_ready()
