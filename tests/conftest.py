from datetime import datetime, timedelta, timezone
from typing import ClassVar
from unittest.mock import Mock

import pytest
from astropy.time import Time  # type: ignore[import-untyped]
from pydantic import BaseModel

from swifttools.swift_too.base.common import (
    API_URL,
    TOOAPIBaseclass,
)
from swifttools.swift_too.base.schemas import BaseSchema
from swifttools.swift_too.base.status import TOOStatus


@pytest.fixture
def equivalent_instants():
    """2024 June 1 12:00:00 UTC, written six different ways.

    Any request field that takes a time should reduce every one of these to the
    same naive UTC datetime, whatever timezone the machine running the code is
    set to.
    """
    return [
        datetime(2024, 6, 1, 12, 0),
        datetime(2024, 6, 1, 12, 0, tzinfo=timezone.utc),
        datetime(2024, 6, 1, 17, 30, tzinfo=timezone(timedelta(hours=5, minutes=30))),
        "2024-06-01T12:00:00",
        "2024-06-01T12:00:00Z",
        Time("2024-06-01T12:00:00", scale="utc"),
    ]


@pytest.fixture
def expected_instant():
    """The naive UTC datetime that every value in `equivalent_instants` means."""
    return datetime(2024, 6, 1, 12, 0)


class MockSchema(BaseModel):
    obs_id: int | None = None
    username: str = "anonymous"


class MockTOOAPIBaseclass(BaseModel, TOOAPIBaseclass):
    """Mock class for testing TOOAPIBaseclass"""

    _endpoint: ClassVar[str] = "/test"
    _api_base: str = API_URL
    _schema: ClassVar[Mock] = Mock()
    _get_schema: ClassVar[MockSchema] = MockSchema
    _post_schema: ClassVar[Mock] = Mock()
    status: TOOStatus = TOOStatus()
    obs_id: int | None = None
    # username, shared_secret, autosubmit inherited from TOOAPIBaseclass

    def __init__(self, **kwargs) -> None:
        # Back compat
        for key, values in self._back_compat_args.items():
            for value in values:
                if value in kwargs:
                    if key not in kwargs:
                        kwargs[key] = kwargs[value]
                    del kwargs[value]
        super().__init__(**kwargs)


@pytest.fixture
def mock_schema():
    return MockSchema


@pytest.fixture
def mock_too_api_baseclass():
    return MockTOOAPIBaseclass


@pytest.fixture
def mock_base_class() -> MockTOOAPIBaseclass:
    return MockTOOAPIBaseclass(username="testuser", shared_secret="testsecret")


@pytest.fixture(autouse=True, scope="session")
def disable_validate_assignment():
    """Disable pydantic `validate_assignment` during tests to avoid
    recursion issues in environment-specific pydantic behavior.

    Tests are allowed to mutate model attributes freely; module behavior
    should remain unchanged in source files.
    """
    original = BaseSchema.model_config.get("validate_assignment", None)
    BaseSchema.model_config["validate_assignment"] = False
    yield
    if original is None:
        BaseSchema.model_config.pop("validate_assignment", None)
    else:
        BaseSchema.model_config["validate_assignment"] = original
