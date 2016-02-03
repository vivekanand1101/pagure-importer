import libpagure
from libpagure.libpagure import Pagure
from github import Github

from exceptions import GithubBadCredentials, GithubRepoNotFound


class GithubImporter():
    ''' Imports from Github using PyGithub and libpagure '''


    def __init__(
            self,
            github_username,
            github_password,
            github_project_name,
            pagure_api_key,
            pagure_project_name,
            pagure_username=None,
            instance_url='https://pagure.io'):

        self.github_username = github_username
        self.github_password = github_password
        self.github_project_name = github_project_name
        self.pagure_project_name = pagure_project_name
        self.github = Github(github_username, github_password)
        self.pagure = Pagure(pagure_api_key, pagure_project_name,
                                pagure_username, instance_url)


    def _get_available_issue_id(self):
        ''' Private method which checks the id
        which would be available for the new issue
        '''
        issues = self.pagure.list_issues()
        try:
            return max([int(issue['id']) for issue in issues]) + 1
        except ValueError:
            return 1


    def _get_repo(self, github_user):
        ''' Private method to get the repo object
        using the given github project name
        '''
        repos = github_user.get_repos()
        for repo in repos:
            if repo.name == self.github_project_name:
                return repo
        raise GithubRepoNotFound(
                'No user repository with given github project name found')


    def import_issues(self, status='all'):
        ''' Imports the issues on github for
        the given project
        '''
        github_user = None
        try:
            github_user = self.github.get_user(self.github_username)
        except:
            raise GithubBadCredentials(
                    'Given github credentials are not correct')

        repo = self._get_repo(github_user)
        for github_issue in repo.get_issues(state=status):
            pagure_issue_title = github_issue.title
            if github_issue.body:
                pagure_issue_content = github_issue.body
            else:
                pagure_issue_content = '#No Description Provided'

            issue_id = self._get_available_issue_id()
            self.pagure.create_issue(
                    pagure_issue_title, pagure_issue_content)

            #comments on the issue
            for comment in github_issue.get_comments():
                self.pagure.comment_issue(issue_id, str(comment.body))

            #change status of the issue if closed
            if github_issue.state.lower() == 'closed':
                self.pagure.change_issue_status(issue_id, 'Fixed')

