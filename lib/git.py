import os

from lib.settings import PROJECT_ROOT


def is_git_repository() -> bool:
    """Check if the current project directory is a git repository."""
    return os.path.exists(os.path.join(PROJECT_ROOT, ".git"))
