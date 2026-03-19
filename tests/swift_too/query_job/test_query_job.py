import pytest

from swifttools.swift_too.query_job import QueryJob


class TestQueryJobInit:
    def test_init_raises_runtime_error(self):
        with pytest.raises(RuntimeError):
            _ = QueryJob(123)

    def test_init_error_message(self):
        with pytest.raises(RuntimeError, match="QueryJob is deprecated"):
            _ = QueryJob(jobnumber=123)
