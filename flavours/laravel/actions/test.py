"""
Build for Laravel (backend) application
"""
from rich.traceback import install

from commands.local import get_envs_from_credentials_provider
from commands.phpunit import phpunit
from flavours.laravel.shared import db_migrate, laravel_nova_support, setup_permissions
from flavours.shared import composer_install, copy_artifacts_from_dind
from lib.misc import check_file

install()


def main(args: list):
    """Main"""

    get_envs_from_credentials_provider()
    check_file(".env")
    laravel_nova_support()
    setup_permissions()
    composer_install()
    copy_artifacts_from_dind()
    db_migrate()
    phpunit(raise_exception=True, capture_output=False, args=args)
