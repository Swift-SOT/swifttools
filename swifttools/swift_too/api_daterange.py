from datetime import timedelta, datetime
from .api_common import convert_to_dt


HAS_ASTROPY = False
try:
    import astropy.units as u
    from astropy.time import TimeDelta

    HAS_ASTROPY = True
except ImportError:
    pass


class TOOAPI_Daterange:
    """A Mixin for all classes that have begin, end and length for setting date
    ranges. These functions allow dates to be givin as strings,
    datetime.datetime or astropy Time objects, and length to be given in number
    of days, or as a datetime.timedelta object or an astropy TimeDelta
    object."""

    _length = None
    _begin = None
    _end = None
    _exposure = None

    @property
    def begin(self):
        if (
            hasattr(self._begin, "utcf")
            and self._begin.utcf is None
            and self.utcf is not None
        ):
            self._begin.utcf = self.utcf
        return self._begin

    @property
    def end(self):
        if self._begin is not None and self._length is not None and self._end is None:
            self._end = self.begin + timedelta(days=self._length)
        if (
            hasattr(self._end, "utcf")
            and self._end.utcf is None
            and self.utcf is not None
        ):
            self._end.utcf = self.utcf
        return self._end

    @property
    def length(self):
        if self._length is None and self._begin is not None and self._end is not None:
            return (self._end - self._begin).total_seconds() / 86400.0
        return self._length

    @begin.setter
    def begin(self, begin):
        self._begin = convert_to_dt(begin, self._isutc, outfunc=datetime)

    @end.setter
    def end(self, end):
        self._end = convert_to_dt(end, self._isutc, outfunc=datetime)
        # If we're changing the end, and begin is defined, then update length
        if self._begin is not None and self._end is not None:
            self._length = (self._end - self._begin).total_seconds() / 86400.0

    @length.setter
    def length(self, length):
        if HAS_ASTROPY and type(length) is u.quantity.Quantity:
            self._length = length.to(u.day).value
        elif type(length) == timedelta:
            self._length = length.total_seconds() / 86400.0
        elif HAS_ASTROPY and type(length) is TimeDelta:
            self._length = length.to_datetime().total_seconds() / 86400.0
        elif length is None:
            self._length = None
        else:
            try:
                self._length = float(length)
            except ValueError:
                raise TypeError(
                    "Length should be given as a datetime.timedelta, astropy TimeDelta, astropy quantity or as a number of days"
                )

        # If we're changing length, make sure end is changed
        if self._begin is not None and self._length is not None:
            self._end = self._begin + timedelta(days=self._length)

    @property
    def exposure(self):
        return self._exposure

    @exposure.setter
    def exposure(self, exposure):
        if HAS_ASTROPY and type(self._exposure) is u.quantity.Quantity:
            self._exposure = exposure.to(u.second).value
        elif type(exposure) == timedelta:
            self._exposure = exposure.total_seconds()
        elif HAS_ASTROPY and type(exposure) is TimeDelta:
            self._exposure = exposure.to_datetime().total_seconds()
        elif exposure is None:
            self._exposure = None
        else:
            try:
                self._exposure = float(exposure)
            except ValueError:
                raise TypeError(
                    "Exposure should be given as a datetime.timedelta, astropy TimeDelta, astropy quantity or as a number of seconds"
                )

    # Aliases
    start = begin
    stop = end
    duration = exposure


class TOOAPI_TriggerTime:
    """Mixin to set triggertime and convert internally to a UTC naive datetime."""

    _triggertime = None

    @property
    def triggertime(self):
        return self._triggertime

    @triggertime.setter
    def triggertime(self, tt):
        self._triggertime = convert_to_dt(tt)

    # Alias for Swift_TOO
    grb_triggertime = triggertime
