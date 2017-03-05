import re
import os
import shutil

import click
import requests
from github import Github

from pagure_importer.utils import (
    models, gh_get_user_email, get_auth_token, issue_to_json, get_secure_filename
)


class GithubImporter(object):
    ''' Imports from Github using PyGithub and libpagure '''

    def __init__(self, username, password,
                 project, repo_name, repo_folder, nopush, pagure_project):
        ''' Instantiate GithubImporter object '''

        self.username = username
        self.password = password
        self.repo_name = repo_name
        self.repo_folder = repo_folder
        self.clone_repo_location = os.path.join(
            repo_folder, 'clone-' + repo_name)
        self.nopush = nopush
        self.github_project_name = project
        self.pagure_project = pagure_project
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

    def _get_attachments(self, attach_regex, whole_body,
                         pagure_attachments, is_image=True):
        ''' Get the Attachment '''

        attach_url_list = re.findall(attach_regex, whole_body)
        format_list = []
        for attach_url in attach_url_list:
            attach_name = attach_url.strip().rstrip('/').rsplit('/')[-1]
            format_list.append(attach_name)
            response = requests.get(attach_url)
            if response.status_code == 200:
                pagure_attachments[attach_name] = response.content
                filename = get_secure_filename(
                    pagure_attachments[attach_name], attach_name)
                url = '/%s/issue/raw/files/%s' % (self.pagure_project, filename)
            else:
                url = '#Attachment Unavailable'
            format_list.append(url)

            # the difference is because of md
            if is_image:
                format_list.append(url)
        return (format_list, whole_body, pagure_attachments)

    def _get_image_attachments(self, whole_body, pagure_attachments):
        ''' Get the image attachments from github comment body '''

        # Markdown for image: ![]()
        attach_regex = r'!\[.*\]\((.*)\)'
        format_list, whole_body, pagure_attachments = self._get_attachments(
            attach_regex=attach_regex,
            whole_body=whole_body,
            pagure_attachments=pagure_attachments,
        )

        unformatted_body = re.sub(attach_regex, '\n[![%s](%s)](%s)', whole_body)
        whole_body = unformatted_body % tuple(format_list)
        return whole_body, pagure_attachments

    def _get_file_attachments(self, whole_body, pagure_attachments):
        ''' Get the file from github comment body '''

        # Markdown for a non-image file is same as any normal link ([]())
        # in markdown. To differentiate i have used the url at which
        # github stores these attachments:
        # https://github.com/<username>/<project>/<files>/<someid>/<filename>
        attach_regex = r'\[.*\]\((.*%s\/.*files.*)\)' \
            % self.github_project_name.replace('/', r'\/')
        format_list, whole_body, pagure_attachments = self._get_attachments(
            attach_regex=attach_regex,
            whole_body=whole_body,
            pagure_attachments=pagure_attachments,
            is_image=False,
        )
        unformatted_body = re.sub(attach_regex, '\n[%s](%s)', whole_body)
        whole_body = unformatted_body % tuple(format_list)
        return whole_body, pagure_attachments

    def get_comment_body(self, comment, pagure_attachments):
        ''' Return the comment body. Check if there is
        an attachment, if so return the attachment as well '''

        whole_body = comment.body
        whole_body, pagure_attachments = self._get_file_attachments(
                            whole_body=whole_body,
                            pagure_attachments=pagure_attachments
        )
        whole_body, pagure_attachments = self._get_image_attachments(
                            whole_body=whole_body,
                            pagure_attachments=pagure_attachments
        )

        return whole_body, pagure_attachments

    def import_issues(self, repo, status='all'):
        ''' Imports the issues on github for the given project '''

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

            # only github comments can have attachments
            pagure_attachments = {}
            for comment in github_issue.get_comments():
                comment_attachments = {}
                comment_user = comment.user
                pagure_issue_comment_body, comment_attachments = self.get_comment_body(
                                        comment, comment_attachments)
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

                pagure_attachments.update(comment_attachments)
                comments.append(pagure_issue_comment.to_json())

            # add all the comments to the issue object and the attachments
            pagure_issue.comments = comments
            pagure_issue.attachment = pagure_attachments

            click.echo('Updated %s with issue : %s/%s' % (self.repo_name, idx + 1, issues_length))
            issue_to_json(pagure_issue, self.clone_repo_location)
