import click
import getpass
import pagure_importer
from pagure_importer.app import app, REPO_PATH
from pagure_importer.utils.importer_github import GithubImporter
from pagure_importer.utils import (
    generate_json_for_github_contributors,
    generate_json_for_github_issue_commentors,
    assemble_github_contributors_commentors
)


def form_github_issues():
    github_username = raw_input('Enter you Github Username: ')
    github_password = getpass.getpass('Enter your github password: ')
    github_project_name = raw_input('Enter github project name like: "pypingou/pagure" without quotes: ')
    return (github_username, github_password, github_project_name)


@app.command()
def github():
    github_username, github_password, github_project_name = form_github_issues()
    gen_json = raw_input(
        'Do you want to generate jsons for project\'s contributers and issue commentors? (y/n): ')
    if gen_json == 'n':
        github_importer = GithubImporter(
            github_username=github_username,
            github_password=github_password,
            github_project_name=github_project_name)

        repos = pagure_importer.utils.display_repo()
        if repos:
            repo_index = raw_input('Choose the import destination repo (default 1) : ') or 1
            repo_name = repos[int(repo_index)-1]
            github_importer.import_issues(repo_path=repo_name, repo_folder=REPO_PATH)
        else:
            click.echo('No ticket repository found. Use pgimport clone command')

    else:
        generate_json_for_github_contributors(
            github_username,
            github_password,
            github_project_name)
        generate_json_for_github_issue_commentors(
            github_username,
            github_password,
            github_project_name)
        assemble_github_contributors_commentors()
    return
