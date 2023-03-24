from importlib import import_module

from lib.dekickrc import get_dekickrc_value

INIT = False


def driver_init():
    module = _get_driver_module()
    module.init()
    global INIT
    INIT = True


def get_vars(env: str) -> dict:
    _init()
    module = _get_driver_module()
    return module.get_vars(env)


def update_vars(env: str, vars: dict) -> dict:
    _init()
    module = _get_driver_module()
    return module.update_vars(env, vars)


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
