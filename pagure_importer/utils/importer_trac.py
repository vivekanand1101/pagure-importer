import sys
import re
import time
import click
import requests
import shutil
import os
from base64 import b64decode
from datetime import datetime
from pagure_importer.utils import (
    get_close_status, is_image, issue_to_json, get_secure_filename)
from pagure_importer.utils.models import User, Issue, IssueComment


def to_timestamp(tm):
    ''' Convert to timestamp which can be jsonified '''

    tm = tm.replace('+00:00', '')
    date = datetime.strptime(tm, '%Y-%m-%dT%H:%M:%S')
    ts = str(time.mktime(date.timetuple()))[:-2]  # Strip the .0
    return ts


class TracImporter(object):
    ''' Pagure importer for trac instance '''

    def __init__(self, project_url, username, password, offset, repo_name,
                 repo_folder, nopush, fasclient=None, tags=False, private=False):
        ''' Instantiate a TracImporter object '''
        self.username = username
        self.password = password
        self.repo_name = repo_name
        self.repo_folder = repo_folder
        self.clone_repo_location = os.path.join(
            repo_folder, 'clone-' + repo_name)
        self.nopush = nopush
        self.url = project_url
        self.fas = fasclient
        self.tags = tags
        self.private = private
        self.offset = offset
        self.somebody = User(name='somebody', fullname='somebody',
                             emails=['some@body.com'])
        self.reqid = 0
        self.custom_fields = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        ''' Delete the cloned repo where the commits were going '''
        if os.path.exists(self.clone_repo_location):
            if not self.nopush:
                shutil.rmtree(self.clone_repo_location)

    def request(self, method, *args):
        ''' Common method for querying trac '''

        self.reqid += 1
        req = {'params': args,
               'method': method,
               'id': self.reqid}
        resp = requests.post(self.url, json=req,
                             auth=(self.username, self.password))
        resp = resp.json()
        if resp['id'] != self.reqid:
            click.echo('ERROR: Invalid response for request! ' +
                       'ID does not match')
            sys.exit(1)
        if resp['error'] is not None:
            # Ignore missing attachment errors
            if 'Attachment ' not in resp['error']['message'] and \
               ' not found' not in resp['error']['message']:
                click.echo("ERROR: Error in response: %s" % resp['error'])
                sys.exit(1)

        return resp['result']

    def get_custom_fields(self):
        ''' Queries the fedorahosted api to get all ticket fields
        and filters all the custom fields, returns
        a list of dicts - dict with keys 'name' and 'key_type' '''

        all_ticket_fields = self.request('ticket.getTicketFields')
        custom_fields = []
        for field in all_ticket_fields:
            if field.get('custom') is True:
                current_field = {}
                current_field['name'] = field['name']
                key_type = 'text'
                if field['type'] == 'checkbox':
                    key_type = 'boolean'
                current_field['key_type'] = key_type
                custom_fields.append(current_field)
        return custom_fields

    def import_issues(self, repo_name, trac_query='max=0&order=id'):
        ''' Queries the trac instance via its jsonrpc API and convert the
        tickets into JSON blob to be imported into pagure's ticket git repo.

        :arg repo_name: the name of the repository
        :arg repo_folder: the folder in which is the repository
        :kwarg trac_query: the query to call trac with in order to retrieve
            all the tickets.
            Defaults to ``max=0&order=id``

        '''

        tickets_id = self.request('ticket.query', trac_query)
        self.custom_fields = self.get_custom_fields()

        for ticket_id in tickets_id:
            pagure_issue = self.create_issue(ticket_id)
            pagure_issue.comments = []
            pagure_issue_comments = self.request('ticket.changeLog', ticket_id)
            comments = self.create_comments(pagure_issue_comments)
            # add all the comments to the issue object
            for key in comments:
                if comments[key].attachment is not None and \
                   any(attachment in comments[key].attachment for attachment in
                       pagure_issue.attachment):

                    for attach_name in comments[key].attachment:
                        filename = get_secure_filename(
                            pagure_issue.attachment[attach_name], attach_name)
                        url = '/%s/issue/raw/files/%s' % (repo_name, filename)
                        if is_image(attach_name):
                            comments[key].comment += ('\n[![%s](%s)](%s)' %
                                                      (attach_name, url, url))
                        else:
                            comments[key].comment += ('\n[%s](%s)' %
                                                      (attach_name, url))
                pagure_issue.comments.append(comments[key].to_json())
            click.echo('Updated ' + repo_name + ' with issue :' +
                       str(ticket_id) + '/' + str(tickets_id[-1]))
            issue_to_json(pagure_issue, self.clone_repo_location)

    def get_custom_fields_of_ticket(self, trac_ticket):
        ''' Given the trac ticket, it will return all the
        custom fields of the ticket, in a form that it can
        be used for pagure Issue '''

        pagure_fields = []
        for field in self.custom_fields:
            if field['name'] in trac_ticket:
                pagure_field = {}
                pagure_field['name'] = field.get('name')
                pagure_field['key_type'] = field.get('key_type')
                pagure_field['value'] = trac_ticket.get(
                                    pagure_field['name'], "").strip()
                if pagure_field['value']:
                    pagure_fields.append(pagure_field)
        return pagure_fields

    def create_issue(self, ticket_id):
        ''' Create Issue object from track ticket '''

        trac_ticket_info = self.request('ticket.get', ticket_id)
        trac_ticket = trac_ticket_info[3]
        trac_attachments = self.request('ticket.listAttachments', ticket_id)

        pagure_attachment = {}
        for attachment in trac_attachments:
            filename = attachment[0]
            attachment_resp = self.request(
                'ticket.getAttachment',
                ticket_id, filename)
            if attachment_resp:
                if is_image(filename):
                    content = b64decode(attachment_resp['__jsonclass__'][1])
                    pagure_attachment[filename] = content
                else:
                    content = b64decode(
                        attachment_resp['__jsonclass__'][1].replace('\n', ''))
                    pagure_attachment[filename] = content

        pagure_custom_fields = self.get_custom_fields_of_ticket(trac_ticket)
        pagure_issue_title = trac_ticket['summary']

        pagure_issue_content = trac_ticket['description']
        if pagure_issue_content == '':
            pagure_issue_content = '#No Description Provided'

        issue_status, close_status = self.get_ticket_status(trac_ticket)

        pagure_issue_created_at = to_timestamp(
            trac_ticket_info[1]['__jsonclass__'][1])

        if self.fas:
            pagure_issue_assignee = self.fas.find_fas_user(
                trac_ticket['owner'])
            pagure_issue_user = self.fas.find_fas_user(trac_ticket['reporter'])
            if not pagure_issue_user.name:
                pagure_issue_user = User(
                    name=trac_ticket['reporter'],
                    fullname=trac_ticket['reporter'],
                    emails=[trac_ticket['reporter'] + '@fedoraproject.org'])
        else:
            pagure_issue_assignee = User(name='', fullname='', emails=[])
            pagure_issue_user = User(
                name=trac_ticket['reporter'],
                fullname=trac_ticket['reporter'],
                emails=[trac_ticket['reporter'] + '@fedoraproject.org'])

        # The milestone of the issue
        pagure_milestone = None
        if 'milestone' in trac_ticket and trac_ticket['milestone'] != '':
            pagure_milestone = trac_ticket['milestone']

        # Issue tags
        pagure_issue_tags = []
        if self.tags:
            pagure_issue_tags = filter(
                lambda x: x != '', trac_ticket['keywords'].split(' '))

        pagure_issue_tags = self.pre_process_tags(pagure_issue_tags)

        pagure_issue_depends = []
        pagure_issue_blocks = []
        if self.private:
            pagure_issue_is_private = True
        else:
            pagure_issue_is_private = False

        pagure_issue = Issue(
            id=ticket_id + self.offset,
            title=pagure_issue_title,
            content=pagure_issue_content,
            status=issue_status,
            close_status=close_status,
            date_created=pagure_issue_created_at,
            user=pagure_issue_user.to_json(),
            private=pagure_issue_is_private,
            attachment=pagure_attachment,
            tags=pagure_issue_tags,
            milestone=pagure_milestone,
            depends=pagure_issue_depends,
            blocks=pagure_issue_blocks,
            assignee=pagure_issue_assignee.to_json(),
            custom_fields=pagure_custom_fields,)
        return pagure_issue

    def pre_process_tags(self, tags):
        ''' Pre process the tags before sending it to pagure '''

        delims_str = ',|/|;|:|-|\+|\*|\'|\"'

        # Remove the delims between the tags and convert all tags to lower case
        pagure_issue_tags = list(set([j for k in [
            re.split(delims_str, i.lower()) for i in tags] for j in k]))

        return pagure_issue_tags

    def get_ticket_status(self, trac_ticket):
        ''' Returns the corresponding status of ticket on pagure '''
        close_status = get_close_status()
        if close_status is not None:
            if trac_ticket['status'] != 'closed':
                return ('Open', '')
            else:
                for status in close_status:
                    if trac_ticket['resolution'] in close_status[status]:
                        return ('Closed', status)
                return ('Closed', 'Fixed')
        else:
            click.echo('ERROR: Close Status not read from config file')
            sys.exit(1)

    def get_comment_user(self, comment):
        ''' Returns the user who commented on the ticket '''

        # The User who commented
        if self.fas and comment[1]:
            pagure_issue_comment_user = self.fas.find_fas_user(comment[1])
            if not pagure_issue_comment_user.name:
                pagure_issue_comment_user = self.somebody
        else:
            pagure_issue_comment_user = self.somebody
        return pagure_issue_comment_user

    def create_comments(self, trac_comments):
        ''' Create IssueComment objects from the trac comments '''

        comments = {}
        for comment in trac_comments:
            ts = to_timestamp(comment[0]['__jsonclass__'][1])

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
                        attachment=[comment[4]],
                        user=pagure_issue_comment_user.to_json())

        return comments
