import click
import os
import subprocess as sp
from pagure_importer.app import app, REPO_PATH


@app.command()
@click.argument('repo_url')
def clone(repo_url):
        repo = os.path.join(REPO_PATH, repo_url.split('/')[-1])
        cmd = ['git', 'clone', '--bare', repo_url, repo]
        proc = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.STDOUT)
        output, _ = proc.communicate()
        output = output.decode('utf-8')
        click.echo(output)
