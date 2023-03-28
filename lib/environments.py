from lib.dekickrc import get_dekickrc_value


def get_environments() -> list:
    """Get list of environments"""
    environments_list = ["local"]
    environments = get_dekickrc_value("project.environments")

    if not environments:
        return environments_list

    for environment in environments:  # type: ignore
        environments_list.extend(list(environment.values()))
    return environments_list
