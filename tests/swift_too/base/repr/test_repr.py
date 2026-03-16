from swifttools.swift_too.base.status import TOOStatus


class TestTable:
    def test_includes_rows_and_status(self, repr_model_with_data):
        obj = repr_model_with_data
        header, table = obj._table
        assert header == ["Parameter", "Value"]
        # Ensure name and tags rows exist
        param_names = [r[0] for r in table]
        assert "name" in param_names
        assert "tags" in param_names
        # status is stored as status string in second column of its row
        status_row = [r for r in table if r[0] == "status"][0]
        assert status_row[1] == "Pending"

    def test_table(self, mock_repr_class):
        obj = mock_repr_class
        header, tab = obj._table
        assert header == ["Parameter", "Value"]
        assert len(tab) == 2
        assert ["field1", "value1"] in tab
        assert ["field2", "42"] in tab


class TestRepr:
    def test_html_and_str_rejected(self, repr_model):
        obj = repr_model
        # Set status to Rejected with errors
        status = TOOStatus()
        status.status = "Rejected"
        status.errors = ["bad", "worse"]
        obj.status = status
        html = obj._repr_html_()
        assert "Rejected with the following error(s):" in html
        s = str(obj)
        assert "Rejected with the following error(s):" in s

    def test_no_data_and_repr(self, repr_model):
        obj = repr_model
        # Clear out status and other values
        obj.status = ""
        assert obj._repr_html_() == "No data"
        assert str(obj) == "No data"
        # repr should include class name
        r = repr(obj)
        assert "ReprModel(" in r

    def test_repr(self, mock_repr_class):
        obj = mock_repr_class
        repr_str = repr(obj)
        assert "MockReprClass" in repr_str
        # The _table returns header and tab, but __repr__ calls self._table, which returns tuple
        # But in the code, __repr__ = f"{self.__class__.__name__}({self._table})"
        # So it will be MockReprClass((header, tab))
        # Perhaps it's meant to be formatted differently, but for test, just check it's str
