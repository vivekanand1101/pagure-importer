#!/usr/bin/env python

import click
import os

REPO_NAME = os.environ.get('REPO_NAME', None)  # this has to be a bare repo
REPO_PATH = os.environ.get('REPO_PATH', None)  # the parent of the git directory


@click.group()
def app():
    pass

__all__ = [
    'app',
]

# from .commands import github
from .commands import fedorahosted
from .commands import github

if __name__ == '__main__':
    app()
