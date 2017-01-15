import csv
import os
import sys
import json
import re
import shutil

import click
import hashlib
import pygit2
import werkzeug

from urllib.parse import urlparse
from configparser import ConfigParser
from github import Github
from github.GithubException import TwoFactorException
from pagure_importer.utils.exceptions import FileNotFound, EmailNotFound
from pagure_importer.app import REPO_PATH

CFG_PATH = os.path.join(os.environ.get('HOME'), '.pgimport')
CONFIG = ConfigParser()
CONFIG.optionxform = str


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


def create_config():
    '''Create the config file with default close statuses
    and an empty github auth_token'''

    CONFIG['close_status'] = {'Invalid': ['invalid', 'wontfix', 'worksforme'],
                              'Insufficient data': ['insufficient_info'],
                              'Duplicate': ['duplicate']}
    CONFIG['github'] = {'auth_token': ''}
    if os.path.exists(CFG_PATH):
        if click.confirm('You already have a config file, if you continue '
                         'your custom settings will be lost'):
            with click.open_file(CFG_PATH, 'w+') as config_file:
                CONFIG.write(config_file)
        else:
            sys.exit(1)
    else:
        with click.open_file(CFG_PATH, 'w+') as config_file:
            CONFIG.write(config_file)


def get_close_status():
    ''' Read the config file and returns the close statuses'''

    close_status = None
    if os.path.exists(CFG_PATH):
        CONFIG.read(CFG_PATH)
        close_status = CONFIG['close_status']
    else:
        create_config()
        CONFIG.read(CFG_PATH)
        close_status = CONFIG['close_status']
    return close_status


def get_auth_token(github):
    ''' Checks the .pgimport file for github authentication key,
    if it is not present, creates it. '''

    if os.path.exists(CFG_PATH):
        CONFIG.read(CFG_PATH)
        otp_auth = CONFIG['github']['auth_token']
        if not otp_auth:
            otp_auth = create_auth_token(github)
            CONFIG['github']['auth_token'] = otp_auth.token
            with click.open_file(CFG_PATH, 'w+') as config_file:
                CONFIG.write(config_file)
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
    project_commits = project.get_commits()
    contributors = []
    for commit in project_commits:
        contributor = {'fullname': commit.author.name,
                       'emails': commit.commit.author.email,
                       'name': commit.author.login}
        if contributor not in contributors:
            contributors.append(contributor)
            click.echo('contributor added: ' + contributor['name'])

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


def get_pagure_namespace(repo_folder, repo_name):
    ''' returns pagure namespace in the following format:
    GROUP/PROJECT
    '''

    repo_path = os.path.join(repo_folder, repo_name)
    repo = pygit2.Repository(repo_path)
    remote_url = repo.remotes['origin'].url
    remote_path = urlparse(remote_url).path
    remote_path = remote_path.replace('.git', '')
    namespace_list = remote_path.split('/')[2:]
    return '/'.join(namespace_list)


def is_image(filename):
    ''' True is filename extension is .jpg, .png, .gif, .bmp or .jpeg else False'''

    if re.search('\.(jpg|png|gif|bmp|jpeg|JPG|PNG|GIF|BMP|JPEG)',
                 filename) is not None:
        return True
    else:
        return False


def issue_to_json(issue, folder):
    ''' Write the specified issue as a JSON blob on the specified folder.
    Returns a list of all the files changed or created.

    :arg issue: a

    '''
    file_path = os.path.join(folder, issue.uid)
    files = []

    # Are we adding files
    added = False
    if not os.path.exists(file_path):
        files.append(issue.uid)

    # If we have attachments
    attachments = issue.attachment
    if attachments:
        if not os.path.exists(os.path.join(folder, 'files')):
            os.mkdir(os.path.join(folder, 'files'))

        for key in attachments.keys():
            filename = get_secure_filename(attachments[key], key)
            attach_path = os.path.join(folder, 'files', filename)
            # Try decoding Bytes to UTF-8
            try:
                with open(attach_path, 'w') as stream:
                    stream.write(attachments[key].decode())
            # If it fails write the data as binary
            except UnicodeDecodeError:
                with open(attach_path, 'wb') as stream:
                    stream.write(attachments[key])
            files.append('files/' + filename)

    # Write down what changed
    with open(file_path, 'w') as stream:
        stream.write(json.dumps(
            issue.to_json(), sort_keys=True, indent=4,
            separators=(',', ': ')))

    return files


def get_secure_filename(attachment, filename):
    ''' Hashes the file name, same as pagure '''
    filename = '%s-%s' % (hashlib.sha256(attachment).hexdigest(),
                          werkzeug.secure_filename(str(filename)))
    return filename
