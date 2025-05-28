from datetime import datetime, timedelta
from typing import Union

from astropy import units as u  # type: ignore[import-untyped]


def utcnow():
    """Return the current UTC time as a datetime object."""
    return datetime.utcnow().replace(tzinfo=None)


def convert_from_timedelta(value: Union[float, int, u.Quantity, timedelta]) -> float:
    """Convert a value to a timedelta in days."""
    if isinstance(value, u.Quantity):
        return value.to(u.day).value
    elif isinstance(value, (int, float)):
        return float(value)
    elif isinstance(value, timedelta):
        return value.total_seconds() / 86400.0
    else:
        raise TypeError(f"Unsupported type for timedelta conversion: {type(value)}")
