from datetime import datetime


def utcnow():
    """Return the current UTC time as a datetime object."""
    return datetime.utcnow().replace(tzinfo=None)
