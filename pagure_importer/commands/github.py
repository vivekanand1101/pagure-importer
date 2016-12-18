import click
import pagure_importer
from pagure_importer.app import app, REPO_PATH
from pagure_importer.utils.importer_github import GithubImporter
from pagure_importer.utils import (
    gh_get_contributors, gh_get_issue_users, gh_assemble_users,
)


@app.command()
@click.option('--username', prompt='Enter your Github Username',
              help="Github username")
@click.option('--password', prompt=True, hide_input=True,
              help="Github password")
@click.option('--project',
              prompt='Enter github project name like pypingou/pagure',
              help="Github project like pypingou/pagure")
def github(username, password, project):
    gen_json = click.confirm(
        "Do you want to generate jsons for project's contributers"
        " and issue commentors?")
    if gen_json:
        gh_get_contributors(username, password, project)
        gh_get_issue_users(username, password, project)
        gh_assemble_users()
    else:
        repos = pagure_importer.utils.display_repo()
        if repos:
            repo_index = click.prompt(
                'Choose the import destination repo', default=1)
            repo_name = repos[int(repo_index)-1]

            with GithubImporter(username=username,
                                password=password,
                                project=project,
                                repo_name=repo_name,
                                repo_folder=REPO_PATH) as github_importer:

                github_importer.import_issues()
        else:
            click.echo(
                'No ticket repository found. Use pgimport clone command')
            return

    return
