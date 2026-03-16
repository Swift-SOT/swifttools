from datetime import datetime, timedelta

import pytest

from swifttools.swift_too.swift.datetime import swiftdatetime


@pytest.fixture
def basic_dt():
    return swiftdatetime(2023, 1, 1, 12, 0, 0)


@pytest.fixture
def utc_dt():
    return swiftdatetime(2023, 1, 1, 12, 0, 0, isutc=True)


@pytest.fixture
def utc_dt_with_utcf():
    return swiftdatetime(2023, 1, 1, 12, 0, 0, isutc=True, utcf=10.5)


@pytest.fixture
def dt_for_met():
    dt = swiftdatetime(2023, 1, 1)
    dt._swifttime = datetime(2001, 1, 1, 12, 0, 0)
    return dt


@pytest.fixture
def dt_for_setters():
    return swiftdatetime(2023, 1, 1)


@pytest.fixture
def utc_dt_for_property():
    return swiftdatetime(2023, 1, 1, 12, 0, 0, isutc=True)


@pytest.fixture
def non_utc_dt_for_property():
    return swiftdatetime(2023, 1, 1, 12, 0, 0, isutc=False)


@pytest.fixture
def dt_for_table():
    return swiftdatetime(2023, 1, 1, 12, 0, 0, isutc=True, utcf=10.0)


@pytest.fixture
def dt1_for_sub():
    return swiftdatetime(2023, 1, 1, 12, 0, 0)


@pytest.fixture
def dt2_for_sub():
    return swiftdatetime(2023, 1, 1, 11, 0, 0)


@pytest.fixture
def dt_for_add():
    return swiftdatetime(2023, 1, 1, 12, 0, 0)


@pytest.fixture
def td_for_add():
    return timedelta(hours=1)


class TestSwiftDatetimeInit:
    def test_init_year(self, basic_dt):
        assert basic_dt.year == 2023

    def test_init_month(self, basic_dt):
        assert basic_dt.month == 1

    def test_init_day(self, basic_dt):
        assert basic_dt.day == 1

    def test_init_hour(self, basic_dt):
        assert basic_dt.hour == 12

    def test_init_minute(self, basic_dt):
        assert basic_dt.minute == 0

    def test_init_second(self, basic_dt):
        assert basic_dt.second == 0


class TestSwiftDatetimeRepr:
    def test_repr_contains_swiftdatetime(self, utc_dt_with_utcf):
        repr_str = repr(utc_dt_with_utcf)
        assert "swiftdatetime" in repr_str

    def test_repr_contains_year(self, utc_dt_with_utcf):
        repr_str = repr(utc_dt_with_utcf)
        assert "2023" in repr_str

    def test_repr_contains_isutc(self, utc_dt_with_utcf):
        repr_str = repr(utc_dt_with_utcf)
        assert "isutc=True" in repr_str

    def test_repr_contains_utcf(self, utc_dt_with_utcf):
        repr_str = repr(utc_dt_with_utcf)
        assert "utcf=10.5" in repr_str


class TestSwiftDatetimeIsutcProperty:
    def test_isutc_default_false(self, dt_for_setters):
        assert dt_for_setters.isutc is False

    def test_isutc_set_true(self, dt_for_setters):
        dt_for_setters.isutc = True
        assert dt_for_setters.isutc is True


class TestSwiftDatetimeMetProperty:
    def test_met_is_float(self, dt_for_met):
        met = dt_for_met.met
        assert isinstance(met, float)


class TestSwiftDatetimeMetSetter:
    def test_met_setter(self, dt_for_setters):
        dt_for_setters.met = 123456789.0
        assert dt_for_setters._met == 123456789.0


class TestSwiftDatetimeUtctimeProperty:
    def test_utctime_is_datetime(self, utc_dt_for_property):
        utctime = utc_dt_for_property.utctime
        assert isinstance(utctime, datetime)

    def test_utctime_year(self, utc_dt_for_property):
        utctime = utc_dt_for_property.utctime
        assert utctime.year == 2023


class TestSwiftDatetimeUtctimeSetter:
    def test_utctime_setter(self, dt_for_setters):
        new_utc = datetime(2023, 6, 1, 12, 0, 0)
        dt_for_setters.utctime = new_utc
        assert dt_for_setters._utctime == new_utc


class TestSwiftDatetimeSwifttimeProperty:
    def test_swifttime_is_datetime(self, non_utc_dt_for_property):
        swifttime = non_utc_dt_for_property.swifttime
        assert isinstance(swifttime, datetime)

    def test_swifttime_year(self, non_utc_dt_for_property):
        swifttime = non_utc_dt_for_property.swifttime
        assert swifttime.year == 2023


class TestSwiftDatetimeSwifttimeSetter:
    def test_swifttime_setter(self, dt_for_setters):
        new_swt = datetime(2023, 6, 1, 12, 0, 0)
        dt_for_setters.swifttime = new_swt
        assert dt_for_setters._swifttime == new_swt


class TestSwiftDatetimeTableProperty:
    def test_table_header_length(self, dt_for_table):
        header, data = dt_for_table._table
        assert len(header) == 4

    def test_table_data_length(self, dt_for_table):
        header, data = dt_for_table._table
        assert len(data) == 1

    def test_table_header_contains_utc(self, dt_for_table):
        header, data = dt_for_table._table
        assert "UTC" in header[2]


class TestSwiftDatetimeFrommet:
    def test_frommet_is_swiftdatetime(self):
        dt = swiftdatetime.frommet(123456789.0, utcf=10.0, isutc=True)
        assert isinstance(dt, swiftdatetime)

    def test_frommet_utcf(self):
        dt = swiftdatetime.frommet(123456789.0, utcf=10.0, isutc=True)
        assert dt.utcf == 10.0

    def test_frommet_isutc(self):
        dt = swiftdatetime.frommet(123456789.0, utcf=10.0, isutc=True)
        assert dt.isutc is True


class TestSwiftDatetimeAliases:
    def test_swift_alias(self, dt_for_setters):
        assert dt_for_setters.swift == dt_for_setters.swifttime

    def test_utc_alias(self, dt_for_setters):
        assert dt_for_setters.utc == dt_for_setters.utctime


class TestSwiftDatetimeSub:
    def test_sub_is_timedelta(self, dt1_for_sub, dt2_for_sub):
        diff = dt1_for_sub - dt2_for_sub
        assert isinstance(diff, timedelta)


class TestSwiftDatetimeAdd:
    def test_add_is_swiftdatetime(self, dt_for_add, td_for_add):
        result = dt_for_add + td_for_add
        assert isinstance(result, swiftdatetime)

    def test_add_hour(self, dt_for_add, td_for_add):
        result = dt_for_add + td_for_add
        assert result.hour == 13


class TestSwiftDatetimeTzinfoRejection:
    def test_tzinfo_rejection(self):
        from datetime import timezone

        with pytest.raises(TypeError):
            swiftdatetime(2023, 1, 1, tzinfo=timezone.utc)
