from lib.dekickrc import get_dekickrc_value


def get_environments():
    """Get list of environments"""
    return get_dekickrc_value("project.environments")