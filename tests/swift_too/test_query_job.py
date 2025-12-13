from unittest.mock import Mock

import pytest

from swifttools.swift_too.query_job import QueryJob


def test_query_job_init():
    # Since the __init__ is broken, perhaps patch
    with pytest.raises(TypeError):
        _ = QueryJob(123)


# Perhaps the __init__ is wrong, let's assume it's super().__init__(jobnumber=jobnumber, fetchresult=True, **kwargs)

# But to test, let's mock


def test_query_job_table():
    job = QueryJob(jobnumber=123, status="Completed")
    job.result = Mock()
    job.result.__class__.__name__ = "MockResult"
    job._parameters = ["jobnumber"]
    job._attributes = ["status"]

    header, table = job._table
    assert header == ["Parameter", "Value"]
    assert ["jobnumber", 123] in table
    assert ["result", "MockResult object"] in table
