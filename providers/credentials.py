from importlib import import_module

from dekickrc import get_dekickrc_value

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
    return import_module(f"providers.credentials.{_get_driver()}")


def _get_driver() -> str:
    return get_dekickrc_value(".project.providers.credentials.driver")
