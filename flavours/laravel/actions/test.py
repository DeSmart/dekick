"""
Build for Laravel (backend) application
"""
from rich.traceback import install

from commands.local import get_envs_from_credentials_provider
from commands.phpunit import phpunit
from flavours.laravel.shared import (
    db_migrate,
    fix_permissions,
    laravel_nova_support,
    setup_permissions,
)
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

    get_envs_from_credentials_provider()
    check_file(".env")
    laravel_nova_support()
    pull_and_build_images()
    setup_permissions()
    composer_install()
    copy_artifacts_from_dind()
    start_services()
    fix_permissions()
    db_migrate()
    phpunit(raise_exception=True, capture_output=False)
