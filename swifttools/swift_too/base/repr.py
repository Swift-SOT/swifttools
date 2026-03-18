import textwrap

from tabulate import tabulate

from .functions import _tablefy


class TOOAPIReprMixin:
    """Mixin to provide string and HTML representations for TOO API classes."""

    @property
    def _table(self) -> tuple[list[str], list[list[str]]]:
        """Table of details of the class"""
        _parameters = self.__class__.model_fields.keys()
        header = ["Parameter", "Value"]
        table = []
        for row in _parameters:
            value = getattr(self, row)
            if value is not None and value != [] and value != "":
                if row == "status" and not isinstance(value, str):
                    table.append([row, value.status])
                elif isinstance(value, list):
                    table.append([row, "\n".join([f"{le}" for le in value])])
                else:
                    table.append([row, "\n".join(textwrap.wrap(f"{value}"))])
        return header, table

    def _repr_html_(self) -> str:
        if hasattr(self, "status") and not isinstance(self.status, str) and self.status.status == "Rejected":
            return "<b>Rejected with the following error(s): </b>" + " ".join(self.status.errors)
        else:
            header, table = self._table
            if len(table) > 0:
                return _tablefy(table, header)
            else:
                return "No data"

    def __str__(self) -> str:
        if hasattr(self, "status") and not isinstance(self.status, str) and self.status.status == "Rejected":
            return "Rejected with the following error(s): " + " ".join(self.status.errors)
        else:
            header, table = self._table
            if len(table) > 0:
                return tabulate(table, header, tablefmt="pretty", stralign="right")
            else:
                return "No data"

    def __repr__(self) -> str:
        args = ",".join(
            [f"{row}='{getattr(self, row)}'" for row in self.__class__.model_fields if getattr(self, row) is not None]
        )
        return f"{self.__class__.__name__}({args})"
