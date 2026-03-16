from swifttools.swift_too.base.status import SwiftTOOStatus, TOOStatus


class TestSwiftTOOStatus:
    def test_equality_and_bool(self, status_obj, status_accepted, status_rejected):
        s = status_obj
        assert s == "Pending"
        s.status = "Accepted"
        assert s
        s.status = "Rejected"
        assert not s

    def test_error_and_warning_and_clear(self, status_obj):
        s = status_obj
        s.errors = []
        s.warnings = []
        s.error("e1")
        s.error("e1")  # duplicate should not be added twice
        assert s.errors == ["e1"]
        s.warning("w1")
        s.warning("w1")  # duplicate should not be added twice
        assert s.warnings == ["w1"]
        s.clear()
        assert s.errors == [] and s.warnings == [] and s.status == "Pending"


class TestTOOStatusAlias:
    def test_alias_TOOStatus_name(self):
        # alias TOOStatus points to SwiftTOOStatus
        assert TOOStatus is SwiftTOOStatus


class TestTOOStatus:
    def test_init_status(self, status_obj):
        status = status_obj
        assert status.status == "Pending"

    def test_init_errors(self, status_obj):
        status = status_obj
        assert status.errors == []

    def test_init_warnings(self, status_obj):
        status = status_obj
        assert status.warnings == []

    def test_init_too_id(self, status_obj):
        status = status_obj
        assert status.too_id is None

    def test_init_jobnumber(self, status_obj):
        status = status_obj
        assert status.jobnumber is None

    def test_error(self, status_obj, test_error_msg):
        status = status_obj
        status.error(test_error_msg)
        assert test_error_msg in status.errors

    def test_warning(self, status_obj, test_warning_msg):
        status = status_obj
        status.warning(test_warning_msg)
        assert test_warning_msg in status.warnings

    def test_bool(self, status_accepted, status_rejected):
        status = status_accepted
        assert bool(status) is True

        status.status = "Rejected"
        assert bool(status) is False

    def test_eq(self, status_pending):
        status = status_pending
        assert status == "Pending"
        assert "Pending" == status

    def test_clear(self, status_obj):
        status = status_obj
        status.error("error")
        status.warning("warning")
        status.clear()
        assert status.errors == []
        assert status.warnings == []
