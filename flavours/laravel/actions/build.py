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
from flavours.shared import (
    composer_install,
    copy_artifacts_from_dind,
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
    copy_artifacts_from_dind()
    start_services()
    generate_apidoc()
