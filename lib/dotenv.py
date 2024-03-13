import re
import shlex

from dotenv import dotenv_values

from lib.settings import C_CMD, C_CODE, C_END, C_FILE


def get_dotenv_var(
    var: str, default: str = "", path: str = "", raise_exception: bool = True
) -> str:
    """Gets variable var from .env file"""

    path_parsed = path

    if path != "" and not path.endswith("/"):
        path_parsed = f"{path}/"

    config = dotenv_values(f"{path_parsed}.env")

    if var not in config and default == "":
        if raise_exception is True:
            raise KeyError(
                f"Variable {C_CMD}{var}{C_END} not found in {C_FILE}{path}.env{C_END} file"
            )
        return ""

    if var not in config and default != "":
        return default

    return str(config[var])


def dict2env(env_vars: dict, env: str) -> str:
    """Groups environment variables by prefix, sort them and adds comments."""
    output = ""
    ungrouped_output = ""
    grouped_output = ""
    groups = {}

    sorted_env_vars = dict(sorted(env_vars.items()))

    for var, value in sorted_env_vars.items():
        prefix = var.split("_")[0]
        value = shlex.quote(value)
        groups.setdefault(prefix, []).append((var, value))

    for group_name, values in groups.items():

        if len(values) == 1:
            ungrouped_output += f"{values[0][0]}={values[0][1]}\n"
        else:
            grouped_output += f"\n# {group_name} settings:\n"
            for var, value in values:
                grouped_output += f"{var}={value}\n"

    if grouped_output:
        output += grouped_output

    if ungrouped_output:
        if output:
            output += "\n"
        if grouped_output:
            output += "# Other settings:\n"
        output += f"{ungrouped_output}"

    output_stripped = output.strip()

    return f"### Environment: {env} ###\n{output_stripped}"


def env2dict(env: str) -> dict:
    """Extracts key-value pairs from env string and returns dict"""
    env_dict = {}
    lines = env.splitlines()

    for line in lines:
        if not line.strip() or line.strip().startswith("#"):
            continue

        match = re.match(
            r"^(?P<var_name>\w+[\w\d_]*)\s*=[\s\"']*(?P<var_value>.*?)[\"']*$", line
        )

        if match:
            var_name = match.group("var_name")
            var_value = match.group("var_value")
            env_dict[var_name] = var_value
        else:
            raise ValueError(
                f"Invalid line in env file, could not parse:\n{C_CODE}{line}{C_END}"
            )

    return env_dict
