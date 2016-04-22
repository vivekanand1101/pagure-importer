from pagure_importer.lib.models import IssueComment, Issue
from datetime import datetime


def get_ticket_tags(trac_ticket):
    return []


def get_ticket_status(trac_ticket):
    ''' Converts Trac ticket status
        to Pagure issue status'''

    if trac_ticket['status'] != 'closed':
        ticket_status = 'Open'
    else:
        ticket_status = 'Fixed'
    return ticket_status


def populate_comments(fasclient, trac_comments):
    comments = []
    for comment in trac_comments:
        if comment[2] == 'comment' and comment[4] != '':
            comment_user = comment[1]
            pagure_issue_comment_user_email = None
            pagure_issue_comment_body = comment[4]
            pagure_issue_comment_created_at = datetime.strptime(
                comment[0].value, "%Y%m%dT%H:%M:%S")
            pagure_issue_comment_updated_at = None

            # No idea what to do with this right now
            # editor: not supported by github api
            pagure_issue_comment_parent = None
            pagure_issue_comment_editor = None

            # comment updated at
            pagure_issue_comment_edited_on = None

            # The User who commented
            pagure_issue_comment_user = fasclient.find_fas_user(comment[1])

            # Object to represent comment on an issue
            pagure_issue_comment = IssueComment(
                id=None,
                comment=pagure_issue_comment_body,
                parent=pagure_issue_comment_parent,
                date_created=pagure_issue_comment_created_at,
                user=pagure_issue_comment_user.to_json(),
                edited_on=pagure_issue_comment_edited_on,
                editor=pagure_issue_comment_editor)

            comments.append(pagure_issue_comment.to_json())
    return comments


def populate_issue(trac, fasclient, ticket_id):
    trac_ticket = trac.ticket.get(ticket_id)[3]
    pagure_issue_title = trac_ticket['summary']
    pagure_issue_content = trac_ticket['description']

    if pagure_issue_content == '':
        pagure_issue_content = '#No Description Provided'

    pagure_issue_status = get_ticket_status(trac_ticket)

    pagure_issue_created_at = datetime.strptime(
        trac.ticket.get(ticket_id)[1].value, "%Y%m%dT%H:%M:%S")

    pagure_issue_assignee = fasclient.find_fas_user(trac_ticket['owner'])

    pagure_issue_tags = get_ticket_tags(trac_ticket)

    pagure_issue_depends = []
    pagure_issue_blocks = []
    pagure_issue_is_private = False

    pagure_issue_user = fasclient.find_fas_user(trac_ticket['reporter'])
    pagure_issue = Issue(
        id=ticket_id,
        title=pagure_issue_title,
        content=pagure_issue_content,
        status=pagure_issue_status,
        date_created=pagure_issue_created_at,
        user=pagure_issue_user.to_json(),
        private=pagure_issue_is_private,
        tags=pagure_issue_tags,
        depends=pagure_issue_depends,
        blocks=pagure_issue_blocks,
        assignee=pagure_issue_assignee.to_json())
    return pagure_issue
