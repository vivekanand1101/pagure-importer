import git
import models

import csv
import os
import getpass
import requests
import json
from github import Github
from requests.auth import HTTPBasicAuth
import pagure_importer
import pagure_importer.lib
from pagure_importer.lib.exceptions import FileNotFound, EmailNotFound

def generate_json_for_github_contributors(github_username, github_password, \
                                                github_project_name):
    ''' Creates a file containing a list of dicts containing the username and
    emails of the contributors in the given github project
    '''

    github_obj = Github(github_username, github_password)
    project = github_obj.get_repo(github_project_name)
    commits_url = project.commits_url.replace('{/sha}', '')

    page = 0
    contributors = []
    while True:
        page += 1
        payload = {'page': page }
        data_ = json.loads(requests.get(commits_url, params=payload,
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
                print 'Maybe one of the contributors is dropped because of lack of details'
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
                print 'contributor added: ', contributor_name
                contributors.append(json_data)

    with open('contributors.json', 'w') as f:
        f.write(json.dumps(contributors))

    return


def generate_json_for_github_issue_commentors(github_username, github_password, \
                                                github_project_name):
    ''' Will create a json file containing details of all the user
    who have commented on any issue in the given project
    '''

    github_obj = Github(github_username, github_password)
    project = github_obj.get_repo(github_project_name)
    issue_comment_url = project.issue_comment_url.replace('{/number}', '')

    page = 0
    issue_commentors = []
    while True:
        page += 1
        payload = {'page': page }
        data_ = json.loads(requests.get(issue_comment_url, params=payload,
                    auth=HTTPBasicAuth(github_username, github_password)).text)

        if not data_:
            break

        for data in data_:
            try:
                commentor = data['user']['login']
            except TypeError:
                print 'Maybe one of the issue commentors have been dropped because of lack of details'
                continue

            present = False
            for i in issue_commentors:
                if i == commentor:
                    present = True
                    break

            if not present:
                print 'commentor added: ', commentor
                issue_commentors.append(commentor)

    with open('issue_commentors.json', 'w') as f:
        f.write(json.dumps(issue_commentors))
    return


def assemble_github_contributors_commentors():
    ''' It uses the files: issue_commentors.json and contributors.json
    Assembles and creates a file: assembled_commentors.json
    To use: just fill the None and [] in the final file '''

    with open('issue_commentors.json', 'r') as ic:
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

    with open('assembled_commentors.csv', 'w') as ac:
        field_names = ['name', 'fullname', 'emails']
        writer = csv.DictWriter(ac, fieldnames=field_names)

        writer.writeheader()
        for name in names:
            writer.writerow(name)


def github_get_commentor_email(name):
    ''' Will return the issue commentor email as given in the
    assembled_commentors.csv file
    '''

    if not os.path.exists('assembled_commentors.csv'):
        raise FileNotFound('The assembled_commentors.json file must be present \
                Rerun the program and choose to generate the json files')

    data = []
    with open('assembled_commentors.csv') as ac:
        reader = csv.DictReader(ac)
        for row in reader:
            data.append(dict( \
                (('name', row['name']), \
                ('fullname', row['fullname']), \
                ('emails', row['emails']))))


    for i in data:
        if i.get('name', None) == name:
            if i['emails']:
                return str(i['emails'])
            else:
                raise EmailNotFound('You need to fill out all the emails of the \
                        issue commentors')

