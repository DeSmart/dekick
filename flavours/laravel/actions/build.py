"""
Build for Laravel (backend) application
"""

from rich.traceback import install

from flavours.laravel.shared import generate_apidoc, laravel_nova_support
from flavours.shared import (
    composer_install,
    copy_artifacts_from_dind,
    pull_and_build_images,
    start_services,
)
from lib.misc import check_file

install()


def main():
    """Main"""
    check_file(".env")
    laravel_nova_support()
    pull_and_build_images()
    composer_install()
    copy_artifacts_from_dind()
    start_services()
    generate_apidoc()
