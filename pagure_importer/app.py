#!/usr/bin/env python
import click
import tempfile

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
from .commands import push

if __name__ == '__main__':
    app()
