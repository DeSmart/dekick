def init():
    pass


def get_vars(env: str) -> dict:
    """Gets all project variables from Gitlab"""
    config = {
        "test": {
            "SENTRY_DSN": "https://sentry.example/",
            "SENTRY_ORG": "sentry",
        },
        "production": {
            "SENTRY_DSN": "https://sentry.io/",
            "SENTRY_ORG": "sentry",
        },
    }

    return config[env]


def update_vars(env: str, vars: dict) -> None:
    """Updates all project variables in Gitlab"""
    pass
