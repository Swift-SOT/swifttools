# Local fixtures for tests/swift_too/base/status
import pytest

from swifttools.swift_too.base.status import TOOStatus


@pytest.fixture
def status_obj():
    """Basic TOOStatus instance"""
    return TOOStatus()


@pytest.fixture
def status_pending():
    """TOOStatus instance with 'Pending' status"""
    return TOOStatus(status="Pending")


@pytest.fixture
def status_accepted():
    """TOOStatus instance with 'Accepted' status"""
    return TOOStatus(status="Accepted")


@pytest.fixture
def status_rejected():
    """TOOStatus instance with 'Rejected' status"""
    return TOOStatus(status="Rejected")


@pytest.fixture
def test_error_msg():
    """Common test error message"""
    return "test error"


@pytest.fixture
def test_warning_msg():
    """Common test warning message"""
    return "test warning"
