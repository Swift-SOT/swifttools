import re
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


def convert_obsnum_sdc(obsnum: Union[str, int]) -> str:
    """
    Convert various formats for obsnum (SDC and Spacecraft) into one format
    (Spacecraft)
    """
    if isinstance(obsnum, str):
        # All SDC format target IDs are 11 digits long and start with a "0"
        # (unless we get into the 10,000,000 target ID range)
        if obsnum.startswith("0"):
            if re.match(r"0[0-9]{10}", obsnum) is None:
                raise ValueError("ERROR: Obsnum string format incorrect")
            return obsnum
        # Handle case where obsids are strings, but not in SDC format
        elif re.match(r"[0-9]+", obsnum) is None:
            raise ValueError("ERROR: Obsnum string format incorrect")
        else:
            obsnum = int(obsnum)

    if isinstance(obsnum, int):
        if obsnum == -1:
            return "00000000000"
        if obsnum < 0 or obsnum > 0xFFFFFFFF:
            raise ValueError("ERROR: Obsnum int format incorrect")
        # Convert to SDC format
        targetid = obsnum & 0xFFFFFF
        segment = obsnum >> 24
        return f"{targetid:08d}{segment:03d}"
    else:
        raise ValueError("`obsnum` in wrong format.")
