from datetime import datetime, timedelta

import pytest
from astropy import units as u

from swifttools.swift_too.base.functions import _tablefy, convert_from_timedelta, convert_obs_id_sdc, utcnow


class TestUtcnow:
    def test_utcnow_type(self):
        now = utcnow()
        assert isinstance(now, datetime)

    def test_utcnow_tzinfo(self):
        now = utcnow()
        assert now.tzinfo is None


class TestConvertFromTimedelta:
    def test_float(self):
        assert convert_from_timedelta(1.0) == 1.0

    def test_int(self):
        assert convert_from_timedelta(2) == 2.0

    def test_quantity(self):
        qty = 3 * u.day
        assert convert_from_timedelta(qty) == 3.0

    def test_timedelta(self):
        td = timedelta(days=4)
        assert convert_from_timedelta(td) == 4.0

    def test_invalid(self):
        with pytest.raises(TypeError):
            convert_from_timedelta("invalid")


class TestConvertObsIdSdc:
    def test_str_sdc(self):
        assert convert_obs_id_sdc("01234567890") == "01234567890"

    def test_str_int(self):
        assert convert_obs_id_sdc("123") == "00000123000"

    def test_int(self):
        assert convert_obs_id_sdc(123) == "00000123000"

    def test_int_with_segment(self):
        obs_id = (1 << 24) + 123
        assert convert_obs_id_sdc(obs_id) == "00000123001"

    def test_invalid_str(self):
        with pytest.raises(ValueError):
            convert_obs_id_sdc("invalid")

    def test_invalid_int(self):
        with pytest.raises(ValueError):
            convert_obs_id_sdc(-2)


class TestTablefy:
    def test_tablefy(self):
        table = [["a", "b"], ["c", "d"]]
        header = ["col1", "col2"]
        html = _tablefy(table, header)
        assert "<table>" in html
        assert "<thead>" in html
        assert "<th" in html
        assert "<tr>" in html
        assert "<td" in html
        assert "a" in html
        assert "b" in html
        assert "c" in html
        assert "d" in html

    def test_no_header(self):
        table = [["a", "b"]]
        html = _tablefy(table)
        assert "<table>" in html
        assert "<thead>" not in html
