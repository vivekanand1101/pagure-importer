from fedora.client.fas2 import AccountSystem
from pagure_importer.utils.models import User


class FASclient ():
    ''' Creates a FAS User object based on the credentials given '''

    def __init__(self, fas_username, fas_password, fas_url):
        ''' Instantiate a FASclient object '''

        self.fasclient = AccountSystem(fas_url, username=fas_username,
                                       password=fas_password)

        anonymous = User(name='', fullname='', emails=[])
        self.fasuser = {'': anonymous}

    def find_fas_user(self, user):
        ''' Queries FAS and returns the FAS user '''

        if user not in self.fasuser.keys():
            person = self.fasclient.person_by_username(user)
            if not person:
                return self.fasuser['']

            self.fasuser[user] = User(name=user,
                                      fullname=person['human_name'],
                                      emails=[person['email']])
        return self.fasuser[user]
