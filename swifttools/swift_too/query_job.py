from .base.status import SwiftTOOStatus
from .swift.calendar import Calendar
from .swift.clock import Clock
from .swift.data import Data
from .swift.guano import GUANO
from .swift.obsquery import AFST
from .swift.planquery import PPST
from .swift.requests import TOORequests
from .swift.saa import SAA
from .swift.uvot import UVOTMode
from .swift.visquery import VisQuery


class QueryJob(SwiftTOOStatus):
    """Class that enables fetching the results of already submitted jobs.
    Essentially the same as TOOStatus other than if the process has
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
        For a TOO request, the TOO ID assigned to a new request
    fetchresult : boolean
        Fetch the result of the query
    result : <varies>
        The completed job object
    """

    # These are the kinds of results that can be returned from a QueryJob
    _subclasses = [
        SwiftTOOStatus,
        VisQuery,
        AFST,
        UVOTMode,
        PPST,
        TOORequests,
        Calendar,
        GUANO,
        Data,
        Clock,
        SAA,
    ]

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
        # Call the TOOStatus constructor with fetchresult=True to that make this a QueryJob
        SwiftTOOStatus.__init__(self, *args, fetchresult=True, **kwargs)

    @property
    def _table(self):
        """Table of request details"""
        _parameters = self._parameters + self._attributes
        table = [
            [row, getattr(self, row)]
            for row in _parameters
            if getattr(self, row) is not None and getattr(self, row) != "" and row != "result"
        ]
        table.append(["result", self.result.__class__.__name__ + " object"])
        return ["Parameter", "Value"], table
