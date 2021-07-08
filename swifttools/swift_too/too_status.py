from .common import TOOAPI_Baseclass


class Swift_TOO_Status(TOOAPI_Baseclass):
    '''Simple class to describe the status of a submitted TOO API request'''
    def __init__(self,username=None,shared_secret=None,jobnumber=None):
        TOOAPI_Baseclass.__init__(self)
        # Required arguments
        self.jobnumber = jobnumber
        self.username = username
        self.shared_secret = shared_secret
        # Returned parameters
        self.status = "Unknown"
        self.timestamp = None
        self.began = None
        self.completed = None
        self.errors = list()
        self.warnings = list()
        self.too_id = None
        # Internal parameters
        self.timeout = 0 # Don't wait for a job to be completed to report it's status
        # These are the parameters that are reported by the class
        self.rows = ['username','status','too_id','jobnumber','errors','warnings','timestamp','began','completed']
        # If all arguments are passed, then submit
        if self.validate():
            self.submit()

    def __eq__(self,value):
        return value == self.status

    def __bool__(self):
        if self.status == 'Accepted':
            return True
        else:
            return False

    def validate(self):
        '''Validate if request meets requirements before submitting'''
        if self.username and self.jobnumber and self.shared_secret:
            return True
        else:
            return False

    def error(self,error):
        '''Add an error to the list of errors'''
        if error not in self.errors:
            self.errors.append(error)
        
    def warning(self,warning):
        '''Add a warning to the list of warnings'''
        if warning not in self.warnings:
            self.warnings.append(warning)

    def clear(self):
        self.__init__()
