from datetime import datetime, timedelta
from typing import Union

from astropy import units as u  # type: ignore[import-untyped]


def utcnow():
    """Return the current UTC time as a datetime object."""
    return datetime.utcnow().replace(tzinfo=None)


def convert_to_timedelta(value: Union[float, int, u.Quantity]) -> timedelta:
    """Convert a value to a timedelta in days."""
    if isinstance(value, u.Quantity):
        return timedelta(days=value.to_value(u.day))
    elif isinstance(value, (int, float)):
        return timedelta(days=value)
    elif isinstance(value, timedelta):
        return value
    else:
        raise TypeError(f"Unsupported type for timedelta conversion: {type(value)}")
