import os

IMPORT_SOURCES = ['github']
IMPORT_OPTIONS = {'github': ['issues']}

REPO_NAME = os.environ.get('REPO_NAME', None) #this has to be a bare repo
REPO_PATH = os.environ.get('REPO_PATH', None) #the parent of the git directory
