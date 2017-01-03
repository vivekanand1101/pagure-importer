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
@click.option('--nopush', is_flag=True,
              help="Do not push the result of pagure-importer back")
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


            newpath, new_repo = clone_repo(repo_path, repo_folder)

            with GithubImporter(username=username,
                                password=password,
                                project=project,
                                repo_name=repo_name,
                                repo_folder=REPO_PATH) as github_importer:

                repo = github_importer.github.get_repo(
                    github_importer.github_project_name)
                try:
                    repo_name = repo.name
                except:
                    raise GithubRepoNotFound(
                            'Repo not found, project name wrong')
                github_importer.import_issues(repo, new_repo)

            # update the local git repo
            new_repo = update_git(pagure_issue, newpath, new_repo)

            if not nopush:
                push_delete_repo(newpath, new_repo)
        else:
            click.echo(
                'No ticket repository found. Use pgimport clone command')
            return

    return
