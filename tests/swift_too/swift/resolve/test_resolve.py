from unittest.mock import patch


class TestSwiftResolveInit:
    def test_name(self, resolve_instance):
        assert resolve_instance.name == "Test Name"

    def test_status(self, resolve_instance):
        assert resolve_instance.status.status == "Pending"


class TestSwiftResolveValidate:
    def test_validate(self, resolve_instance):
        with patch.object(resolve_instance, "validate_get", return_value=True):
            assert resolve_instance.validate() is True


class TestSwiftResolveTable:
    def test_header(self, configured_resolve_instance):
        header, _ = configured_resolve_instance._table
        assert header == ["Name", "RA (J2000)", "Dec (J2000)", "Resolver"]

    def test_table_name(self, configured_resolve_instance):
        _, table = configured_resolve_instance._table
        assert table[0][0] == "Test Name"

    def test_table_ra(self, configured_resolve_instance):
        _, table = configured_resolve_instance._table
        # Floating point precision: expecting 10.00001 due to rounding
        assert table[0][1] == "10.00001"

    def test_table_dec(self, configured_resolve_instance):
        _, table = configured_resolve_instance._table
        assert table[0][2] == "20.00000"

    def test_table_resolver(self, configured_resolve_instance):
        _, table = configured_resolve_instance._table
        assert table[0][3] == "Simbad"


class TestSwiftResolveTableNoRa:
    def test_header_no_ra(self, resolve_instance):
        header, _ = resolve_instance._table
        assert header == []

    def test_table_no_ra(self, resolve_instance):
        _, table = resolve_instance._table
        assert table == []
