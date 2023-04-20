from .api_common import TOOAPI_Baseclass, swiftdatetime, convert_to_dt
from .api_status import TOOStatus
from datetime import datetime


class Swift_Clock(TOOAPI_Baseclass):
    """Class to obtain clock corrections, MET values and corrected UTC times for
    Swift. Typical use of the class is to pass a MET value, Swift Time
    (essentially MET in datetime format), or a UTC datetime. The API returns
    back, all three values, corrected for Swift's clock drift and leap seconds.

    Attributes
    ----------
    met : int
        Mission Elapsed Time (seconds). Amount of seconds since 2001-01-01
        00:00:00 UT. Note that MET is measured using Swift's internal clock, and
        are not corrected for clock drift.
    swifttime : datetime
        Spacecraft time converted to datetime units. Note that dates are note
        corrected for leap seconds or clock drift.
    utctime : datetime
        Universal Time value, corrected for Swift's clock drift and leap
        seconds.
    utcf : float
        Univeral Time Correction Factor. The number of seconds to apply to
        correct MET / Spacecraft time into UTC.
    status : TOOStatus
        Status of API request
    username : str (default 'anonymous')
        TOO API username.
    """

    # API details
    api_name = "Swift_Clock"
    # Arguments
    _parameters = ["username", "met", "swifttime", "utctime"]
    # Returned values
    _attributes = ["status", "entries"]
    # Returned classes
    _subclasses = [TOOStatus, swiftdatetime]
    # Local parameters
    _local = ["shared_secret"]

    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        met : int
            Mission Elapsed Time (seconds). Amount of seconds since 2001-01-01
            00:00:00 UT. Note that MET is measured using Swift's internal clock, and
            are not corrected for clock drift.
        swifttime : datetime
            Spacecraft time converted to datetime units. Note that dates are note
            corrected for leap seconds or clock drift.
        utctime : datetime
            Universal Time value, corrected for Swift's clock drift and leap
            seconds.
        username : str (default 'anonymous')
            TOO API username.
        shared_secret : str (default 'anonymous')
            TOO API shared secret
        """
        # attributes
        self._met = None
        self._swifttime = None
        self._utctime = None
        self._utcf = None
        # parse arguments
        self._parseargs(*args, **kwargs)
        self.status = TOOStatus()
        self.entries = None

        # Submit if enough parameters are passed to the constructor
        if self.validate():
            self.submit()
        else:
            self.status.clear()

    @property
    def met(self):
        if self._met is None and self.entries is not None:
            self._met = [e.met for e in self]
            if len(self._met) == 1:
                self._met = self._met[0]
        return self._met

    @met.setter
    def met(self, mettime):
        self._met = mettime

    @property
    def utcf(self):
        if self._utcf is None and self.entries is not None:
            self._utcf = [e.utcf for e in self]
            if len(self._utcf) == 1:
                self._utcf = self._utcf[0]
        return self._utcf

    @utcf.setter
    def utcf(self, utcftime):
        self._utcf = utcftime

    @property
    def utctime(self):
        if self._utctime is None and self.entries is not None:
            self._utctime = [entry.utctime for entry in self.entries]
            if len(self._utctime) == 1:
                self._utctime = self._utctime[0]
        return self._utctime

    @utctime.setter
    def utctime(self, utct):
        if type(utct) == swiftdatetime:
            if utct.utctime is None:
                raise TypeError("swiftdatetime does not have utctime set")
            else:
                self._utctime = utct.utctime
        else:
            self._utctime = self.__todt(utct)

    @property
    def swifttime(self):
        if self._swifttime is None and self.entries is not None:
            self._swifttime = [e.swifttime for e in self]
            if len(self._swifttime) == 1:
                self._swifttime = self._swifttime[0]
        return self._swifttime

    @swifttime.setter
    def swifttime(self, swiftt):
        if type(swiftt) == swiftdatetime:
            if swiftt.swifttime is None:
                raise TypeError("swiftdatetime does not have swifttime set")
            else:
                self._swifttime = swiftt.swifttime
        else:
            self._swifttime = self.__todt(swiftt)
        self._swifttime = self.__todt(swiftt)

    def __todt(self, dt):
        """Simple method to revert a swiftdatetime back to a datetime"""
        if isinstance(dt, (list, tuple)):
            return [convert_to_dt(d) for d in dt]
        else:
            return convert_to_dt(dt)

    def __getitem__(self, index):
        return self.entries[index]

    def __len__(self):
        if self.entries is not None:
            return len(self.entries)
        else:
            return 0

    @property
    def _table(self):
        if len(self) > 0:
            values = [self[i]._table[1][0] for i in range(len(self))]
            header = self[0]._table[0]
        else:
            header, values = [], []
        return header, values

    def validate(self):
        """Validate API submission before submit

        Returns
        -------
        bool
            Was validation successful?
        """
        # Check what the source is, and set _isutc appropriately
        if self.swifttime is not None or self.met is not None:
            self._isutc = False
        else:
            self._isutc = True
        # Basic check that anything is set
        if (
            self.met is not None
            or self.swifttime is not None
            or self.utctime is not None
        ):
            return True

    def to_utctime(self):
        """Convert all entries to a UTC time base"""
        mets = [entry.met for entry in self.entries]
        utcfs = [entry.utcf for entry in self.entries]
        self.entries = [
            swiftdatetime.frommet(mets[i], utcf=utcfs[i], isutc=True)
            for i in range(len(mets))
        ]

    def to_swifttime(self):
        """Convert all entries to a Swift Time base"""
        mets = [entry.met for entry in self.entries]
        utcfs = [entry.utcf for entry in self.entries]
        self.entries = [
            swiftdatetime.frommet(mets[i], utcf=utcfs[i], isutc=False)
            for i in range(len(mets))
        ]

    # Aliases
    mettime = met
    swift = swifttime
    utc = utctime


Clock = Swift_Clock


def index_datetimes(dictionary, i=0, values=[], setvals=None):
    """Recursively spider a dictionary looking for datetimes and updating them
    if necessary"""
    # Don't spider internal variables
    keys = [key for key in list(dictionary.keys())]
    # Go through all keys
    for key in keys:
        value = dictionary[key]
        # Don't index any `Swift_Clock`s
        if type(value) is Swift_Clock:
            continue
        # If value is another dict, recurse
        if isinstance(value, dict):
            i, values = index_datetimes(value, i, values, setvals=setvals)

        # If value is a list, recurse one by one
        elif isinstance(value, (list, tuple)):
            for j in range(len(value)):
                i, values = index_datetimes(
                    {f"value{j}": value[j]}, i, values, setvals=setvals
                )

        # If value is a datetime, record and/or update to the result from
        # Swift_Clock, increment the counter
        elif isinstance(value, datetime):
            if setvals is not None:
                dictionary[key] = setvals[i]
            values.append(value)
            i += 1

        # If value is a class object other than a datetime, convert to dict and recurse
        elif hasattr(value, "__dict__"):
            i, values = index_datetimes(value.__dict__, i, values, setvals=setvals)

    # Return counter and values
    return i, values


class TOOAPI_ClockCorrect:
    """Mixin for clock correction. Provides the  `clock_correct` method, which
    spiders through a class looking for datetimes, submits them to Swift_Clock,
    and then replaces them all with the results of Swift_Clock."""

    def clock_correct(self):
        """Spider through the class dictionary recording datetimes, and then
        updating them using Swift_Clock"""
        if not hasattr(self, "_clock"):
            # Read in all datetime values into an array
            _, datevalues = index_datetimes(self.__dict__, 0, [])

            # What is the base time format for this class? Send that to Clock for
            # clock correction
            dts = [dt for dt in datevalues]
            if len(dts) > 0:
                if self._isutc:
                    self._clock = Swift_Clock(utctime=dts)
                else:
                    self._clock = Swift_Clock(swifttime=dts)

                # Replace existing datetime values with clock corrected swiftdatetimes
                _, _ = index_datetimes(self.__dict__, 0, [], setvals=self._clock)

        # After clock correction, make UTC the default time system
        self.to_utctime()

    def to_utctime(self):
        """Convert times to a UTC base"""
        self._clock.to_utctime()
        _, _ = index_datetimes(self.__dict__, 0, [], setvals=self._clock)

    def to_swifttime(self):
        """Convert times to a Swift time base"""
        self._clock.to_swifttime()
        _, _ = index_datetimes(self.__dict__, 0, [], setvals=self._clock)

    def _header_title(self, parameter):
        """Add UTC or Swift to headers in table depending on the default"""
        title = self._varnames[parameter]
        value = getattr(self, parameter)
        if type(value) == swiftdatetime:
            if value.isutc:
                title += " (UTC)"
            else:
                title += " (Swift)"
        return title
