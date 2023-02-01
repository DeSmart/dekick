"""Terminal colors for printing to the terminal."""


class TerminalColors:  # pylint: disable=too-few-public-methods
    """class TerminalColors"""

    _reset = "\033[0m"
    _bold = "\033[01m"
    _disable = "\033[02m"
    _underline = "\033[04m"
    _reverse = "\033[07m"
    _strikethrough = "\033[09m"
    _invisible = "\033[08m"

    def reset(self) -> str:
        """Reset color"""
        return getattr(self, "_reset")

    def bold(self) -> str:
        """Bold color"""
        return getattr(self, "_bold")

    def fg(self, color: str) -> str:
        """Get color"""
        return getattr(self.foreground, f"_{color}")

    def bg(self, color: str) -> str:
        """Get background color"""
        return getattr(self.background, f"_{color}")

    class foreground:  # pylint: disable=too-few-public-methods, invalid-name
        """Foreground colors"""

        _black = "\033[30m"
        _red = "\033[31m"
        _green = "\033[32m"
        _orange = "\033[33m"
        _blue = "\033[34m"
        _purple = "\033[35m"
        _cyan = "\033[36m"
        _lightgrey = "\033[37m"
        _darkgrey = "\033[90m"
        _lightred = "\033[91m"
        _lightgreen = "\033[92m"
        _yellow = "\033[93m"
        _lightblue = "\033[94m"
        _pink = "\033[95m"
        _lightcyan = "\033[96m"

    class background:  # pylint: disable=too-few-public-methods, invalid-name
        """Background colors"""

        _black = "\033[40m"
        _red = "\033[41m"
        _green = "\033[42m"
        _orange = "\033[43m"
        _blue = "\033[44m"
        _purple = "\033[45m"
        _cyan = "\033[46m"
        _lightgrey = "\033[47m"
