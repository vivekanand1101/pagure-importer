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

import pagure_importer.commands.fedorahosted
import pagure_importer.commands.github
import pagure_importer.commands.clone
import pagure_importer.commands.push
import pagure_importer.commands.mkconfig

if __name__ == '__main__':
    app()
