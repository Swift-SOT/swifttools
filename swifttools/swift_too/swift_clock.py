from datetime import datetime
from typing import Union

from pydantic import computed_field

from .api_common import TOOAPIBaseclass
from .swift_datetime import swiftdatetime
from .swift_schemas import BaseSchema


class SwiftDateTimeSchema(BaseSchema):
    met: float
    utcf: float
    isutc: bool

    @computed_field  # type: ignore[prop-decorator]
    @property
    def swifttime(self) -> swiftdatetime:
        return swiftdatetime.frommet(self.met, utcf=self.utcf, isutc=self.isutc).swifttime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def utctime(self) -> swiftdatetime:
        return swiftdatetime.frommet(self.met, utcf=self.utcf, isutc=self.isutc).utctime


class SwiftClockSchema(BaseSchema):
    met: Union[float, list[float], None] = None
    utctime: Union[datetime, list[datetime], None] = None
    swifttime: Union[datetime, list[datetime], None] = None
    entries: list[SwiftDateTimeSchema] = []


class SwiftClockGetSchema(BaseSchema):
    met: Union[float, list[float], None] = None
    utctime: Union[datetime, list[datetime], None] = None
    swifttime: Union[datetime, list[datetime], None] = None


class SwiftClock(TOOAPIBaseclass, SwiftClockSchema):
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
    api_name: str = "Swift_Clock"
    _schema = SwiftClockSchema
    _get_schema = SwiftClockGetSchema
    _endpoint = "/swift/clock"

    def _post_process(self) -> None:
        self.entries = [swiftdatetime.frommet(e.met, utcf=e.utcf, isutc=e.isutc) for e in self.entries]
        self.met = [entry.met for entry in self.entries]
        self.swifttime = [entry.swifttime for entry in self.entries]
        self.utctime = [entry.utctime for entry in self.entries]

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

    def to_utctime(self):
        """Convert all entries to a UTC time base"""
        mets = [entry.met for entry in self.entries]
        utcfs = [entry.utcf for entry in self.entries]
        self.entries = [swiftdatetime.frommet(mets[i], utcf=utcfs[i], isutc=True) for i in range(len(mets))]

    def to_swifttime(self):
        """Convert all entries to a Swift Time base"""
        mets = [entry.met for entry in self.entries]
        utcfs = [entry.utcf for entry in self.entries]
        self.entries = [swiftdatetime.frommet(mets[i], utcf=utcfs[i], isutc=False) for i in range(len(mets))]


Swift_Clock = SwiftClock
Clock = SwiftClock


def index_datetimes(dictionary, i=0, values=[], setvals=None):
    """Recursively spider a dictionary looking for datetimes and updating them
    if necessary"""
    # Don't spider internal variables
    keys = [key for key in list(dictionary.keys())]
    # Go through all keys
    for key in keys:
        value = dictionary[key]
        # Don't index any `SwiftClock`s
        if type(value) is SwiftClock:
            continue
        # If value is another dict, recurse
        if isinstance(value, dict):
            i, values = index_datetimes(value, i, values, setvals=setvals)

        # If value is a list, recurse one by one
        elif isinstance(value, (list, tuple)):
            for j in range(len(value)):
                i, values = index_datetimes({f"value{j}": value[j]}, i, values, setvals=setvals)

        # If value is a datetime, record and/or update to the result from
        # SwiftClock, increment the counter
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


class TOOAPIClockCorrect:
    """Mixin for clock correction. Provides the  `clock_correct` method, which
    spiders through a class looking for datetimes, submits them to SwiftClock,
    and then replaces them all with the results of SwiftClock."""

    def clock_correct(self):
        """Spider through the class dictionary recording datetimes, and then
        updating them using SwiftClock"""
        if not hasattr(self, "_clock"):
            # Read in all datetime values into an array
            model_in = self.model_dump()
            # Get the index of the first datetime value
            _, datevalues = index_datetimes(model_in, 0, [])
            print(datevalues)
            # What is the base time format for this class? Send that to Clock for
            # clock correction
            dts = [dt for dt in datevalues]
            if len(dts) > 0:
                if self._isutc:
                    self._clock = SwiftClock(utctime=dts)
                else:
                    self._clock = SwiftClock(swifttime=dts)

                # Replace existing datetime values with clock corrected swiftdatetimes
                _, _ = index_datetimes(model_in, 0, [], setvals=self._clock)
        self.__dict__.update(model_in)

        # After clock correction, make UTC the default time system
        self.to_utctime()

    def to_utctime(self):
        """Convert times to a UTC base"""
        self._clock.to_utctime()
        _, _ = index_datetimes(self.model_dump(), 0, [], setvals=self._clock)

    def to_swifttime(self):
        """Convert times to a Swift time base"""
        self._clock.to_swifttime()
        _, _ = index_datetimes(self.model_dump(), 0, [], setvals=self._clock)

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
