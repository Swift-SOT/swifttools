from typing import ClassVar, Optional
from unittest.mock import Mock

import pytest
from pydantic import BaseModel

from swifttools.swift_too.base.common import (
    API_URL,
    TOOAPIBaseclass,
)
from swifttools.swift_too.base.schemas import BaseSchema
from swifttools.swift_too.base.status import TOOStatus


class MockSchema(BaseModel):
    obs_id: Optional[int] = None
    username: str = "anonymous"


class MockTOOAPIBaseclass(BaseModel, TOOAPIBaseclass):
    """Mock class for testing TOOAPIBaseclass"""

    _endpoint: ClassVar[str] = "/test"
    _api_base: str = API_URL
    _schema: ClassVar[Mock] = Mock()
    _get_schema: ClassVar[MockSchema] = MockSchema
    _post_schema: ClassVar[Mock] = Mock()
    status: TOOStatus = TOOStatus()
    obs_id: Optional[int] = None
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
