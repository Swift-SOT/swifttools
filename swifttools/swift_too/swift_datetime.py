from datetime import datetime, timedelta
from typing import Optional, Union


class swiftdatetime(datetime):
    """Extend datetime to store met, utcf and swifttime. Default value is UTC"""

    api_name: str = "swiftdatetime"

    _utctime: Union[datetime, None]
    _swifttime: Union[datetime, None]
    _met: Union[float, None]
    _utcf: Union[float, None]
    _isutc: bool

    def __new__(self, *args, **kwargs):
        return super().__new__(self, *args)

    def __init__(self, *args, **kwargs):
        self._met = None
        self.utcf = None
        self._swifttime = None
        self._utctime = None
        self._isutc = False
        self._isutc_set = False
        if "tzinfo" in kwargs.keys():
            raise TypeError("swiftdatetime does not support timezone information.")
        for key in kwargs.keys():
            setattr(self, key, kwargs[key])

    def __repr__(self):
        return f"swiftdatetime({self.year}, {self.month}, {self.day}, {self.hour}, {self.minute}, {self.second}, {self.microsecond}, isutc={self.isutc}, utcf={self.utcf})"

    def __sub__(self, other):
        """Redefined __sub__ to handle mismatched time bases"""
        if isinstance(other, swiftdatetime):
            if self.isutc != other.isutc and (self.utctime is None or other.utctime is None):
                raise ArithmeticError(
                    "Cannot subtract mismatched time zones with no UTCF"
                )  # FIXME - correct exception?

            if self.isutc is True and other.isutc is True or self.isutc is False and other.isutc is False:
                return super().__sub__(other)
            else:
                if self.isutc:
                    return super().__sub__(other.utctime)
                else:
                    return self.utctime.__sub__(other.utctime)
        else:
            value = super().__sub__(other)
            if hasattr(value, "isutc"):
                value.isutc = self.isutc
            return value

    def __add__(self, other):
        """Custom add for swiftdatetime. Note that UTCF is not preserved, on purpose."""
        value = super().__add__(other)
        if hasattr(value, "isutc"):
            value.isutc = self.isutc
        return value

    @property
    def isutc(self):
        return self._isutc

    @isutc.setter
    def isutc(self, utc):
        """Is this swiftdatetime based on UTC or Swift Time"""
        # if self._isutc_set is not True:
        # If we change the time base for this, reset the values of swifttime and utctime
        self._isutc = utc
        self.swifttime = None
        self.utctime = None
        self._isutc_set = True
        # else:
        #    raise AttributeError("Cannot set attribute isutc when previously set.")

    @property
    def met(self):
        if self.swifttime is not None:
            return (self.swifttime - datetime(2001, 1, 1)).total_seconds()

    @met.setter
    def met(self, met):
        self._met = met

    @property
    def utctime(self) -> Optional[datetime]:
        if self._utctime is None:
            if self.isutc:
                self._utctime = datetime(
                    self.year,
                    self.month,
                    self.day,
                    self.hour,
                    self.minute,
                    self.second,
                    self.microsecond,
                )
            elif self.utcf is not None and self.swifttime is not None:
                self._utctime = self.swifttime + timedelta(seconds=self.utcf)
        return self._utctime

    @utctime.setter
    def utctime(self, utc):
        if isinstance(utc, datetime):
            # Ensure that utctime set to a pure datetime
            self._utctime = datetime(
                utc.year,
                utc.month,
                utc.day,
                utc.hour,
                utc.minute,
                utc.second,
                utc.microsecond,
            )
        else:
            self._utctime = utc

    @property
    def swifttime(self) -> Optional[datetime]:
        if self._swifttime is None:
            if not self.isutc:
                self._swifttime = datetime(
                    self.year,
                    self.month,
                    self.day,
                    self.hour,
                    self.minute,
                    self.second,
                    self.microsecond,
                )
            elif self.utcf is not None and self.utctime is not None:
                self._swifttime = self.utctime - timedelta(seconds=self.utcf)
        return self._swifttime

    @swifttime.setter
    def swifttime(self, st):
        if isinstance(st, datetime):
            # Ensure that swifttime is set to a pure datetime
            self._swifttime = datetime(
                st.year,
                st.month,
                st.day,
                st.hour,
                st.minute,
                st.second,
                st.microsecond,
            )
        else:
            self._swifttime = st

    @property
    def _table(self):
        if self._isutc:
            header = ["MET (s)", "Swift Time", "UTC Time (default)", "UTCF (s)"]
        else:
            header = ["MET (s)", "Swift Time (default)", "UTC Time", "UTCF (s)"]
        return header, [[self.met, self.swifttime, self.utctime, self.utcf]]

    @classmethod
    def frommet(cls, met, utcf=None, isutc=False):
        """Construct a swiftdatetime from a given MET and (optional) UTCF."""
        dt = datetime(2001, 1, 1) + timedelta(seconds=met)
        if isutc and utcf is not None:
            dt += timedelta(seconds=utcf)
        ret = cls(
            dt.year,
            dt.month,
            dt.day,
            dt.hour,
            dt.minute,
            dt.second,
            dt.microsecond,
        )
        ret.utcf = utcf
        ret.isutc = isutc
        return ret

    # Attribute aliases
    swift = swifttime
    utc = utctime
