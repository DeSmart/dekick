from importlib import import_module

from lib.dekickrc import get_dekickrc_value

INIT = False


def driver_init():
    """Initialize driver"""
    global INIT  # pylint: disable=global-statement
    if INIT is True:
        return
    module = _get_driver_module()
    module.init()
    INIT = True


def get_info() -> str:
    _init()
    module = _get_driver_module()
    return module.info()


def get_envs(env: str) -> str:
    _init()
    module = _get_driver_module()
    return module.get_envs(env)


def update_envs(env: str, vars: dict):
    _init()
    module = _get_driver_module()
    module.update_envs(env, vars)


def parser_driver_arguments(parser):
    _init()
    module = _get_driver_module()
    return module.arguments(parser)


def _init():
    if INIT:
        return
    driver_init()


def _get_driver_module():
    module_name = _get_driver()
    get_module = import_module(f"lib.drivers.credentials.{module_name}")
    return get_module


def _get_driver():
    get_name = get_dekickrc_value("project.providers.credentials.driver")
    return get_name
