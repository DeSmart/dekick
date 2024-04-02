import re
from sys import stdout

from halo import Halo

from lib.settings import C_CMD, C_CODE, C_END, C_FILE, TERMINAL_COLUMN_WIDTH

DEFAULT_SPINNER_MODE = ""


def get_spinner_mode() -> str:
    """Gets current spinner mode"""
    return DEFAULT_SPINNER_MODE


def set_spinner_mode(mode: str) -> None:
    """Sets spinner mode"""
    if mode not in ["simple", "null", "halo"]:
        mode = "simple" if not stdout.isatty() else "halo"

    global DEFAULT_SPINNER_MODE  # pylint: disable=global-statement
    DEFAULT_SPINNER_MODE = mode


def create_spinner(text: str):
    """Creates spinner"""
    if get_spinner_mode() == "halo":
        return Halo(
            text=text, interval=50, spinner="dots4", color="white", placement="left"
        )
    elif get_spinner_mode() == "null":
        return NullSpinner()

    return SimpleSpinner(text=text)


def len_valid_str(text) -> int:
    """Remove color control characters and return real length of string"""
    text = text.replace(C_CMD, "")
    text = text.replace(C_CODE, "")
    text = text.replace(C_END, "")
    text = text.replace(C_FILE, "")
    return len(text)


def str_pad_right(text: str, spare_width: int = 3) -> str:
    """Pads string to the right with spaces and takes terminal width into account"""
    return (TERMINAL_COLUMN_WIDTH - spare_width - len_valid_str(text)) * " "


class SimpleSpinner:
    """Simple spinner is used when there's no tty attached to the output"""

    initial_text: str = ""

    def __init__(self, text: str) -> None:
        print(text, end=str_pad_right(text, 8))
        self.initial_text = text

    def start(self):
        return self

    def succeed(self, text=None):
        self._print_text("✔", text)

    def warn(self, text=None):
        self._print_text("⚠", text)

    def fail(self, text=None):
        self._print_text("✖", text)

    def _print_text(self, mark: str, text=None):
        if text is not None:
            if self.initial_text in text:
                out_text = text.replace(self.initial_text, "").strip()
                print(f"{out_text} {mark}")
            else:
                bullet = " ⏵ "
                bullet_len = len(bullet)
                out_text = re.sub(r"\s{" + str(bullet_len) + "}(.*)$", "\\1", text)
                print(f"\n{bullet}{out_text} {mark}")
        else:
            print(f"     {mark}")


class NullSpinner:
    """Null spinner is used when spinner mode is set to null,
    defaults to not showing any spinner at all"""

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
