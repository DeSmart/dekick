"""Miscellaneous functinos running tests"""
from logging import debug
from os import remove
from shutil import copy
from tempfile import mktemp

from dotenv import set_key
from rich.traceback import install

from lib.rbash import rbash
from lib.tests.boilerplates import get_boilerplates_path
from lib.tests.dind import get_dind_container_id, rbash_dind
from lib.tests.docker import get_docker_env
from lib.tests.misc import get_dekick_runner

install()


def _dekick_command_wrapper(args: list, flavour: str, version: str) -> dict:
    """Runs DeKick command with given arguments, flavour and version of the boilerplate used"""
    args_parsed = " ".join(args)
    env = get_docker_env()
    project_root = env["PROJECT_ROOT"]
    debug("env: %s", env)
    dekick_runner = get_dekick_runner()

    return rbash_dind(
        info_desc=f"Running 'dekick {args_parsed}' for flavour {flavour}, version {version}",
        cmd=f'cd "{project_root}" && {dekick_runner} {args_parsed} '
        + "--pytest --log-level DEBUG --log-filename=stdout",
        env=env,
    )


def dekick_local(flavour: str, version: str) -> bool:
    """Runs dekick local command with given flavour and version of the boilerplate used"""
    proc = _dekick_command_wrapper(["local"], flavour, version)
    return proc["code"] == 0


def dekick_status(flavour: str, version: str) -> bool:
    """Runs dekick status command with given flavour and version of the boilerplate used"""
    proc = _dekick_command_wrapper(["status"], flavour, version)
    return proc["code"] == 0


def dekick_stop(flavour: str, version: str, args=None) -> bool:
    """Runs dekick stop command with given flavour and version of the boilerplate used"""
    args = args or []
    proc = _dekick_command_wrapper(["stop", *args], flavour, version)
    return proc["code"] == 0


def dekick_build(flavour: str, version: str) -> bool:
    """Runs dekick build command with given flavour and version of the boilerplate used"""
    proc = _dekick_command_wrapper(
        ["build", f"--target-image={flavour}-{version}"], flavour, version
    )
    return proc["code"] == 0


def dekick_test(flavour: str, version: str, args=None) -> bool:
    """Runs dekick test command with given flavour and version of the boilerplate used"""
    args = args or []
    proc = _dekick_command_wrapper(["test"] + args, flavour, version)
    return proc["code"] == 0


def dekick_dotenv_replace(flavour: str, version: str, env: dict) -> bool:
    """
    Replaces .env file contents with given environment variables as env
    """
    try:
        docker_env = get_docker_env()
        project_root = docker_env["PROJECT_ROOT"]
        source_env_file = f"{get_boilerplates_path()}/{flavour}/{version}/.env"
        # copy source_env_file to temporary file
        tmp_env_file = mktemp()
        copy(source_env_file, tmp_env_file)

        container_id = get_dind_container_id()

        for key, value in env.items():
            set_key(tmp_env_file, key, value, quote_mode="auto")

        destination_env_file = f"{project_root}/.env"
        rbash(
            f"Copying {tmp_env_file} .env file to DinD container",
            f"docker cp -aq {tmp_env_file} {container_id}:{destination_env_file}",
        )
        rbash(
            "Setting permissions for .env file",
            f"docker exec {container_id} chmod 666 {destination_env_file}",
        )

        remove(tmp_env_file)

    except Exception:  # pylint: disable=broad-except
        return False

    return True
