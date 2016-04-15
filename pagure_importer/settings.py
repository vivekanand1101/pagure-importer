import os

IMPORT_SOURCES = ['github', 'fedorahosted']
IMPORT_OPTIONS = {'github': ['issues'], 'fedorahosted': ['issues']}

REPO_NAME = os.environ.get('REPO_NAME', None) #this has to be a bare repo
REPO_PATH = os.environ.get('REPO_PATH', None) #the parent of the git directory
