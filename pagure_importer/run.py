#!/usr/bin/env python

from forms import form_github_issues
from settings import IMPORT_SOURCES, IMPORT_OPTIONS

def github_handler(item):
    if item.lower() == 'issues':
        form_github_issues()
    return

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

    return

if __name__ == '__main__':
    main()
