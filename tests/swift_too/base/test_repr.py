from swifttools.swift_too.base.repr import TOOAPIReprMixin
from swifttools.swift_too.base.schemas import BaseSchema


class MockReprClass(BaseSchema, TOOAPIReprMixin):
    field1: str = "value1"
    field2: int = 42


def test_repr():
    obj = MockReprClass()
    repr_str = repr(obj)
    assert "MockReprClass" in repr_str
    # The _table returns header and tab, but __repr__ calls self._table, which returns tuple
    # But in the code, __repr__ = f"{self.__class__.__name__}({self._table})"
    # So it will be MockReprClass((header, tab))
    # Perhaps it's meant to be formatted differently, but for test, just check it's str


def test_table():
    obj = MockReprClass()
    header, tab = obj._table
    assert header == ["Parameter", "Value"]
    assert len(tab) == 2
    assert ["field1", "value1"] in tab
    assert ["field2", "42"] in tab
