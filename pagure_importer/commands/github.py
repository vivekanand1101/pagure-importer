import click
import pagure_importer
from pagure_importer.app import app, REPO_PATH
from pagure_importer.utils.importer_github import GithubImporter
from pagure_importer.utils import (
    generate_json_for_github_contributors,
    generate_json_for_github_issue_commentors,
    assemble_github_contributors_commentors
)


@app.command()
@click.option('--username', prompt="Enter your Github Username: ",
              help="Github username")
@click.option('--password', prompt=True, hide_input=True,
              help="Github password")
@click.option('--project',
              prompt='Enter github project name like pypingou/pagure: ',
              help="Github project like pypingou/pagure")
def github(username, password, project):
    gen_json = click.confirm(
        "Do you want to generate jsons for project's contributers and issue commentors?")
    if gen_json:
        generate_json_for_github_contributors(
            username,
            password,
            project)
        generate_json_for_github_issue_commentors(
            username,
            password,
            project)
        assemble_github_contributors_commentors()
    else:
        repos = pagure_importer.utils.display_repo()
        if repos:
            repo_index = click.prompt(
                'Choose the import destination repo', default=1)
            repo_name = repos[int(repo_index)-1]

            github_importer = GithubImporter(
                username=username,
                password=password,
                project=project)

            github_importer.import_issues(
                repo_path=repo_name, repo_folder=REPO_PATH)
        else:
            click.echo(
                'No ticket repository found. Use pgimport clone command')
            return

    return
