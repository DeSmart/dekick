from lib.dekickrc import get_dekickrc_value


def get_environments() -> list:
    """Get list of environments"""
    environments_list = ["local"]
    for environment in get_dekickrc_value("project.environments"):  # type: ignore
        environments_list.extend(list(environment.values()))
    return environments_list
