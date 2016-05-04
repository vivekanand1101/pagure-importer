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
    trac_importer = importer_trac.TracImporter(project_url, fasclient)
    trac_importer.import_issues(repo_path=REPO_NAME, repo_folder=REPO_PATH)
