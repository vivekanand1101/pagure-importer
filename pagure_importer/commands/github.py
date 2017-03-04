import click

import pagure_importer
from pagure_importer.app import app, REPO_PATH
from pagure_importer.utils.importer_github import GithubImporter
from pagure_importer.utils import (
    gh_get_contributors, gh_get_issue_users,
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
              prompt='Enter name of pagure project: \n'
                     ' 1. it is a fork then like: fork/<username>/<projectname>\n'
                     ' 2. it has a namespace: <namespacename>/<projectname>\n'
                     ' 3. it is a fork of namespaced project:'
                     ' fork/<username>/<namespacename>/<projectname>')
def github(username, project, nopush, pagure_project, status, gencsv):
    ''' For imports from github '''

    password = click.prompt("Github Password", hide_input=True)
    pagure_project = pagure_project.strip().strip('/')
    if gencsv:
        gh_get_contributors(username, password, project)
        gh_get_issue_users(username, password, project)
        gh_assemble_users()
    else:
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
        else:
            click.echo(
                'No ticket repository found. Use pgimport clone command')
            return

    return
