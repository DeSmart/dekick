from flavours.shared import setup_permissions as shared_setup_permissions


def get_container() -> str:
    return "api"


def setup_permissions():
    shared_setup_permissions("/.cache/ /.yarn/ /.pm2 dist/")
