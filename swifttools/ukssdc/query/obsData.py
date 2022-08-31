__docformat__ = "restructedtext en"
from .dataquery_base import dataQuery


class ObsQuery(dataQuery):
    """A request to query the main Swift observation database.

    This inherits from the dataQuery class, and adds no new functions,
    it simply defines the database, tables and default columns for the
    observation database.

    """

    def __init__(self, table=None, silent=True, verbose=False):
        super().__init__(silent=silent, verbose=verbose)

        # Set the basic details for an obsquery - the database, acceptable
        # tables and default table.
        self._dbName = "obs"
        self._tables = ("swiftmastr", "swiftxrlog", "swiftbalog", "swiftuvlog", "swifttdrss")

        # Set the table, to default or to that requested.
        if table is not None:
            self.table = table
        else:
            self.table = "swiftmastr"
