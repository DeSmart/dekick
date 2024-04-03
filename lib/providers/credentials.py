import sys
from importlib import import_module

from beaupy import select
from rich.console import Console

from lib.dekickrc import get_dekickrc_value
from lib.settings import C_BOLD, C_END, C_FILE, DEKICKRC_FILE

console = Console()


# Public functions
def get_info() -> str:
    """Get info about driver"""
    _configure()
    module = _get_driver_module()
    return module.info()


def get_driver_name() -> str:
    """Get driver name"""
    return _get_driver_module_name()


def get_envs(*args, **kwargs) -> str:
    """Get all variables from driver"""
    _configure()
    try:
        return _get_driver_module().get_envs(*args, **kwargs)
    except Exception as exception:
        raise ValueError(f"{get_info()}: {exception.args[0]}") from exception


def get_actions() -> list[tuple[str, str]]:
    """Get driver documentation"""
    _configure()
    return _get_driver_module().get_actions()


def parser_driver_arguments(sub_command: str, parser):
    """Arg parse arguments for driver"""
    _configure()
    return _get_driver_module().arguments(sub_command, parser)


def ui_init() -> bool:
    """Initialize driver"""
    _configure()
    return _get_driver_module().ui_init()


def ui_pull() -> bool:
    """Pull all environment variables and save to envs/ dir for further processing"""
    _configure()
    return _get_driver_module().ui_pull()


def ui_push() -> bool:
    """Push all environment variables to provider"""
    _configure()
    return _get_driver_module().ui_push()


def ui_run_action() -> bool:
    """Run driver"""
    _configure()
    ARG_ACTION = sys.argv[3] if len(sys.argv) > 3 else None
    action_name = ""

    if not ARG_ACTION:
        actions = list()
        for action_name, doc in get_actions():
            action_name = action_name.replace("_", " ")
            actions.append(f"{C_FILE}{C_BOLD}{action_name}{C_END} - {doc}")

        console.print("\nChoose an action:", style="bold")
        ARG_ACTION = select(actions, cursor="🢧", cursor_style="cyan")
        sys.stdout.write("\033[F")  # Cursor up one line
        sys.stdout.write("\033[K")  # Clear line
        sys.stdout.write("\033[F")  # Cursor up one line
        sys.stdout.write("\033[K")  # Clear line

        action_name = get_actions()[actions.index(ARG_ACTION)][1]
        console.print(f"\n{action_name}", style="bold")

        if not ARG_ACTION:
            return False
    else:
        action_name = get_actions()[
            [action.lower() for action, _ in get_actions()].index(ARG_ACTION)
        ][1]
        console.print(f"\n{action_name}", style="bold")

    action_module = (
        str(ARG_ACTION)
        .split(" - ")[0]
        .replace(f"{C_FILE}{C_BOLD}", "")
        .replace(f"{C_END}", "")
        .replace(" ", "_")
        .lower()
    )

    return _get_driver_module(action_module).ui_action()


# Private functions
DRIVER_CONFIGURED = False


def _configure():
    """Initialize driver, once per run"""
    if DRIVER_CONFIGURED:
        return
    _driver_configure()


def _driver_configure():
    """Initialize driver"""
    global DRIVER_CONFIGURED  # pylint: disable=global-statement
    if DRIVER_CONFIGURED is True:
        return
    module = _get_driver_module()

    try:
        module.configure()
        DRIVER_CONFIGURED = True
    except Exception as exception:
        raise RuntimeError(f"{get_info()}: {exception.args[0]}") from exception


def _get_driver_module(submodule: str = "_main"):
    """Gets driver module"""
    module_name = _get_driver_module_name()
    get_module = import_module(f"lib.drivers.credentials.{module_name}.{submodule}")
    return get_module


def _get_driver_module_name() -> str:
    """Get driver name"""
    module_name = get_dekickrc_value("project.providers.credentials.driver")
    if not module_name:
        raise KeyError("No driver")
    return str(module_name)
