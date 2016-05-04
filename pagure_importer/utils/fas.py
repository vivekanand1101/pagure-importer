from fedora.client.fas2 import AccountSystem
from pagure_importer.utils.models import User


class FASclient ():
    def __init__(self, fas_username, fas_password, fas_url):
        self.fasclient = AccountSystem(fas_url, username=fas_username,
                                       password=fas_password)

        anonymous = User(name='', fullname='', emails=[])
        self.fasuser = {'': anonymous}

    def find_fas_user(self, user):

        if user not in self.fasuser.keys():
            person = self.fasclient.person_by_username(user)
            if not person:
                return self.fasuser['']

            self.fasuser[user] = User(name=user,
                                      fullname=person['human_name'],
                                      emails=[person['email']])
        return self.fasuser[user]
