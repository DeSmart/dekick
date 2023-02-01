from sys import stdout

from halo import Halo

from lib.settings import C_CMD, C_CODE, C_END, C_FILE, TERMINAL_COLUMN_WIDTH

DEFAULT_SPINNER_MODE = ""


def get_spinner_mode() -> str:
    return DEFAULT_SPINNER_MODE


def set_spinner_mode(mode: str) -> None:
    if mode not in ["simple", "null", "halo"]:
        mode = "simple" if not stdout.isatty() else "halo"

    global DEFAULT_SPINNER_MODE  # pylint: disable=global-statement
    DEFAULT_SPINNER_MODE = mode


def create_spinner(text: str):
    if get_spinner_mode() == "halo":
        return Halo(text=text, spinner="dots4", color="white", placement="left")
    elif get_spinner_mode() == "null":
        return NullSpinner()

    return SimpleSpinner(text=text)


def len_valid_str(text) -> int:
    """Remove color control characters and return real length of string

    Args:
        text (_type_): _description_

    Returns:
        int: _description_
    """
    text = text.replace(C_CMD, "")
    text = text.replace(C_CODE, "")
    text = text.replace(C_END, "")
    text = text.replace(C_FILE, "")
    return len(text)


def str_pad_right(text: str) -> str:
    return (TERMINAL_COLUMN_WIDTH - 3 - len_valid_str(text)) * " "


class SimpleSpinner:
    def __init__(self, text: str) -> None:
        print(text, end=str_pad_right(text))

    def start(self):
        return self

    def succeed(self, text=None):
        print("✔")
        self._print_text(text)

    def warn(self, text=None):
        print("⚠")
        self._print_text(text)

    def fail(self, text=None):
        print("✖")
        self._print_text(text)

    def _print_text(self, text=None):
        if text is not None:
            print(f"╰─ {text}")


class NullSpinner:
    def __init__(self) -> None:
        return

    def start(self):
        return self

    def succeed(self, text=None):
        return text

    def warn(self, text=None):
        return text

    def fail(self, text=None):
        return text

    def _print_text(self, text=None):
        return text
