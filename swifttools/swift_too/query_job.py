from .swift_clock import Swift_Clock
from .swift_saa import Swift_SAA
from .swift_guano import Swift_GUANO
from .swift_calendar import Swift_Calendar
from .too_status import Swift_TOO_Status
from .swift_visquery import Swift_VisQuery
from .swift_obsquery import Swift_AFST
from .swift_planquery import Swift_PPST
from .swift_requests import Swift_TOO_Requests
from .swift_data import Swift_Data
from .swift_uvot import UVOT_mode


class QueryJob(Swift_TOO_Status):
    """Class that enables fetching the results of already submitted jobs.
    Essentially the same as Swift_TOO_Status other than if the process has
    been completed the result of the job will be attached as `result`.

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
        For a Swift_TOO request, the TOO ID assigned to a new request
    fetchresult : boolean
        Fetch the result of the query
    result : <varies>
        The completed job object
    """

    # These are the kinds of results that can be returned from a QueryJob
    _subclasses = [
        Swift_TOO_Status,
        Swift_VisQuery,
        Swift_AFST,
        UVOT_mode,
        Swift_PPST,
        Swift_TOO_Requests,
        Swift_Calendar,
        Swift_GUANO,
        Swift_Data,
        Swift_Clock,
        Swift_SAA,
    ]
    # API name
    # This is really just a Swift_TOO_Status request with a twist
    api_name = "Swift_TOO_Status"

    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        jobnumber : int
            TOO API job number
        username : str
            username for TOO API (default 'anonymous')
        shared_secret : str
            shared secret for TOO API (default 'anonymous')
        """
        # Call the Swift_TOO_Status constructor with fetchresult=True to that make this a QueryJob
        Swift_TOO_Status.__init__(
            self, *args, fetchresult=True, api_name=self.api_name, **kwargs
        )

    @property
    def _table(self):
        """Table of request details"""
        _parameters = self._parameters + self._attributes
        table = [
            [row, getattr(self, row)]
            for row in _parameters
            if getattr(self, row) is not None
            and getattr(self, row) != ""
            and row != "result"
        ]
        table.append(["result", self.result.__class__.__name__ + " object"])
        return ["Parameter", "Value"], table
