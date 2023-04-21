from importlib import import_module

from lib.dekickrc import get_dekickrc_value
from lib.settings import DEKICKRC_FILE

# Public functions


def get_info() -> str:
    """Get info about driver"""
    _init()
    module = _get_driver_module()
    return module.info()


def get_envs(*args, **kwargs) -> str:
    """Get all variables from driver"""
    _init()
    try:
        module = _get_driver_module()
        return module.get_envs(*args, **kwargs)
    except Exception as exception:
        raise ValueError(f"{get_info()}: {exception.args[0]}") from exception


def parser_driver_arguments(parser):
    """Arg parse arguments for driver"""
    _init()
    module = _get_driver_module()
    return module.arguments(parser)


# Private functions

DRIVER_INITIALIZED = False


def _init():
    """Initialize driver, once per run"""
    if DRIVER_INITIALIZED:
        return
    _driver_init()


def _driver_init():
    """Initialize driver"""
    global DRIVER_INITIALIZED  # pylint: disable=global-statement
    if DRIVER_INITIALIZED is True:
        return
    module = _get_driver_module()

    try:
        module.init()
        DRIVER_INITIALIZED = True
    except Exception as exception:
        raise RuntimeError(f"{get_info()}: {exception.args[0]}") from exception


def _get_driver_module():
    """Gets driver module"""
    module_name = _get_driver_module_name()
    get_module = import_module(f"lib.drivers.credentials.{module_name}")
    return get_module


def _get_driver_module_name():
    """Get driver name"""
    module_name = get_dekickrc_value("project.providers.credentials.driver")
    if not module_name:
        raise ValueError(
            f"Missing key project.providers.credentials.driver in {DEKICKRC_FILE}"
        )
    return module_name
