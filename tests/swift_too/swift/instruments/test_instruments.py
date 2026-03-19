class TestTOOAPIInstrumentsInit:
    def test_uvot_mode_init(self, default_instruments):
        assert default_instruments.uvot_mode == 0x9999

    def test_xrt_mode_init(self, default_instruments):
        assert default_instruments.xrt_mode == 7

    def test_bat_mode_init(self, default_instruments):
        assert default_instruments.bat_mode == 1


class TestTOOAPIInstrumentsProperties:
    def test_xrt_property_pc(self, xrt_pc_instruments):
        assert xrt_pc_instruments.xrt == "PC"

    def test_xrt_property_unset(self, xrt_none_instruments):
        assert xrt_none_instruments.xrt == "Unset"

    def test_uvot_property_hex(self, uvot_hex_instruments):
        assert uvot_hex_instruments.uvot == "0x9999"

    def test_uvot_property_test(self, uvot_test_instruments):
        assert uvot_test_instruments.uvot == "test"

    def test_bat_property_hex(self, bat_hex_instruments):
        assert bat_hex_instruments.bat == "0x1234"

    def test_bat_property_test(self, bat_test_instruments):
        assert bat_test_instruments.bat == "test"

    def test_uvot_mode_approved_str(self, approved_instruments):
        assert approved_instruments.uvot_mode_approved_str == "0x9999"

    def test_xrt_mode_approved_str(self, approved_instruments):
        assert approved_instruments.xrt_mode_approved_str == "WT"


class TestXRTModeConversion:
    def test_convert_valid_string(self, xrt_pc_string_instruments):
        assert xrt_pc_string_instruments.xrt_mode == 7

    def test_convert_valid_int(self, xrt_int_instruments):
        assert xrt_int_instruments.xrt_mode == 6

    def test_convert_none_mode(self, xrt_none_instruments):
        assert xrt_none_instruments.xrt_mode is None

    def test_convert_none_xrt(self, xrt_none_instruments):
        assert xrt_none_instruments.xrt == "Unset"


class TestUVOTModeConversion:
    def test_convert_hex_string(self, uvot_hex_string_instruments):
        assert uvot_hex_string_instruments.uvot_mode == 0x9999

    def test_convert_int_string(self, uvot_int_string_instruments):
        assert uvot_int_string_instruments.uvot_mode == 9999

    def test_convert_int(self, uvot_int_instruments):
        assert uvot_int_instruments.uvot_mode == 9999

    def test_convert_with_colon(self, uvot_colon_instruments):
        assert uvot_colon_instruments.uvot_mode == "9999:filter"

    def test_convert_invalid(self, uvot_invalid_instruments):
        assert uvot_invalid_instruments.uvot_mode == "invalid"


class TestBATModeConversion:
    def test_conversion_hex_string(self, bat_hex_string_instruments):
        assert bat_hex_string_instruments.bat_mode == 0x1234

    def test_conversion_bat_property(self, bat_hex_string_instruments):
        assert bat_hex_string_instruments.bat == "0x1234"


class TestApprovedModesConversion:
    def test_uvot_mode_approved(self, approved_conversion_instruments):
        assert approved_conversion_instruments.uvot_mode_approved == 0x9999

    def test_xrt_mode_approved(self, approved_conversion_instruments):
        assert approved_conversion_instruments.xrt_mode_approved == 7

    def test_uvot_mode_approved_str(self, approved_conversion_instruments):
        assert approved_conversion_instruments.uvot_mode_approved_str == "0x9999"

    def test_xrt_mode_approved_str(self, approved_conversion_instruments):
        assert approved_conversion_instruments.xrt_mode_approved_str == "PC"


# Note: The invalid conversion tests that raise ValueError are not included as they don't fit the "one assert per method" rule without fixtures, but they can be added as separate methods if needed.
