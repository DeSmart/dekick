"""
Local run for Laravel (backend) application
"""
from rich.traceback import install

from commands.seed import ui_seed
from flavours.laravel.shared import (
    api_is_ready,
    generate_apidoc,
    laravel_nova_support,
    setup_permissions,
)
from flavours.shared import composer_install, start_services

install()


def main():
    """Main"""
    laravel_nova_support()
    setup_permissions()
    composer_install()
    start_services()
    ui_seed()
    generate_apidoc()
    api_is_ready()
