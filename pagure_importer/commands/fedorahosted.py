import click
import getpass
from pagure_importer.app import app, REPO_NAME, REPO_PATH
from pagure_importer.utils import importer_trac
from pagure_importer.utils.fas import FASclient

@app.command()
@click.argument('project_url')
def fedorahosted(project_url):
    fas_username = raw_input('Enter you FAS Username: ')
    fas_password = getpass.getpass('Enter your FAS password: ')
    fasclient = FASclient(fas_username, fas_password,
                               'https://admin.fedoraproject.org/accounts')

    rpc_login = fas_username + ':' + fas_password + '@'
    url_index = project_url.find('://')
    rpc_url = project_url[:url_index+3] + rpc_login + project_url[url_index+3:]\
        + '/login/xmlrpc'
    trac_importer = importer_trac.TracImporter(rpc_url, fasclient)
    trac_importer.import_issues(repo_path=REPO_NAME, repo_folder=REPO_PATH)
