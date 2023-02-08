"""
Build for Laravel (backend) application
"""
from rich.traceback import install

from commands.phpunit import phpunit
from flavours.laravel.shared import laravel_nova_support, setup_dirs
from flavours.shared import composer_install, pull_and_build_images

install()


def main():
    """Main"""

    laravel_nova_support()
    pull_and_build_images()
    setup_dirs()
    composer_install()
    phpunit(raise_exception=True, capture_output=False)
