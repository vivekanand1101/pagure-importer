#import pagure_importer
from sources.importer_github import GithubImporter
import getpass

def form_github_issues():
    github_username = raw_input('Enter you Github Username: ')
    github_password = getpass.getpass('Enter your github password: ')
    github_project_name = raw_input('Enter github project name: ')
    pagure_api_key = raw_input('Enter your pagure api key: ')
    pagure_project_name = raw_input('Enter pagure project name: ')

    is_forked = raw_input('Is the pagure project a forked repo ? (y/n): ') or 'y'
    if is_forked.lower() == 'y':
        pagure_username = raw_input('Enter your pagure username: ')
    else:
        pagure_username = None

    is_pagure_io = raw_input(
                'Is the pagure instance url - https://pagure.io ?: (y/n) ') or 'y'
    if is_pagure_io.lower() == 'n':
        pagure_instance = raw_input('Enter the pagure instance url: ') or 'https://pagure.io'
    else:
        pagure_instance = 'https://pagure.io'

    status = raw_input(
            'Enter status of the issues to be imported (all/open/closed): ') or 'all'

    github_importer = GithubImporter(
                        github_username=github_username,
                        github_password=github_password,
                        github_project_name=github_project_name,
                        pagure_api_key=pagure_api_key,
                        pagure_project_name=pagure_project_name,
                        pagure_username=pagure_username,
                        instance_url=pagure_instance)
    github_importer.import_issues(status)
