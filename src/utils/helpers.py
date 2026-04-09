import os


def pct(a, b):
    return 100 * (a / b - 1)


def ensure_folder(path: str):
    """Create folder if it does not exist."""
    os.makedirs(path, exist_ok=True)
