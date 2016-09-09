import click
import os
import sys
import subprocess as sp
from pagure_importer.app import app, REPO_PATH


@app.command()
@click.argument('repo_name')
def push (repo_name):
    not_cont = raw_input('Before executing this command, you must have'
        ' "Pagure Tickets" enabled from pagure project\'s settings'
        ' (Pressing just "Enter" will continue): ')
    if not_cont:
        sys.exit(1)
    repo = os.path.join(REPO_PATH, repo_name)
    os.chdir(repo)
    cmd = ['git', 'push', 'origin', 'master' ]
    proc = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.STDOUT)
    output, _ = proc.communicate()
    output = output.decode('utf-8')
    click.echo(output)
