class GithubBadCredentials(Exception):
    ''' Raised when username/password for github is wrong '''
    def __init__(self, msg):
        self.msg = msg

class GithubRepoNotFound(Exception):
    ''' Raised when the repo is not found for the user '''
    def __init__(self, msg):
        self.msg = msg
