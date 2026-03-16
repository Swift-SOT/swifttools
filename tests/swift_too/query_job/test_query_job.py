from unittest.mock import Mock

import pytest

from swifttools.swift_too.query_job import QueryJob


@pytest.fixture
def mock_job():
    job = QueryJob(jobnumber=123, status="Completed")
    job.result = Mock()
    job.result.__class__.__name__ = "MockResult"
    job._parameters = ["jobnumber"]
    job._attributes = ["status"]
    return job


class TestQueryJobInit:
    def test_init_raises_type_error(self):
        with pytest.raises(TypeError):
            _ = QueryJob(123)


class TestQueryJobTable:
    def test_header(self, mock_job):
        header, _ = mock_job._table
        assert header == ["Parameter", "Value"]

    def test_jobnumber_in_table(self, mock_job):
        _, table = mock_job._table
        assert ["jobnumber", 123] in table

    def test_result_in_table(self, mock_job):
        _, table = mock_job._table
        assert ["result", "MockResult object"] in table
