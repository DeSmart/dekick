"""Miscellaneous functinos running tests"""
from logging import debug

from dotenv import set_key
from rich.traceback import install

from lib.tests.dind import rbash_dind
from lib.tests.docker import docker_no_running_container, get_docker_env
from lib.tests.misc import get_dekick_runner
from lib.tests.rbash import rbash

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


def dekick_stop(flavour: str, version: str) -> bool:
    """Runs dekick stop command with given flavour and version of the boilerplate used"""
    proc = _dekick_command_wrapper(["stop", "--remove"], flavour, version)
    return proc["code"] == 0 and docker_no_running_container()


def dekick_build(flavour: str, version: str) -> bool:
    """Runs dekick build command with given flavour and version of the boilerplate used"""
    proc = _dekick_command_wrapper(
        ["build", f"--target-image={flavour}-{version}"], flavour, version
    )
    return proc["code"] == 0


def dekick_test(flavour: str, version: str) -> bool:
    """Runs dekick test command with given flavour and version of the boilerplate used"""
    proc = _dekick_command_wrapper(["test"], flavour, version)
    return proc["code"] == 0


def dekick_dotenv_replace(flavour: str, version: str, env: dict) -> bool:
    """
    Replaces .env file contents with given environment variables as env
    """
    try:
        docker_env = get_docker_env()
        project_root = docker_env["PROJECT_ROOT"]
        env_file = f"{project_root}/.env"

        for key, value in env.items():
            set_key(env_file, key, value, quote_mode="auto")

        rbash(
            "Change owner of .env file", f"chown {docker_env['CURRENT_UID']} {env_file}"
        )

    except Exception:  # pylint: disable=broad-except
        return False

    return True
