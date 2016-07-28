from xmlrpclib import ServerProxy
from datetime import datetime
from pagure_importer.utils.git import update_git
from pagure_importer.utils.models import User, Issue, IssueComment


class TracImporter():
    '''Pagure importer for trac instance'''

    def __init__(self, trac_project_url, fasclient=None, tags=False):
        self.trac = ServerProxy(trac_project_url)
        self.fas = fasclient
        self.tags = tags

    def import_issues(self, repo_name, repo_folder,
                      trac_query='max=0&order=id'):
        '''Import issues from trac instance using xmlrpc API'''
        tickets_id = self.trac.ticket.query(trac_query)

        for ticket_id in tickets_id:
            pagure_issue = self.create_issue(ticket_id)
            pagure_issue.comments = []
            pagure_issue_comments = self.trac.ticket.changeLog(ticket_id)
            comments = self.create_comments(pagure_issue_comments)
            # add all the comments to the issue object
            for key in comments:
                if comments[key].attachment:
                    project = repo_name.replace('.git', '')
                    url = '/%s/issue/raw/files/%s' % \
                        (project, pagure_issue.uid+comments[key].attachment)
                    comments[key].comment += '\n[%s](%s)' % (comments[key].attachment, url)
                pagure_issue.comments.append(comments[key].to_json())
            # update the local git repo
            update_git(pagure_issue, repo_name, repo_folder)
            print 'Updated ' + repo_name + ' with issue :' + str(ticket_id) +\
                '/' + str(tickets_id[-1])

    def create_issue(self, ticket_id):

        trac_ticket = self.trac.ticket.get(ticket_id)[3]
        trac_attachments = self.trac.ticket.listAttachments(ticket_id)

        pagure_attachment = {}
        for attachment in trac_attachments:
            filename = attachment[0]
            content = self.trac.ticket.getAttachment(ticket_id, filename)
            pagure_attachment[filename] = content

        pagure_issue_title = trac_ticket['summary']

        pagure_issue_content = trac_ticket['description']
        if pagure_issue_content == '':
            pagure_issue_content = '#No Description Provided'

        pagure_issue_status = self.get_ticket_status(trac_ticket)

        pagure_issue_created_at = datetime.strptime(
            self.trac.ticket.get(ticket_id)[1].value, "%Y%m%dT%H:%M:%S")

        if self.fas:
            pagure_issue_assignee = self.fas.find_fas_user(trac_ticket['owner'])
            pagure_issue_user = self.fas.find_fas_user(trac_ticket['reporter'])
        else:
            pagure_issue_assignee = User(name='', fullname='', emails=[])
            pagure_issue_user = User(name='', fullname='', emails=[])

        pagure_issue_tags = []
        if self.tags:
            pagure_issue_tags = filter(lambda x: x != '', trac_ticket['keywords'].split(' '))

            if trac_ticket['milestone'] != '':
                pagure_issue_tags.append(str(trac_ticket['milestone']))

        pagure_issue_depends = []
        pagure_issue_blocks = []
        pagure_issue_is_private = False

        pagure_issue = Issue(
            id=ticket_id,
            title=pagure_issue_title,
            content=pagure_issue_content,
            status=pagure_issue_status,
            date_created=pagure_issue_created_at,
            user=pagure_issue_user.to_json(),
            private=pagure_issue_is_private,
            attachment=pagure_attachment,
            tags=pagure_issue_tags,
            depends=pagure_issue_depends,
            blocks=pagure_issue_blocks,
            assignee=pagure_issue_assignee.to_json())
        return pagure_issue

    def get_ticket_status(self, trac_ticket):

        if trac_ticket['status'] != 'closed':
            ticket_status = 'Open'
        else:
            ticket_status = 'Fixed'
        return ticket_status

    def create_comments(self, trac_comments):
        comments = {}
        for comment in trac_comments:
            ts = datetime.strptime(comment[0].value, "%Y%m%dT%H:%M:%S")
            if comment[2] == 'comment' and comment[4] != '':
                if ts in comments:
                    attachment = comments[ts]
                else:
                    attachment = []

                pagure_issue_comment_body = comment[4]
                pagure_issue_comment_created_at = ts

                # The User who commented
                if self.fas:
                    pagure_issue_comment_user = self.fas.find_fas_user(comment[1])
                else:
                    pagure_issue_comment_user = User(name='', fullname='', emails=[])

                # Object to represent comment on an issue
                pagure_issue_comment = IssueComment(
                    id=None,
                    comment=pagure_issue_comment_body,
                    date_created=pagure_issue_comment_created_at,
                    attachment=attachment,
                    user=pagure_issue_comment_user.to_json())

                comments[ts] = pagure_issue_comment

            elif comment[2] == 'attachment':
                if ts in comments:
                    comments[ts].attachment.append(comment[4])
                else:
                    comments[ts] = comment[4]
        return comments
