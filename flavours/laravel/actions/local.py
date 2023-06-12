"""
Local run for Laravel (backend) application
"""
from rich.traceback import install

from commands.seed import ui_seed
from flavours.laravel.shared import api_is_ready, generate_apidoc, laravel_nova_support
from flavours.shared import composer_install, pull_and_build_images, start_services

install()


def main():
    """Main"""
    laravel_nova_support()
    pull_and_build_images()
    composer_install()
    start_services()
    ui_seed()
    generate_apidoc()
    api_is_ready()
