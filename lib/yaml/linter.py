import sys

from rich.console import Console
from yamllint import config, linter

from lib.settings import (
    DEKICK_PATH,
    DEKICKRC_GLOBAL_HOST_PATH,
    DEKICKRC_GLOBAL_PATH,
    PROJECT_ROOT,
)

console = Console()


def lint(path):
    """Lint a YAML file."""
    yaml_config = config.YamlLintConfig(file=f"{DEKICK_PATH}/.yamllint.yml")

    with open(path, "r", encoding="utf-8") as file:
        description = list(linter.run(file, yaml_config))

        if len(description) == 0:
            return

        path_reduced = path.replace(f"{PROJECT_ROOT}/", "")
        path_reduced = path.replace(DEKICKRC_GLOBAL_PATH, DEKICKRC_GLOBAL_HOST_PATH)

        error = (
            "\nOoops, something terrible happened!\n\n"
            + f"You have a syntax error in your [bold]{path_reduced}[/bold] YAML file:\n"
        )

        for desc in description:
            error += f" - line {desc.line} has a {desc.desc}\n"

        console.print(error)
        sys.exit(1)
