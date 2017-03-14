import click

import pagure_importer
from pagure_importer.app import app, REPO_PATH
from pagure_importer.utils.importer_github import GithubImporter
from pagure_importer.utils import (
    gh_get_contributors, gh_get_issue_users, prepare_pagure_project,
    gh_assemble_users, validate_gh_project,
)

import pagure_importer.utils.git as gitutils


@app.command()
@click.option('--username', prompt='Enter your Github Username',
              help="Github username")
@click.option('--project',
              prompt='Github project name like pypingou/pagure',
              callback=validate_gh_project,
              help="Github project name like pypingou/pagure")
@click.option('--gencsv', is_flag=True, default=False)
@click.option('--status', type=click.Choice(['all', 'open', 'closed']),
              default='all',
              help="Status of issue/PR to be imported(open/closed/all)")
@click.option('--nopush', is_flag=True,
              help="Do not push the result of pagure-importer back")
@click.option('--pagure_project',
              help="Name of the pagure project without namespace or 'fork'")
@click.option('--namespace', help="Name of the namespace of the pagure project")
@click.option('--is_fork', is_flag=True, default=False)
@click.option('--nosearch', is_flag=True,
              help="Do not go through the list of commits to find email ids")
def github(username, project, nopush, pagure_project,
           status, gencsv, namespace, is_fork, nosearch):
    ''' For imports from github '''

    password = click.prompt("Github Password", hide_input=True)
    if gencsv:
        if not nosearch:
            gh_get_contributors(username, password, project)
        gh_get_issue_users(username, password, project)
        gh_assemble_users()
        return

    if not pagure_project:
        pagure_project = click.prompt("Pagure project name without namespace")

    pagure_project = prepare_pagure_project(
        name=pagure_project,
        namespace=namespace,
        is_fork=is_fork
    )

    repos = pagure_importer.utils.display_repo()
    if repos:
        repo_index = click.prompt(
            'Choose the import destination repo', default=1)
        repo_name = repos[int(repo_index)-1]

        newpath, new_repo = gitutils.clone_repo(repo_name, REPO_PATH)

        with GithubImporter(username=username,
                            password=password,
                            project=project,
                            repo_name=repo_name,
                            repo_folder=REPO_PATH,
                            pagure_project=pagure_project,
                            nopush=nopush) as github_importer:

            repo = github_importer.github.get_repo(
                github_importer.github_project_name)
            github_importer.import_issues(repo, status=status)

            # update the local git repo
            new_repo = gitutils.update_git(
                new_repo,
                commit_message='Imported issues from the github project: %s' % repo_name)

            if not nopush:
                gitutils.push_repo(new_repo)
        return
    click.echo(
        'No ticket repository found. Use pgimport clone command')
    return
