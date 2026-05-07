"""CLI module for command-line interface."""

def main():
    from .menu import main as _main

    return _main()


__all__ = [
    "main"
]
