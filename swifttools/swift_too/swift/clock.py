from datetime import datetime
from typing import Any, Optional, Union

from pydantic import ConfigDict, computed_field, model_validator

from ..base.common import TOOAPIBaseclass
from ..base.schemas import BaseSchema
from ..base.status import TOOStatus
from .datetime import swiftdatetime


class SwiftDateTimeSchema(BaseSchema):
    met: float
    utcf: float
    isutc: bool
    status: TOOStatus = TOOStatus()

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
    status: TOOStatus = TOOStatus()

    model_config = ConfigDict(extra="ignore")


class SwiftClockGetSchema(BaseSchema):
    met: Union[float, list[float], None] = None
    utctime: Union[datetime, list[datetime], None] = None
    swifttime: Union[datetime, list[datetime], None] = None

    @model_validator(mode="before")
    @classmethod
    def validate_exactly_one_field(cls, values):
        """Require exactly one of met, utctime, or swifttime to be provided"""
        if not isinstance(values, dict):
            values = values.__dict__
        provided_fields = [field for field in ["met", "utctime", "swifttime"] if values.get(field) is not None]

        if len(provided_fields) != 1:
            raise ValueError("Exactly one of 'met', 'utctime', or 'swifttime' must be provided")

        return values


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
    _schema = SwiftClockSchema
    _get_schema = SwiftClockGetSchema
    _endpoint = "/swift/clock"

    def _post_process(self) -> None:
        converted = [swiftdatetime.frommet(e.met, utcf=e.utcf, isutc=e.isutc) for e in self.entries]
        object.__setattr__(self, "entries", converted)
        object.__setattr__(self, "met", [entry.met for entry in converted])
        object.__setattr__(self, "swifttime", [entry.swifttime for entry in converted])
        object.__setattr__(self, "utctime", [entry.utctime for entry in converted])

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
        object.__setattr__(
            self,
            "entries",
            [swiftdatetime.frommet(mets[i], utcf=utcfs[i], isutc=True) for i in range(len(mets))],
        )

    def to_swifttime(self):
        """Convert all entries to a Swift Time base"""
        mets = [entry.met for entry in self.entries]
        utcfs = [entry.utcf for entry in self.entries]
        object.__setattr__(
            self,
            "entries",
            [swiftdatetime.frommet(mets[i], utcf=utcfs[i], isutc=False) for i in range(len(mets))],
        )


Swift_Clock = SwiftClock
Clock = SwiftClock


def index_datetimes(dictionary, i=0, values=None, setvals=None):
    """
    Recursively spider a dictionary looking for datetimes and updating them if
    necessary.
    """
    if values is None:
        values = []
    # Don't spider internal variables
    if isinstance(dictionary, dict):
        items = dictionary.items()
    elif hasattr(dictionary, "model_dump"):
        items = [(k, v) for k, v in dictionary.model_dump().items() if not k.startswith("_")]
    else:
        items = [
            (k, getattr(dictionary, k))
            for k in dir(dictionary)
            if not k.startswith("_") and not callable(getattr(dictionary, k))
        ]

    # Go through all keys
    for key, value in items:
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
                if isinstance(dictionary, dict):
                    dictionary[key] = setvals[i]
                else:
                    setattr(dictionary, key, setvals[i])
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

    _clock: Optional[SwiftClock] = None

    def to_utctime(self):
        """Convert times to a UTC base"""
        self._clock.to_utctime()
        self.clock_correct()

    def to_swifttime(self):
        """Convert times to a Swift time base"""
        self._clock.to_swifttime()
        self.clock_correct()

    def _header_title(self, parameter):
        """Add UTC or Swift to headers in table depending on the default"""
        title = self._varnames.get(parameter, parameter)
        value = getattr(self, parameter, None)
        if isinstance(value, swiftdatetime):
            if value.isutc:
                title += " (UTC)"
            else:
                title += " (Swift)"
        return title

    def clock_correct(self) -> None:
        """
        Recursively find all datetime values in a Pydantic model,
        apply a transformation function to them, and replace them in place.

        Args:
            model: A Pydantic BaseModel instance.
            transform_func: A function that takes a list[datetime] and returns list[datetime].

        Returns:
            The same model instance with updated datetime values.
        """
        if self._clock is None:
            # Step 1: Collect all datetime references (paths + objects)
            datetime_refs = []

            def collect_datetimes(obj: Any, path: list[Any]):
                if isinstance(obj, datetime):
                    datetime_refs.append((path.copy(), obj))
                elif isinstance(obj, BaseSchema):
                    for field_name, value in obj.__dict__.items():
                        collect_datetimes(value, path + [("model", field_name)])
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        collect_datetimes(item, path + [("list", i)])
                elif isinstance(obj, dict):
                    for k, v in obj.items():
                        collect_datetimes(v, path + [("dict", k)])

            collect_datetimes(self, [])
            self._datetime_refs = datetime_refs
            # Step 2: Apply transformation
            self._clock = Clock(swifttime=[dt for _, dt in datetime_refs])
            self._clock.to_utctime()
        else:
            datetime_refs = self._datetime_refs

        # Step 3: Replace them in place.
        # Prefer explicit UTC values, which are swiftdatetime instances.
        replacement_values = self._clock.entries

        for (path, _), new_value in zip(datetime_refs, replacement_values):
            if isinstance(new_value, SwiftDateTimeSchema):
                new_value = new_value.utctime
            current = self
            for kind, key in path[:-1]:
                if kind == "model":
                    current = getattr(current, key)
                elif kind == "list":
                    assert isinstance(current, list), f"Expected list but got {type(current)}"
                    current = current[key]
                elif kind == "dict":
                    assert isinstance(current, dict), f"Expected dict but got {type(current)}"
                    current = current[key]
            kind, key = path[-1]
            if kind == "model":
                # Avoid validate-assignment coercing swiftdatetime back into schema objects.
                object.__setattr__(current, key, new_value)
            elif kind == "list":
                assert isinstance(current, list), f"Expected list but got {type(current)}"
                current[key] = new_value
            elif kind == "dict":
                assert isinstance(current, dict), f"Expected dict but got {type(current)}"
                current[key] = new_value
