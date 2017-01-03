import click
import pagure_importer
from pagure_importer.app import app, REPO_PATH
from pagure_importer.utils import importer_trac, get_pagure_namespace
from pagure_importer.utils.fas import FASclient

import pagure_importer.utils.git as gitutils


@app.command()
@click.argument('project_url')
@click.option('--tags', help="Import pagure tags:", is_flag=True)
@click.option('--private', help="By default make all issues private",
              is_flag=True)
@click.option('--username', prompt="Enter your FAS Username",
              help="FAS username")
@click.option('--password', prompt=True, hide_input=True,
              help="FAS password")
@click.option('--offset', default=0,
              help='Number of issue in pagure before import')
def fedorahosted(project_url, tags, private, username, password, offset):
    project_url = project_url.rstrip('/')
    fasclient = FASclient(username, password,
                          'https://admin.fedoraproject.org/accounts')
    project_url += '/login/jsonrpc'
    repos = pagure_importer.utils.display_repo()
    if repos:
        repo_index = click.prompt('Choose the import destination repo ',
                                  default=1)
        repo_name = repos[int(repo_index)-1]
        newpath, new_repo = gitutils.clone_repo(repo_name, REPO_PATH)
        project = get_pagure_namespace(REPO_PATH, repo_name)
        with importer_trac.TracImporter(project_url=project_url,
                                        username=username,
                                        password=password,
                                        offset=offset,
                                        repo_name=repo_name,
                                        repo_folder=REPO_PATH,
                                        fasclient=fasclient,
                                        tags=tags,
                                        private=private) as trac_importer:

            trac_importer.import_issues(project, REPO_PATH)
        # update the local git repo
        new_repo = gitutils.update_git(newpath, new_repo)
        gitutils.push_delete_repo(newpath, new_repo)
    else:
        click.echo('No ticket repository found. Use pgimport clone command')
