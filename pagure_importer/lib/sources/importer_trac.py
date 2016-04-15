from xmlrpclib import ServerProxy
import pagure_importer
import pagure_importer.lib
from pagure_importer.lib import models
from datetime import datetime

class TracImporter():
    '''Pagure importer for trac instance'''

    def __init__(self, trac_project_url):
        self.trac = ServerProxy(trac_project_url + '/rpc')

    def import_issues(self, repo_path, repo_folder, trac_query='report=9&order=id'):
        '''Import issues from trac instance using xmlrpc API'''
        tickets_list = []
        tickets_id = self.trac.ticket.query(trac_query)

        for ticket_id in tickets_id:

            trac_ticket = self.trac.ticket.get(ticket_id)[3]
            pagure_issue_title = trac_ticket['summary']
            pagure_issue_content = trac_ticket['description']

            if pagure_issue_content == '':
                pagure_issue_content = '#No Description Provided'

            if trac_ticket['status'] != 'closed':
                pagure_issue_status = 'Open'
            else:
                pagure_issue_status = 'Fixed'

            pagure_issue_created_at = datetime.strptime(self.trac.ticket.get(ticket_id)[1].value, "%Y%m%dT%H:%M:%S")

            pagure_issue_assignee = trac_ticket['owner']

            # if github_issue.labels:
            #    pagure_issue_tags = [i.name for i in github_issue.labels]
            #  else:
            pagure_issue_tags = []

            pagure_issue_depends = []
            pagure_issue_blocks = []
            pagure_issue_is_private = False

            pagure_issue_user = models.User(
                name=trac_ticket['reporter'],
                fullname=None,
                emails=[None])

            pagure_issue = models.Issue(
                id=None,
                title=pagure_issue_title,
                content=pagure_issue_content,
                status=pagure_issue_status,
                date_created=pagure_issue_created_at,
                user=pagure_issue_user.to_json(),
                private=pagure_issue_is_private,
                tags=pagure_issue_tags,
                depends=pagure_issue_depends,
                blocks=pagure_issue_blocks,
                assignee=pagure_issue_assignee)

            pagure_issue_comments = self.trac.ticket.changeLog(ticket_id)
            comments = []
            for comment in pagure_issue_comments:
                if comment[2] == 'comment' and comment[4] != '':
                    comment_user = comment[1]
                    pagure_issue_comment_user_email = None
                    pagure_issue_comment_body = comment[4]
                    pagure_issue_comment_created_at = datetime.strptime(comment[0].value, "%Y%m%dT%H:%M:%S")
                    pagure_issue_comment_updated_at = None

                    # No idea what to do with this right now
                    # editor: not supported by github api
                    pagure_issue_comment_parent = None
                    pagure_issue_comment_editor = None

                    # comment updated at
                    pagure_issue_comment_edited_on = None

                    # The User who commented
                    pagure_issue_comment_user = models.User(
                        name=comment[1],
                        fullname=None,
                        emails=None)

                    # Object to represent comment on an issue
                    pagure_issue_comment = models.IssueComment(
                        id=None,
                        comment=pagure_issue_comment_body,
                        parent=pagure_issue_comment_parent,
                        date_created=pagure_issue_comment_created_at,
                        user=pagure_issue_comment_user.to_json(),
                        edited_on=pagure_issue_comment_edited_on,
                        editor=pagure_issue_comment_editor)

                    comments.append(pagure_issue_comment.to_json())

                # add all the comments to the issue object
                pagure_issue.comments = comments

                # update the local git repo
            print 'Update repo with issue :' + str(ticket_id)
            pagure_importer.lib.git.update_git(pagure_issue,
                                               repo_path,
                                               repo_folder)
