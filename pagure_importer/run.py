#!/usr/bin/env python
import getpass
from forms import form_github_issues
from settings import IMPORT_SOURCES, IMPORT_OPTIONS, REPO_NAME, REPO_PATH
import pagure_importer
import pagure_importer.lib
import pagure_importer.lib.sources
from pagure_importer.lib.sources.importer_github import GithubImporter
from pagure_importer.lib.sources.importer_trac import TracImporter
from pagure_importer.lib import generate_json_for_github_contributors, \
    generate_json_for_github_issue_commentors, \
    assemble_github_contributors_commentors


def github_handler(item):
    if item.lower() == 'issues':
        github_username, github_password, github_project_name = form_github_issues()
        gen_json = raw_input('Do you want to generate jsons for project\'s contributers and issue commentors? (y/n): ')
        if gen_json == 'n':
            github_importer = GithubImporter(
                github_username=github_username,
                github_password=github_password,
                github_project_name=github_project_name)
            github_importer.import_issues(repo_path=REPO_NAME, repo_folder=REPO_PATH)
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


def trac_handler(item, fedora=False):
    if item.lower() == 'issues':
        trac_url = raw_input('Enter the trac project url: ')
        trac_importer = TracImporter(trac_url)
        trac_importer.import_issues(repo_path=REPO_NAME, repo_folder=REPO_PATH)


def main():
    source = raw_input('Enter source from where you want to import: ')
    if source.lower() not in IMPORT_SOURCES:
        print 'Source location not supported'
        return

    item = raw_input('Enter the item to be imported: ')
    if item.lower() not in IMPORT_OPTIONS[source]:
        print 'Item import not supported'
        return

    if source.lower() == 'github':
        github_handler(item)
    elif source.lower() == 'fedorahosted':
        trac_handler(item, fedora=True)
    return

if __name__ == '__main__':
    main()
