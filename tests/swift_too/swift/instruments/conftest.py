# Local fixtures for tests/swift_too/swift/instruments

import pytest

from swifttools.swift_too.swift.instruments import TOOAPIInstruments


@pytest.fixture
def default_instruments():
    return TOOAPIInstruments(uvot_mode=0x9999, xrt_mode="PC", bat_mode=1)


@pytest.fixture
def xrt_pc_instruments():
    return TOOAPIInstruments(xrt_mode=7)


@pytest.fixture
def xrt_none_instruments():
    return TOOAPIInstruments(xrt_mode=None)


@pytest.fixture
def uvot_hex_instruments():
    return TOOAPIInstruments(uvot_mode=0x9999)


@pytest.fixture
def uvot_test_instruments():
    return TOOAPIInstruments(uvot_mode="test")


@pytest.fixture
def bat_hex_instruments():
    return TOOAPIInstruments(bat_mode=0x1234)


@pytest.fixture
def bat_test_instruments():
    return TOOAPIInstruments(bat_mode="test")


@pytest.fixture
def approved_instruments():
    return TOOAPIInstruments(uvot_mode_approved=0x9999, xrt_mode_approved=6)


@pytest.fixture
def xrt_pc_string_instruments():
    return TOOAPIInstruments(xrt_mode="PC")


@pytest.fixture
def xrt_int_instruments():
    return TOOAPIInstruments(xrt_mode=6)


@pytest.fixture
def uvot_hex_string_instruments():
    return TOOAPIInstruments(uvot_mode="0x9999")


@pytest.fixture
def uvot_int_string_instruments():
    return TOOAPIInstruments(uvot_mode="9999")


@pytest.fixture
def uvot_int_instruments():
    return TOOAPIInstruments(uvot_mode=9999)


@pytest.fixture
def bat_hex_string_instruments():
    return TOOAPIInstruments(bat_mode="0x1234")


@pytest.fixture
def uvot_colon_instruments():
    return TOOAPIInstruments(uvot_mode="9999:filter")


@pytest.fixture
def uvot_invalid_instruments():
    return TOOAPIInstruments(uvot_mode="invalid")


@pytest.fixture
def approved_conversion_instruments():
    return TOOAPIInstruments(uvot_mode_approved="0x9999", xrt_mode_approved="PC")
