from .api_common import TOOAPI_Baseclass


class Swift_TOO_Status(TOOAPI_Baseclass):
    """Simple class to describe the status of a submitted TOO API request

    Attributes
    ----------
    jobnumber : int
        TOO API job number
    username : str
        username for TOO API (default 'anonymous')
    shared_secret : str
        shared secret for TOO API (default 'anonymous')
    status : str
        status of API request
    timestamp : datetime
        time request was submitted
    began : datetime
        time request began processing
    completed : datetime
        time request finished processing
    errors : list
        list of error strings assoicated with the request
    warnings : list
        list of warning strings associated with the request
    too_id : list
        For a TOO request, the TOO ID assigned to a new request
    """

    # Core API definitions
    _parameters = ["username", "jobnumber", "too_id", "fetchresult"]
    _attributes = [
        "status",
        "errors",
        "warnings",
        "timestamp",
        "began",
        "completed",
        "result",
    ]
    _local = ["api_name", "shared_secret"]
    api_name = "Swift_TOO_Status"

    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        username : str
            username for TOO API (default 'anonymous')
        shared_secret : str
            shared secret for TOO API (default 'anonymous')
        jobnumber : int
            TOO API job number
        """
        # Required arguments
        self.jobnumber = None
        self.username = "anonymous"
        # Optional arguments
        self.fetchresult = None  # This is only to be used with QueryJob

        # Returned parameters
        self.status = "Unknown"
        self.timestamp = None
        self.began = None
        self.completed = None
        self.errors = list()
        self.warnings = list()
        self.too_id = None
        # Result of QueryJob
        self.result = None

        # Parse argument keywords
        self._parseargs(*args, **kwargs)

        # If all arguments are passed, then submit
        if self.validate():
            self.submit()

    def __eq__(self, value):
        return value == self.status

    def __bool__(self):
        if self.status == "Accepted":
            return True
        else:
            return False

    def validate(self):
        """Validate API submission before submit

        Returns
        -------
        bool
            Was validation successful?
        """
        if self.username and self.jobnumber and self.shared_secret:
            return True
        else:
            return False

    def error(self, error):
        """Add an error to the list of errors"""
        if error not in self.errors:
            self.errors.append(error)

    def warning(self, warning):
        """Add a warning to the list of warnings"""
        if warning not in self.warnings:
            self.warnings.append(warning)

    def clear(self):
        """Reset status"""
        self.__init__()


# Aliases for better PEP8 compliance, and future API updates
Swift_TOOStatus = Swift_TOO_Status
TOOStatus = Swift_TOOStatus
