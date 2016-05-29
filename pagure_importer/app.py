#!/usr/bin/env python
import click
import tempfile

REPO_NAME = ''
REPO_PATH = tempfile.gettempdir()


@click.group()
def app():
    pass

__all__ = [
    'app',
]

from .commands import fedorahosted
from .commands import github
from .commands import clone

if __name__ == '__main__':
    app()
