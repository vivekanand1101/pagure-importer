from github import Github

from pagure_importer.utils import (
    models, github_get_commentor_email, get_auth_token)
from pagure_importer.utils.git import (
    clone_repo, push_delete_repo, update_git)
from pagure_importer.utils.exceptions import (
    GithubRepoNotFound
)


class GithubImporter():
    ''' Imports from Github using PyGithub and libpagure '''

    def __init__(self, username, password, project):
        ''' Instantiate GithubImporter object '''

        self.github_username = username
        self.github_password = password
        self.github_project_name = project
        self.github = Github(username, password)

        otp_auth = get_auth_token(self.github)
        self.github = Github(otp_auth)

    def import_issues(self, repo_path, repo_folder, status='all'):
        ''' Imports the issues on github for
        the given project
        '''
        repo = self.github.get_repo(self.github_project_name)
        try:
            repo_name = repo.name
        except:
            raise GithubRepoNotFound(
                    'Repo not found, project name wrong')
        newpath, new_repo = clone_repo(repo_path, repo_folder)
        for github_issue in repo.get_issues(state=status):

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
                close_status=''
            else:
                pagure_issue_status = 'Closed'
                close_status = 'Fixed'

            pagure_issue_created_at = github_issue.created_at.strftime('%s')
            # Not sure how to deal with this atm
            pagure_issue_assignee = None

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
                            else [github_get_commentor_email(github_issue.user.login)])

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
                        else [github_get_commentor_email(comment_user.login)])

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

            # update the local git repo
            new_repo = update_git(pagure_issue, newpath, new_repo)
        push_delete_repo(newpath, new_repo)
