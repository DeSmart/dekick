"""Runs migrations from migrations/ directory"""

from importlib import import_module
from os import listdir
from re import match

from lib.dekickrc import version_int
from lib.run_func import run_func
from lib.settings import C_CODE, C_END, DEKICK_MIGRATIONS_DIR


def migrate(migrate_from_version: str = ""):
    """Migrates the current flavour to the latest version"""

    if migrate_from_version == "":
        return

    def get_migrations():

        migration_files = listdir(DEKICK_MIGRATIONS_DIR)
        migrations = []

        for migration_file in migration_files:

            if not match(r"^\d+_\d+_\d+__\d+_\d+_\d+", migration_file):
                continue

            migration_file_parsed = migration_file.replace(".py", "")
            from_version = migration_file_parsed.split("__")[0].replace("_", ".")
            to_version = migration_file_parsed.split("__")[1].replace("_", ".")

            if version_int(from_version) < version_int(migrate_from_version):
                continue

            migrations.append(
                {
                    "from": from_version,
                    "to": to_version,
                    "module": migration_file_parsed,
                }
            )

        def split_version(version):
            return tuple(map(int, version["from"].split(".")))

        migrations.sort(key=split_version)

        return migrations

    def run_module_main(module_name: str):
        module = import_module(f"migrations.{module_name}")
        return module.main()

    for migration in get_migrations():

        from_version = migration["from"]
        to_version = migration["to"]
        module_name = migration["module"]

        run_func(
            f"Running migration from {C_CODE}{from_version}{C_END} to {C_CODE}{to_version}{C_END}",
            func=run_module_main,
            func_args={"module_name": module_name},
        )
