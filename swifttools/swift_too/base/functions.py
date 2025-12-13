import re
from datetime import datetime, timedelta, timezone
from typing import Union

from astropy import units as u  # type: ignore[import-untyped]


def utcnow():
    """Return the current UTC time as a datetime object."""
    return datetime.now(tz=timezone.utc).replace(tzinfo=None)


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


def convert_obs_id_sdc(obs_id: Union[str, int]) -> str:
    """
    Convert various formats for obs_id (SDC and Spacecraft) into one format
    (Spacecraft)
    """
    if isinstance(obs_id, str):
        # All SDC format target IDs are 11 digits long and start with a "0"
        # (unless we get into the 10,000,000 target ID range)
        if obs_id.startswith("0"):
            if re.match(r"0[0-9]{10}", obs_id) is None:
                raise ValueError("ERROR: Obsnum string format incorrect")
            return obs_id
        # Handle case where obsids are strings, but not in SDC format
        elif re.match(r"[0-9]+", obs_id) is None:
            raise ValueError("ERROR: Obsnum string format incorrect")
        else:
            obs_id = int(obs_id)

    if isinstance(obs_id, int):
        if obs_id == -1:
            return "00000000000"
        if obs_id < 0 or obs_id > 0xFFFFFFFF:
            raise ValueError("ERROR: Obsnum int format incorrect")
        # Convert to SDC format
        targetid = obs_id & 0xFFFFFF
        segment = obs_id >> 24
        return f"{targetid:08d}{segment:03d}"
    else:
        raise ValueError("`obs_id` in wrong format.")


def _tablefy(table, header=None):
    """Simple HTML table generator

    Parameters
    ----------
    table : list
        Data for table
    header : list
        Headers for table, by default None

    Returns
    -------
    str
        HTML formatted table.
    """

    tab = "<table>"
    if header is not None:
        tab += "<thead>"
        tab += "".join([f"<th style='text-align: left;'>{head}</th>" for head in header])
        tab += "</thead>"

    for row in table:
        tab += "<tr>"
        # Replace any carriage returns with <br>
        row = [f"{col}".replace("\n", "<br>") for col in row]
        tab += "".join([f"<td style='text-align: left;'>{col}</td>" for col in row])
        tab += "</tr>"
    tab += "</table>"
    return tab
