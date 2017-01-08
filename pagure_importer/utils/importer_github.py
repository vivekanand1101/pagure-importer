import click
import os
import shutil
from github import Github

from pagure_importer.utils import (
    models, gh_get_user_email, get_auth_token, issue_to_json
)


class GithubImporter(object):
    ''' Imports from Github using PyGithub and libpagure '''

    def __init__(self, username, password, project, repo_name, repo_folder, nopush):
        ''' Instantiate GithubImporter object '''

        self.username = username
        self.password = password
        self.repo_name = repo_name
        self.repo_folder = repo_folder
        self.clone_repo_location = os.path.join(
            repo_folder, 'clone-' + repo_name)
        self.nopush = nopush
        self.github_project_name = project
        self.github = Github(username, password)

        otp_auth = get_auth_token(self.github)
        self.github = Github(otp_auth)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        ''' Delete the cloned repo where the commits were going '''
        if os.path.exists(self.clone_repo_location):
            if not self.nopush:
                shutil.rmtree(self.clone_repo_location)

    def get_issue_assignee(self, github_issue):
        ''' From the github issue object, return the
        assignee of the issue if any '''

        assignee = None
        if github_issue.assignee is not None:
            assignee = models.User(
                name=github_issue.assignee.login,
                fullname=github_issue.assignee.name,
                emails=[gh_get_user_email(github_issue.assignee.login)]
            )

        if assignee is not None:
            return assignee.to_json()

    def import_issues(self, repo, status='all'):
        ''' Imports the issues on github for the given project
        '''

        repo_issues = repo.get_issues(state=status)
        issues_length = sum(1 for issue in repo_issues)

        for idx, github_issue in enumerate(repo_issues):

            # title of the issue
            pagure_issue_title = github_issue.title

            # body of the issue
            if github_issue.body:
                pagure_issue_content = github_issue.body
            else:
                pagure_issue_content = '#No Description Provided'

            # Some details of a issue
            if github_issue.state != 'closed':
                pagure_issue_status = 'Open'
                close_status = ''
            else:
                pagure_issue_status = 'Closed'
                close_status = 'Fixed'

            pagure_issue_created_at = github_issue.created_at.strftime('%s')

            # Get the assignee of the issue
            pagure_issue_assignee = self.get_issue_assignee(github_issue)

            if github_issue.labels:
                pagure_issue_tags = [i.name for i in github_issue.labels]
            else:
                pagure_issue_tags = []

            pagure_issue_milestone = github_issue.milestone.title \
                if github_issue.milestone else None

            # few things not supported by github
            pagure_issue_depends = []
            pagure_issue_blocks = []
            pagure_issue_is_private = False

            # User who created the issue
            pagure_issue_user = models.User(
                    name=github_issue.user.login,
                    fullname=github_issue.user.name,
                    emails=[github_issue.user.email] if github_issue.user.email
                            else [gh_get_user_email(github_issue.user.login)])

            pagure_issue = models.Issue(
                    id=None,
                    title=pagure_issue_title,
                    content=pagure_issue_content,
                    status=pagure_issue_status,
                    close_status=close_status,
                    date_created=pagure_issue_created_at,
                    user=pagure_issue_user.to_json(),
                    private=pagure_issue_is_private,
                    attachment=None,
                    tags=pagure_issue_tags,
                    depends=pagure_issue_depends,
                    blocks=pagure_issue_blocks,
                    assignee=pagure_issue_assignee,
                    milestone=pagure_issue_milestone)

            # comments on the issue
            comments = []
            for comment in github_issue.get_comments():

                comment_user = comment.user
                pagure_issue_comment_body = comment.body
                pagure_issue_comment_created_at = comment.created_at.strftime('%s')

                # No idea what to do with this right now
                # editor: not supported by github api
                pagure_issue_comment_parent = None
                pagure_issue_comment_editor = None

                # comment updated at
                pagure_issue_comment_edited_on = comment.updated_at.strftime('%s')

                # The User who commented
                pagure_issue_comment_user = models.User(
                        name=comment_user.login,
                        fullname=comment_user.name,
                        emails=[comment_user.email] if comment_user.email
                        else [gh_get_user_email(comment_user.login)])

                # Object to represent comment on an issue
                pagure_issue_comment = models.IssueComment(
                        id=None,
                        comment=pagure_issue_comment_body,
                        parent=pagure_issue_comment_parent,
                        date_created=pagure_issue_comment_created_at,
                        user=pagure_issue_comment_user.to_json(),
                        edited_on=pagure_issue_comment_edited_on,
                        editor=pagure_issue_comment_editor,
                        attachment=None)

                comments.append(pagure_issue_comment.to_json())

            # add all the comments to the issue object
            pagure_issue.comments = comments

            click.echo('Updated %s with issue : %s/%s' % (self.repo_name, idx + 1, issues_length))
            issue_to_json(pagure_issue, self.clone_repo_location)
