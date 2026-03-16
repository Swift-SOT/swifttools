# Local fixtures for tests/swift_too/base/repr

from typing import Union

import pytest
from pydantic import BaseModel

from swifttools.swift_too.base.repr import TOOAPIReprMixin
from swifttools.swift_too.base.schemas import BaseSchema
from swifttools.swift_too.base.status import TOOStatus


class ReprModel(TOOAPIReprMixin, BaseModel):
    name: Union[str, None] = None
    tags: list[str] = []
    status: Union[TOOStatus, str] = TOOStatus()


class MockReprClass(BaseSchema, TOOAPIReprMixin):
    field1: str = "value1"
    field2: int = 42


@pytest.fixture
def repr_model():
    return ReprModel()


@pytest.fixture
def repr_model_with_data():
    obj = ReprModel(name="TestName", tags=["a", "b"], status=TOOStatus())
    obj.status.status = "Pending"
    return obj


@pytest.fixture
def mock_repr_class():
    return MockReprClass()
