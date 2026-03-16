from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from swifttools.swift_too.swift.visquery import SwiftVisQueryGetSchema


class TestSwiftVisQuery:
    @patch("swifttools.swift_too.base.common.cookie_jar")
    @patch("httpx.Client")
    def test_init_ra(self, mock_client, mock_cookie_jar, vis_query):
        assert abs(vis_query.ra - 10.0) < 1e-5

    @patch("swifttools.swift_too.base.common.cookie_jar")
    @patch("httpx.Client")
    def test_init_dec(self, mock_client, mock_cookie_jar, vis_query):
        assert abs(vis_query.dec - 20.0) < 1e-5

    @patch("swifttools.swift_too.base.common.cookie_jar")
    @patch("httpx.Client")
    def test_init_status(self, mock_client, mock_cookie_jar, vis_query):
        assert vis_query.status.status == "Pending"

    def test_validate(self, vis_query):
        with patch.object(vis_query, "validate_get", return_value=True):
            assert vis_query.validate_get() is True

    def test_table_header_with_window(self, vis_query_with_window):
        header, _ = vis_query_with_window._table
        assert header == ["Begin Time", "End Time", "Window length"]

    def test_table_length_with_window(self, vis_query_with_window):
        _, table = vis_query_with_window._table
        assert len(table) == 1

    def test_table_header_empty(self, vis_query):
        header, _ = vis_query._table
        assert header == []

    def test_table_empty(self, vis_query):
        _, table = vis_query._table
        assert table == []

    def test_entries(self, vis_query_with_window):
        assert vis_query_with_window.entries == vis_query_with_window.windows

    def test_len_zero(self, vis_query):
        assert len(vis_query) == 0

    def test_len_with_window(self, vis_query_with_window):
        assert len(vis_query_with_window) == 1

    def test_getitem(self, vis_query_with_window, vis_window):
        assert vis_query_with_window[0] == vis_window

    def test_get_schema_end_drops_length(self):
        schema = SwiftVisQueryGetSchema(
            ra=10.0,
            dec=20.0,
            begin=datetime(2023, 1, 1),
            end=datetime(2023, 1, 2),
        )
        payload = schema.model_dump(exclude_none=True)
        assert "end" in payload
        assert "length" not in payload

    def test_get_schema_defaults_length_when_no_end(self):
        schema = SwiftVisQueryGetSchema(
            ra=10.0,
            dec=20.0,
            begin=datetime(2023, 1, 1),
        )
        payload = schema.model_dump(exclude_none=True)
        assert "end" not in payload
        assert payload["length"] == 7


class TestSwiftVisWindow:
    def test_table_header(self, vis_window):
        header, _ = vis_window._table
        assert header == ["Begin Time", "End Time", "Window length"]

    def test_table_length(self, vis_window):
        _, table = vis_window._table
        assert len(table) == 1

    def test_table_begin(self, vis_window):
        _, table = vis_window._table
        assert table[0][0] == datetime(2023, 1, 1, 0, 0)

    def test_table_end(self, vis_window):
        _, table = vis_window._table
        assert table[0][1] == datetime(2023, 1, 2, 0, 0)

    def test_table_length_value(self, vis_window):
        _, table = vis_window._table
        assert table[0][2] == timedelta(days=1)

    def test_getitem_begin(self, vis_window):
        assert vis_window[0] == vis_window.begin

    def test_getitem_end(self, vis_window):
        assert vis_window[1] == vis_window.end

    def test_getitem_index_error(self, vis_window):
        with pytest.raises(IndexError):
            _ = vis_window[2]
