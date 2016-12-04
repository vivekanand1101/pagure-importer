import click
import os
import subprocess as sp
from pagure_importer.app import app, REPO_PATH


@app.command()
@click.argument('repo_name')
def push(repo_name):
    if click.confirm('Before executing this command, you must have'
        ' "Pagure Tickets" enabled from pagure project\'s settings. Continue?'):
        repo = os.path.join(REPO_PATH, repo_name)
        os.chdir(repo)
        cmd = ['git', 'push', 'origin', 'master']
        proc = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.STDOUT)
        output, _ = proc.communicate()
        output = output.decode('utf-8')
        click.echo(output)
