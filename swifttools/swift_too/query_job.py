from .too_status import Swift_TOO_Status
from .swift_visquery import Swift_VisQuery
from .swift_obsquery import Swift_AFST
from .swift_planquery import Swift_PPST

class QueryJob(Swift_TOO_Status):
    def __init__(self,username=None,shared_secret=None,jobnumber=None):
        '''Class that enables fetching the results of already submitted jobs. Essentially the same as
        Swift_TOO_Status other than if the process has been completed the resultant data will be used
        to create a `Swift_VisQuery`, `Swift_AFST` AKA `Swift_ObsQuery` or `Swift_PPST` AKA 
        `Swift_PlanQuery` class.'''
        # Inherit the Swift_TOO_Status class init
        Swift_TOO_Status.__init__(self)
        self.api_name = 'Swift_TOO_Status' # This is really just a Swift_TOO_Status request with a twist

        # Parameter passed as arguments
        self.username = username
        self.shared_secret=shared_secret
        self.jobnumber=jobnumber
        
        # Set this so that the result of the job is returned rather than just the status
        self.fetchresult = True
        self.result = None 
        # These are the kinds of results that can be returned
        self.subclasses =[Swift_TOO_Status,Swift_VisQuery,Swift_AFST,Swift_PPST]
        # Add fetchresult and result to the required parameters list
        self.rows += ['fetchresult','result']
        # Submit if all parameters given
        if self.validate():
            self.submit()
    
    def __str__(self):
        values = [f"{row}={getattr(self,row)}" for row in self.rows if row != "fetchresult"]
        return f"job type={type(self.result)} {[val for val in values if 'None' not in val]}"
