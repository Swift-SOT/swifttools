import pytest

from swifttools.swift_too.base.schemas import BaseSchema


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
