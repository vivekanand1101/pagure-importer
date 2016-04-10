import getpass

from lib.sources.importer_github_new import GithubImporter
from settings import REPO_PATH, REPO_NAME

def form_github_issues():
    github_username = raw_input('Enter you Github Username: ')
    github_password = getpass.getpass('Enter your github password: ')
    github_project_name = raw_input('Enter github project name like: "pypingou/pagure" without quotes: ')
    return (github_username, github_password, github_project_name)
