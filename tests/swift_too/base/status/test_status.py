from swifttools.swift_too.base.status import SwiftTOOStatus, TOOStatus


def test_status_equality_and_bool():
    s = SwiftTOOStatus()
    assert s == "Pending"
    s.status = "Accepted"
    assert s
    s.status = "Rejected"
    assert not s


def test_status_error_and_warning_and_clear():
    s = SwiftTOOStatus()
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


def test_alias_TOOStatus_name():
    # alias TOOStatus points to SwiftTOOStatus
    assert TOOStatus is SwiftTOOStatus


def test_too_status_init():
    status = TOOStatus()
    assert status.status == "Pending"
    assert status.errors == []
    assert status.warnings == []
    assert status.too_id is None
    assert status.jobnumber is None


def test_too_status_error():
    status = TOOStatus()
    status.error("test error")
    assert "test error" in status.errors


def test_too_status_warning():
    status = TOOStatus()
    status.warning("test warning")
    assert "test warning" in status.warnings


def test_too_status_bool():
    status = TOOStatus(status="Accepted")
    assert bool(status) is True

    status.status = "Rejected"
    assert bool(status) is False


def test_too_status_eq():
    status = TOOStatus(status="Pending")
    assert status == "Pending"
    assert "Pending" == status


def test_too_status_clear():
    status = TOOStatus()
    status.error("error")
    status.warning("warning")
    status.clear()
    assert status.errors == []
    assert status.warnings == []
