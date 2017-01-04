''' Code taken from https://pagure.io/pagure/blob/master/f/pagure/lib/git.py
    by pingou@pingoured.fr

    Modified by Clement Verna <cverna@tutanota.com> to add attachment support
'''

import shutil
import os

import pygit2


def clone_repo(repo_name, repo_folder):
    ''' Clone the original repo where the commits will be made
    before pushing back '''

    if not repo_folder:
        return

    # Get the fork
    repopath = os.path.join(repo_folder, repo_name)
    # Clone the repo into a temp folder
    newpath = os.path.join(repo_folder, 'clone-' + repo_name)
    new_repo = pygit2.clone_repository(repopath, newpath)
    return (newpath, new_repo)


def push_repo(new_repo):
    ''' Push the changes to the originally cloned repo from pagure '''

    # Push to origin
    ori_remote = new_repo.remotes[0]
    master_ref = new_repo.lookup_reference('HEAD').resolve()
    refname = '%s:%s' % (master_ref.name, master_ref.name)

    ori_remote.push([refname])


def update_git(new_repo, commit_message):
    """ Update the given issue in its git.
    This method forks the provided repo, add/edit the issue whose file name
    is defined by the uid field of the issue and if there are additions/
    changes commit them and push them back to the original repo.
    """

    # Get the current index
    index = new_repo.index
    index.add_all()

    # See if there is a parent to this commit
    parent = None
    try:
        parent = new_repo.head.get_object().oid
    except pygit2.GitError:
        pass

    parents = []
    if parent:
        parents.append(parent)

    # Author/commiter will always be this one
    author = pygit2.Signature(name='pagure', email='pagure')

    # Actually commit
    new_repo.create_commit(
        'refs/heads/master',
        author,
        author,
        commit_message,
        new_repo.index.write_tree(),
        parents)
    index.write()

    return new_repo
