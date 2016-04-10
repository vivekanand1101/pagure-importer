# pagure-importer
CLI tool for importing issues etc. from different sources like github to pagure

## Installation
1. Install it using ```pip``` . ```pip install pagure_importer```

## How to run
0. Clone the issue tracker for issues from pagure. Use: ```git clone --bare```
and set the env variables: 'REPO_NAME' and 'REPO_PATH'
ex: REPO_NAME='abc.git'; REPO_PATH='/home/vivek/'
1. Activate the pagure tickets hook from project settings.
2. Execute ```pgimport```
3. Just answer what is asked. Check below instructions for particular source
4. The script will make commits in your cloned bare repo: push the changes back to pagure.

### Present options for sources: github
### Present options for items: issues

### Tools used:
1. [PyGithub](https://github.com/PyGithub/PyGithub) - a python library for [github](https://github.com/) api.


## How it works: Github Issues
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

3. The above step will create 3 different json files: ```contributors.json```
```issue_commentors.json``` and ```assembled_commentors.json```. The last file
is where all the edit has to go. All the missing entries in the assembled
commentors file has to be filled for the running of the script.

4. Run the script again, filling the same details but answer 'n' when asked for
whether you want to create the json files. In this step, your local issues git
repo gets updated with all the issues from github issue tracker.

5. Now push the local git repo changes to the remote repo on pagure. It will
update the db and if the user is not found, it will create them from the
details given.
