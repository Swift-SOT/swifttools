import pytest

from swifttools.swift_too.swift.instruments import TOOAPIInstruments


def test_too_api_instruments_init():
    inst = TOOAPIInstruments(uvot_mode=0x9999, xrt_mode="PC", bat_mode=1)
    assert inst.uvot_mode == 0x9999
    assert inst.xrt_mode == 7  # PC
    assert inst.bat_mode == 1


def test_too_api_instruments_xrt_property():
    inst = TOOAPIInstruments(xrt_mode=7)
    assert inst.xrt == "PC"
    inst2 = TOOAPIInstruments(xrt_mode=None)
    assert inst2.xrt == "Unset"


def test_too_api_instruments_uvot_property():
    inst = TOOAPIInstruments(uvot_mode=0x9999)
    assert inst.uvot == "0x9999"
    inst2 = TOOAPIInstruments(uvot_mode="test")
    assert inst2.uvot == "test"


def test_too_api_instruments_bat_property():
    inst = TOOAPIInstruments(bat_mode=0x1234)
    assert inst.bat == "0x1234"
    inst2 = TOOAPIInstruments(bat_mode="test")
    assert inst2.bat == "test"


def test_too_api_instruments_approved_properties():
    inst = TOOAPIInstruments(uvot_mode_approved=0x9999, xrt_mode_approved=6)
    assert inst.uvot_mode_approved_str == "0x9999"
    assert inst.xrt_mode_approved_str == "WT"


def test_xrt_mode_convert_valid_string():
    inst = TOOAPIInstruments(xrt_mode="PC")
    assert inst.xrt_mode == 7


def test_xrt_mode_convert_valid_int():
    inst = TOOAPIInstruments(xrt_mode=6)
    assert inst.xrt_mode == 6


def test_xrt_mode_convert_invalid_string():
    with pytest.raises(ValueError):
        TOOAPIInstruments(xrt_mode="Invalid")


def test_xrt_mode_convert_invalid_int():
    with pytest.raises(ValueError):
        TOOAPIInstruments(xrt_mode=999)


def test_uvot_mode_convert_hex_string():
    inst = TOOAPIInstruments(uvot_mode="0x9999")
    assert inst.uvot_mode == 0x9999


def test_uvot_mode_convert_int_string():
    inst = TOOAPIInstruments(uvot_mode="9999")
    assert inst.uvot_mode == 9999


def test_uvot_mode_convert_int():
    inst = TOOAPIInstruments(uvot_mode=9999)
    assert inst.uvot_mode == 9999


def test_bat_mode_conversion():
    """Test BAT mode conversion using uvot_mode_convert"""
    inst = TOOAPIInstruments(bat_mode="0x1234")
    assert inst.bat_mode == 0x1234
    assert inst.bat == "0x1234"


def test_uvot_mode_convert_with_colon():
    """Test UVOT mode conversion with colon syntax (should fail and return as is)"""
    inst = TOOAPIInstruments(uvot_mode="9999:filter")
    assert inst.uvot_mode == "9999:filter"


def test_uvot_mode_convert_invalid():
    """Test UVOT mode conversion with invalid input"""
    inst = TOOAPIInstruments(uvot_mode="invalid")
    assert inst.uvot_mode == "invalid"


def test_xrt_mode_convert_none():
    """Test XRT mode conversion with None"""
    inst = TOOAPIInstruments(xrt_mode=None)
    assert inst.xrt_mode is None
    assert inst.xrt == "Unset"


def test_approved_modes_conversion():
    """Test conversion of approved modes"""
    inst = TOOAPIInstruments(uvot_mode_approved="0x9999", xrt_mode_approved="PC")
    assert inst.uvot_mode_approved == 0x9999
    assert inst.xrt_mode_approved == 7
    assert inst.uvot_mode_approved_str == "0x9999"
    assert inst.xrt_mode_approved_str == "PC"
