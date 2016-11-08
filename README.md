# pagure-importer
CLI tool for importing issues etc. from different sources like github to pagure

## Installation
---

#### In a Virtual Environment
*  Install it using ```pip``` . ```pip install pagure_importer```

#### Using COPR package
*  Install it using [copr](https://copr.fedorainfracloud.org/coprs/cverna/pagure-importer/).
```
    $ sudo dnf copr enable cverna/pagure-importer
    $ sudo dnf install python3-pgimport
```

#### Using Docker
* Build and run a container using the Dockerfile in this repository
```
    $ docker build -t pgimport .
    $ docker run -t -i -v ~/.ssh/:/root/.ssh/:Z /bin/bash
```
* Inside the container you can use the pgimport command.

#### Running the tests

     $ python -m unittest discover tests

## How to run
---
0. Clone the issue tracker for issues from pagure. Use: ```pgimport clone  ssh://git@pagure.io/tickets/foobar.git```
1. Activate the pagure tickets hook from project settings. This is necessary step to also get pagure database updated for tickets repository changes.
2. Deactivate the pagure Fedmsg hook from project settings. This will avoid the issues import to spam the fedmsg bus. The Hook can be reactivated  once the import has completed.
3. Execute ```pgimport```. See Usage section
4. Just answer what is asked. Check below instructions for particular source
5. The script will make commits in your cloned repo: push the changes back to pagure. Use : ```pgimport push foobar.git```

## Custom Close Status
---
pagure-importer creates a configuration under the home directory of the user $HOME/.pgimport. This configuration file contains the default close status.
If this file is not present run the following command.
    ```$ pgimport mkconfig```
To add some new close status just edit the config file as follow. Where ```Foo``` is the pagure custom status and ```bar``` is the trac resolution status

    [close_status]
    Duplicate = ['duplicate']
    Insufficient data = ['insufficient_info']
    Invalid = ['invalid', 'wontfix', 'worksforme']
    Foo = ['bar']

    [github]
    auth_token =


## Usage
---


    $ pgimport --help
    Usage: pgimport [OPTIONS] COMMAND [ARGS]...

    Options:
      --help  Show this message and exit.

    Commands:
      clone
      fedorahosted
      github
      mkconfig
      push


### Migrate fedorahosted trac tickets to pagure
---
1) The clone command can be used to clone the newly created pagure ticket repository:

    $ pgimport clone ssh://git@pagure.io/tickets/foobar.git

   This will clone the pagure foobar repository into the default set /tmp directory as /tmp/foobar.git

2) The fedorahosted command can be used to import issues from a fedorahosted project to pagure

    $ pgimport fedorahosted --help
        Usage: pgimport fedorahosted [OPTIONS] PROJECT_URL

        Options:
        --tags  Import pagure tags as well.
        --private By default make all issues private.
        --username TEXT FAS username
        --password TEXT FAS password
        --offset INTEGER Number of issue in pagure before import
        --help  Show this message and exit.
        --nopush Do not push the result of pagure-importer back


    $ pgimport fedorahosted https://fedorahosted.org/foobar --tags

   This command will import all the tickets information with all tags to /tmp/foobar.git repository

    $ pgimport fedorahosted https://fedorahosted.org/foobar --private

   This command will import all the fedorahosted tickets as private tickets in pagure

    $ pgimport fedorahosted https://fedorahosted.org/foobar --offset 10

   This command will import all the fedorahosted tickets starting using their
   former trac ID + the offset number 10 in this example. This is usefull for project
   which already have issues in pagure before import.

    $ pgimport fedorahosted https://fedorahosted.org/foobar --username foo --password bar

   This command will run the import using the username and password provided in the command
   line without prompting the user. This is usefull to use pgimport in a script.

    $ pgimport fedorahosted https://fedorahosted.org/foobar --nopush

   This command will not push the temporary cloned repository where the importer creates the json
   representation of the issues to import. This can be used to process the issues using the json files
   before running the import.
   Default location of the cloned repository is under /tmp/clone-foobar.git

3) The push command can be used to push a clone pagure ticket repo back to pagure.

    $ pgimport push foobar.git

4) The mkconfig command will create a default config `.pgimport` file under the user $HOME directory.

    $ pgimport mkconfig


### Migrate github issues to pagure
---
1)  The clone command can be used to clone the newly created pagure ticket repository:

     $ pgimport clone ssh://git@pagure.io/tickets/foobar.git

   This will clone the pagure foobar repository into the default set /tmp directory as /tmp/foobar.git

2) The github command can be used to import issues from a github project to pagure

    $ pgimport github

   This will ask few questions, just answer them and issues will be imported to /tmp/foobar.git repository.

3) The push command can be used to push a clone pagure ticket repo back to pagure.

    $ pgimport push foobar.git


### Tools used:
---
1. [PyGithub](https://github.com/PyGithub/PyGithub) - a python library for [github](https://github.com/) api.
2. [click](https://github.com/pallets/click) - Python package for creating beautiful command line interfaces
3. [python-fedora](https://fedorahosted.org/python-fedora/) - A collection of python code that allows programs to talk to Fedora Services
4. [pygit2](http://pygit2.org/) - A Python bindings to the libgit2 to interact
   with git from python.


## How it works: Github Issues
---
0. For github issues, there is a bit of pre-processing so, the process is
not very user friendly. The reason behind the pre-processing is that: github
doesn't give away the email ids of issue commentors unless the commentor
is you (if you are logged in) or if the commentor is the issue reporter
himself. So, to overcome this problem, we will be taking email ids from their
commits, if they have contributed to the project but if they haven't, : start
panicking and read below.

1. We will have to run the script two times. The first time, it will
generate a json file containing all the issue commentors with their details,
if the emails are found, no edit for that particular commentor is required.
Otherwise, you will have to manually fill the emails. Fullnames not required.

2. After running the program and answering the 'source' and 'items', you
will be asked a question on whether you want to generate a json file for
contributors and issue commentors. If you are running the script for github
for the first time, the answer is 'y'.

3. The above step will create 3 different files: ```contributors.json```
```issue_users.json``` and ```assembled_users.csv```. The last file
is where all the edit has to go. All the missing entries in the assembled
commentors file has to be filled for the running of the script.

4. Run the script again, filling the same details but answer 'n' when asked for
whether you want to create the json files. In this step, your local issues git
repo gets updated with all the issues from github issue tracker.

5. Now push the local git repo changes to the remote repo on pagure. It will
update the db and if the user is not found, it will create them from the
details given.
