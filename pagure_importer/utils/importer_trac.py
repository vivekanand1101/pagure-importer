from xmlrpclib import ServerProxy
from pagure_importer.utils.git import update_git
from pagure_importer.utils import trac


class TracImporter():
    '''Pagure importer for trac instance'''

    def __init__(self, trac_project_url, fasclient=None):
        self.tracclient = ServerProxy(trac_project_url)
        self.fasclient = fasclient

    def import_issues(self, repo_name, repo_folder, tags,
                      trac_query='max=0&order=id'):
        '''Import issues from trac instance using xmlrpc API'''
        tickets_id = self.tracclient.ticket.query(trac_query)

        for ticket_id in tickets_id:

            pagure_issue = trac.populate_issue(self.tracclient,
                                               self.fasclient, ticket_id, tags)

            pagure_issue_comments = self.tracclient.ticket.changeLog(ticket_id)
            comments = trac.populate_comments(self.fasclient,
                                              pagure_issue_comments)

            # add all the comments to the issue object
            pagure_issue.comments = comments

            # update the local git repo
            print 'Update ' + repo_name + ' with issue :' + str(ticket_id) + '/' +\
                str(tickets_id[-1])
            update_git(pagure_issue, repo_name, repo_folder)
