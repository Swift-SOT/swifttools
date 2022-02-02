from .common import TOOAPI_Baseclass, TOOAPI_SkyCoord
from .too_status import Swift_TOO_Status


class Swift_Resolve(TOOAPI_Baseclass, TOOAPI_SkyCoord):
    '''Swift_Resolve class

    Performs name resolution using Simbad, TNS or MARS. Simply give the name of
    the source, and it will return `ra` and `dec` in decimal degrees, or a
    astropy SkyCoord (`skycoord`).

    Attributes
    ----------
    name : str
        name of the object to have coordinates resolved.
    username: str
        Swift TOO API username (default 'anonymous')
    shared_secret: str
        TOO API shared secret (default 'anonymous')
    ra : float
        Right Ascension of resolved target in J2000 (decimal degrees)
    dec : float
        Declination of resolved target in J2000 (decimal degrees)
    resolver : str
        Name of name resolving service used
    skycoord : SkyCoord
        SkyCoord version of RA/Dec if astropy is installed
    status : str
        status of API request
    '''
    # API input and return values definition
    rows = ['username', 'name']
    extrarows = ['ra', 'dec', 'resolver', 'status']
    # Other API classes that may be used by this class
    subclasses = [Swift_TOO_Status]
    # API name
    api_name = 'Swift_Resolve'

    def __init__(self, *args, **kwargs):
        '''
        Parameters
        ----------
        name : str
            name of the object to have coordinates resolved.
        username: str
            Swift TOO API username (default 'anonymous')
        shared_secret: str
            TOO API shared secret (default 'anonymous')
        '''
        # Input parameters
        self.name = None
        self.username = 'anonymous'
        # Returned parameters
        self.ra = None
        self.dec = None
        self.resolver = None
        # Initiate status class
        self.status = Swift_TOO_Status()
        # Parse argument keywords
        self._parseargs(*args, **kwargs)

        # If the required parameters are given as arguments, submit the job
        if self.validate():
            self.submit()

    def validate(self):
        '''Local validation that TOO_API object is ready for submission'''
        if self.name is not None and self.shared_secret is not None:
            return True
        else:
            return False

    @property
    def _table(self):
        '''Displays values in class as a table'''
        if self.ra is not None:
            header = ['Name', 'RA (J2000)', 'Dec (J2000)', 'Resolver']
            table = [[self.name, f"{self.ra:.5f}",
                      f"{self.dec:.5f}", self.resolver]]
            return header, table
        else:
            return [], []


class TOOAPI_AutoResolve:
    '''Mixin to automatically any given `name` into RA/Dec coordinates using
    `Swift_Resolve`'''

    _name = None
    resolve = None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, sourcename):
        '''If you set a name, use `Swift_Resolve` to retrieve it's `ra` and `dec`.'''
        if self._name != sourcename:
            self._name = sourcename
            self.resolve = Swift_Resolve(name=sourcename)
            if self.resolve.ra is not None:
                self.ra = self.resolve.ra
                self.dec = self.resolve.dec
            else:
                self.status.error('Could not resolve name.')


# Shorthand alias for class
Resolve = Swift_Resolve