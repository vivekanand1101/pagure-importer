import csv
import os
import requests
import json
import click
import ConfigParser
from github import Github
from github.GithubException import TwoFactorException

from requests.auth import HTTPBasicAuth

from pagure_importer.utils.exceptions import FileNotFound, EmailNotFound
from pagure_importer.app import REPO_PATH


def create_auth_token(github):
    ''' Creates github authentication token. If Two Factor Authentication
    is enabled, the user will be asked to enter the key '''

    user = github.get_user()
    try:
        otp_auth = user.create_authorization(scopes=['user'],
                                             note='pgimport')
    except TwoFactorException:
        otp_key = click.prompt("Enter github Two-Factor Auth key: ")
        otp_auth = user.create_authorization(scopes=['user'],
                                             note='pgimport',
                                             onetime_password=otp_key)
    return otp_auth


def get_auth_token(github):
    ''' Checks the .pgimport file for github authentication key,
    if it is not present, creates it. '''

    cfg_path = os.path.join(os.environ.get('HOME'), '.pgimport')
    if os.path.exists(cfg_path):
        parser = ConfigParser.RawConfigParser()
        parser.read(cfg_path)
        otp_auth = parser.get('github', 'auth_token')
    else:
        otp_auth = create_auth_token(github)
        otp_auth = otp_auth.token
        with click.open_file(cfg_path, 'w+') as fp:
            fp.write('[github] \nauth_token : %s' % otp_auth)
    return otp_auth


def display_repo():
    ''' Displays the list of repos elegantly '''

    repo = []
    index = 0
    click.secho('#### Repo available ####', fg='blue')
    for file in os.listdir(REPO_PATH):
        if file.endswith('.git'):
            index += 1
            click.echo(str(index) + ' - ' + file)
            repo.append(file)
    click.echo()
    return repo


def gh_get_contributors(github_username, github_password, github_project_name):
    ''' Creates a file containing a list of dicts containing the username and
    emails of the contributors in the given github project
    '''

    github_obj = Github(github_username, github_password)
    otp_auth = get_auth_token(github_obj)
    github_obj = Github(otp_auth)
    project = github_obj.get_repo(github_project_name)
    commits_url = project.commits_url.replace('{/sha}', '')

    page = 0
    contributors = []
    while True:
        page += 1
        payload = {'page': page}
        data_ = json.loads(requests.get(
                    commits_url, params=payload,
                    auth=HTTPBasicAuth(github_username, github_password)).text)

        if not data_:
            break

        for data in data_:
            try:
                contributor = data['commit']['committer']
                contributor_email = contributor['email']
                contributor_fullname = contributor['name']
                contributor_name = data['committer']['login']
            except TypeError:
                click.echo('Maybe one of the contributors is dropped because\
                            of lack of details')
                continue

            json_data = {
                'name': contributor_name,
                'fullname': contributor_fullname,
                'emails': [contributor_email]
            }

            present = False
            for i in contributors:
                if i == json_data:
                    present = True
                    break

            if not present:
                click.echo('contributor added: ' + contributor_name)
                contributors.append(json_data)

    with open('contributors.json', 'w') as f:
        f.write(json.dumps(contributors))

    return


def gh_get_issue_users(github_username, github_password, github_project_name):
    ''' Will create a json file containing details of all the user
    who have commented on or filed any issue in the given project
    This also contains users who are assignee of an issue
    '''

    github_obj = Github(github_username, github_password)
    otp_auth = get_auth_token(github_obj)
    github_obj = Github(otp_auth)
    project = github_obj.get_repo(github_project_name)
    issue_commentors_assignees = []

    for issue in project.get_issues(state='all'):
        if issue.user.login not in issue_commentors_assignees:
            issue_commentors_assignees.append(issue.user.login)
            click.echo('commentor added: ' + issue.user.login)

        if issue.assignee is not None and \
                issue.assignee.login not in issue_commentors_assignees:
            issue_commentors_assignees.append(issue.assignee.login)
            click.echo('assignee added: ' + issue.assignee.login)

    for comment in project.get_issues_comments():
        if comment.user.login not in issue_commentors_assignees:
            issue_commentors_assignees.append(comment.user.login)
            click.echo('commentor added: ' + comment.user.login)

    with open('issue_users.json', 'w') as f:
        f.write(json.dumps(issue_commentors_assignees))
    return


def gh_assemble_users():
    ''' It uses the files: issue_commentors.json and contributors.json
    Assembles and creates a file: assembled_commentors.csv
    To use: just fill the empty blocks under emails column'''

    with open('issue_users.json', 'r') as ic:
        issue_names = json.load(ic)

    with open('contributors.json', 'r') as c:
        contributors = json.load(c)

    names = []
    for i in issue_names:
        found = False
        for j in contributors:
            if j.get('name', None) == i:
                j['emails'] = j.get('emails')[0]
                names.append(j)
                found = True

        if not found:
            d = {'name': i, 'fullname': None, 'emails': None}
            names.append(d)

    with open('assembled_users.csv', 'w') as ac:
        field_names = ['name', 'fullname', 'emails']
        writer = csv.DictWriter(ac, fieldnames=field_names)

        writer.writeheader()
        for name in names:
            writer.writerow(name)


def gh_get_user_email(name):
    ''' Will return the issue commentor email as given in the
    assembled_users.csv file
    '''

    if not os.path.exists('assembled_users.csv'):
        raise FileNotFound('The assembled_commentors.json file must be present'
                           ' Rerun the program and choose to generate the json'
                           ' files')

    data = []
    with open('assembled_users.csv') as ac:
        reader = csv.DictReader(ac)
        for row in reader:
            data.append(dict(
                (('name', row['name']),
                 ('fullname', row['fullname']),
                 ('emails', row['emails']))))

    for i in data:
        if i.get('name', None) == name:
            if i['emails']:
                return str(i['emails'])
            else:
                raise EmailNotFound('You need to fill out all the emails of'
                                    ' the issue commentors')
