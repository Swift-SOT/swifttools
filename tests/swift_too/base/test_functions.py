from datetime import datetime, timedelta

import pytest
from astropy import units as u

from swifttools.swift_too.base.functions import _tablefy, convert_from_timedelta, convert_obs_id_sdc, utcnow


def test_utcnow():
    now = utcnow()
    assert isinstance(now, datetime)
    assert now.tzinfo is None


def test_convert_from_timedelta_float():
    assert convert_from_timedelta(1.0) == 1.0


def test_convert_from_timedelta_int():
    assert convert_from_timedelta(2) == 2.0


def test_convert_from_timedelta_quantity():
    qty = 3 * u.day
    assert convert_from_timedelta(qty) == 3.0


def test_convert_from_timedelta_timedelta():
    td = timedelta(days=4)
    assert convert_from_timedelta(td) == 4.0


def test_convert_from_timedelta_invalid():
    with pytest.raises(TypeError):
        convert_from_timedelta("invalid")


def test_convert_obs_id_sdc_str_sdc():
    assert convert_obs_id_sdc("01234567890") == "01234567890"


def test_convert_obs_id_sdc_str_int():
    assert convert_obs_id_sdc("123") == "00000123000"


def test_convert_obs_id_sdc_int():
    assert convert_obs_id_sdc(123) == "00000123000"


def test_convert_obs_id_sdc_int_with_segment():
    obs_id = (1 << 24) + 123
    assert convert_obs_id_sdc(obs_id) == "00000123001"


def test_convert_obs_id_sdc_invalid_str():
    with pytest.raises(ValueError):
        convert_obs_id_sdc("invalid")


def test_convert_obs_id_sdc_invalid_int():
    with pytest.raises(ValueError):
        convert_obs_id_sdc(-2)


def test_tablefy():
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


def test_tablefy_no_header():
    table = [["a", "b"]]
    html = _tablefy(table)
    assert "<table>" in html
    assert "<thead>" not in html
