''' Code taken from https://pagure.io/pagure/blob/master/f/pagure/lib/git.py
    by pingou@pingoured.fr

    Modified by Clement Verna <cverna@tutanota.com> to add attachment support
'''

import shutil
import os
import pygit2
import json
import hashlib
import werkzeug


def get_secure_filename(attachment, filename):
    ''' Hashes the file name, same as pagure '''
    filename = '%s-%s' % (hashlib.sha256(attachment).hexdigest(),
                          werkzeug.secure_filename(str(filename)))
    return filename


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


def push_delete_repo(newpath, new_repo):
    ''' Push the changes to the originally cloned repo from pagure and delete
    the cloned repo where the commits were going '''

    # Push to origin
    ori_remote = new_repo.remotes[0]
    master_ref = new_repo.lookup_reference('HEAD').resolve()
    refname = '%s:%s' % (master_ref.name, master_ref.name)

    ori_remote.push([refname])

    # Remove the clone
    shutil.rmtree(newpath)


def update_git(obj, newpath, new_repo):
    """ Update the given issue in its git.
    This method forks the provided repo, add/edit the issue whose file name
    is defined by the uid field of the issue and if there are additions/
    changes commit them and push them back to the original repo.
    """
    file_path = os.path.join(newpath, obj.uid)

    # Get the current index
    index = new_repo.index

    # Are we adding files
    added = False
    if not os.path.exists(file_path):
        added = True

    # If we have attachments
    attachments = obj.attachment
    if attachments:
        if not os.path.exists(os.path.join(newpath, 'files')):
            os.mkdir(os.path.join(newpath, 'files'))

        for key in attachments.keys():
            filename = get_secure_filename(attachments[key], key)
            attach_path = os.path.join(newpath, 'files', filename)
            with open(attach_path, 'w') as stream:
                stream.write(str(attachments[key]))
            index.add('files/' + filename)

    # Write down what changed
    with open(file_path, 'w') as stream:
        stream.write(json.dumps(
            obj.to_json(), sort_keys=True, indent=4,
            separators=(',', ': ')))

    # Retrieve the list of files that changed
    diff = new_repo.diff()
    files = []
    for p in diff:
        if hasattr(p, 'new_file_path'):
            files.append(p.new_file_path)
        elif hasattr(p, 'delta'):
            files.append(p.delta.new_file.path)

    # Add the changes to the index
    if added:
        index.add(obj.uid)
    for filename in files:
        index.add(filename)

    # If not change, return
    if not files and not added:
        shutil.rmtree(newpath)
        return

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
        'Updated %s %s: %s' % (obj.isa, obj.uid, obj.title),
        new_repo.index.write_tree(),
        parents)
    index.write()

    return new_repo
