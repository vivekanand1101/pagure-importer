import click
import pagure_importer
from pagure_importer.app import app, REPO_PATH
from pagure_importer.utils import importer_trac
from pagure_importer.utils.fas import FASclient


@app.command()
@click.argument('project_url')
@click.option('--tags', help="Import pagure tags:", is_flag=True)
@click.option('--private', help="By default make all issues private",
              is_flag=True)
@click.option('--username', prompt="Enter your FAS Username: ",
              help="FAS username")
@click.option('--password', prompt=True, hide_input=True,
              help="FAS password")
def fedorahosted(project_url, tags, private, username, password):
    fasclient = FASclient(username, password,
                          'https://admin.fedoraproject.org/accounts')
    project_url = project_url + '/login/jsonrpc'
    repos = pagure_importer.utils.display_repo()
    if repos:
        repo_index = click.prompt('Choose the import destination repo ',
                                  default=1)
        repo_name = repos[int(repo_index)-1]
        trac_importer = importer_trac.TracImporter(project_url, username,
                                                   password, fasclient, tags,
                                                   private)
        trac_importer.import_issues(repo_name=repo_name, repo_folder=REPO_PATH)
    else:
        click.echo('No ticket repository found. Use pgimport clone command')
