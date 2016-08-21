import requests
from datetime import datetime
from pagure_importer.utils.git import update_git, get_secure_filename
from pagure_importer.utils.models import User, Issue, IssueComment


class TracImporter():
    '''Pagure importer for trac instance'''

    def __init__(self, project_url, username, password, fasclient=None, tags=False):
        self.url = project_url
        self.username = username
        self.password = password
        self.fas = fasclient
        self.tags = tags
        self.somebody = User(name='somebody', fullname='somebody', emails=['some@body.com'])
        self.reqid = 0

    def request(self, method, *args):
        self.reqid += 1
        req = {'params': args,
               'method': method,
               'id': self.reqid}
        resp = requests.post(self.url, json=req, auth=(self.username, self.password))
        resp = resp.json()
        if resp['id'] != self.reqid:
            print('ERROR: Invalid response for request! ID does not match')
            sys.exit(1)
        if resp['error'] != None:
            print("ERROR: Error in response: %s" % resp['error'])
            sys.exit(1)

        return resp['result']

    def import_issues(self, repo_name, repo_folder,
                      trac_query='max=0&order=id'):
        '''Import issues from trac instance using xmlrpc API'''
        tickets_id = self.request('ticket.query', trac_query)

        for ticket_id in tickets_id:
            pagure_issue = self.create_issue(ticket_id)
            pagure_issue.comments = []
            pagure_issue_comments = self.trac.ticket.changeLog(ticket_id)
            comments = self.create_comments(pagure_issue_comments)
            # add all the comments to the issue object
            for key in comments:
                if comments[key].attachment:
                    attach_name = comments[key].attachment
                    project = repo_name.replace('.git', '')
                    filename = get_secure_filename(pagure_issue.attachment[attach_name], attach_name)
                    url = '/%s/issue/raw/files/%s' % (project, filename)
                    comments[key].comment += '\n[%s](%s)' % (attach_name, url)
                pagure_issue.comments.append(comments[key].to_json())
            # update the local git repo
            update_git(pagure_issue, repo_name, repo_folder)
            print 'Updated ' + repo_name + ' with issue :' + str(ticket_id) +\
                '/' + str(tickets_id[-1])

    def create_issue(self, ticket_id):

        trac_ticket = self.request('ticket.get', ticket_id)[3]
        trac_attachments = self.request('ticket.listAttachments', ticket_id)

        pagure_attachment = {}
        for attachment in trac_attachments:
            filename = attachment[0]
            content = self.request('ticket.getAttachment', ticket_id, filename)
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

    def get_comment_user(self, comment):
        # The User who commented
        if self.fas:
            pagure_issue_comment_user = self.fas.find_fas_user(comment[1])
            if not pagure_issue_comment_user.name:
                pagure_issue_comment_user = self.somebody
        else:
            pagure_issue_comment_user = self.somebody
        return pagure_issue_comment_user

    def create_comments(self, trac_comments):
        comments = {}
        for comment in trac_comments:
            ts = datetime.strptime(comment[0].value, "%Y%m%dT%H:%M:%S")

            if comment[2] == 'comment' and comment[4] != '':
                if ts in comments:
                    attachment = comments[ts].attachment
                else:
                    attachment = []

                pagure_issue_comment_body = comment[4]
                pagure_issue_comment_created_at = ts

                pagure_issue_comment_user = self.get_comment_user(comment)
                # Object to represent comment on an issue
                comments[ts] = IssueComment(
                    id=None,
                    comment=pagure_issue_comment_body,
                    date_created=pagure_issue_comment_created_at,
                    attachment=attachment,
                    user=pagure_issue_comment_user.to_json())

            elif comment[2] == 'attachment':
                if ts in comments:
                    comments[ts].attachment.append(comment[4])
                else:
                    pagure_issue_comment_user = self.get_comment_user(comment)
                    comments[ts] = IssueComment(
                        id=None,
                        comment='attachment',
                        date_created=ts,
                        attachment=comment[4],
                        user=pagure_issue_comment_user.to_json())

        return comments
