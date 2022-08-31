"""Filters for the database queries.

This module defines a single class, 'filter', which is used to compile
filters for database queries -- essentially the building blocks of
SQL 'WHERE' statements.

"""
__docformat__ = "restructedtext en"


class filter:
    """
    A filter, or pair of filters on an SQL column.

    This class stores the components of a query on an SQL column, which
    has one or two parts, combined with AND or OR.

    The components are:

    colName : str The name of the column to filter on.

    filter : str The filter - must match a specific subset.

    val : Union[list,float,int,str] The value associated with the
        filter. OPTIONAL

    combiner : str How to combine the two filter (AND/OR) OPTIONAL

    filter2 : str The second filter - must match a specific subset.

    val2 : Union[list,float,int,str] The value associated with the
        second filter. OPTIONAL


    """

    # ---------------------------------------------------------------
    # Static variables

    # _filters details acceptable values for filter/filter2, and how
    # many arguments each needs.
    _filters = {
        "<": 1,
        ">": 1,
        "=": 1,
        "<=": 1,
        ">=": 1,
        "LIKE": 1,
        "BETWEEN": 2,
        "NOT LIKE": 1,
        "!=": 1,
        "IS NULL": 0,
        "IS NOT NULL": 0,
    }
    # Also need to know the acceptable combiners:
    _combs = ["AND", "OR"]

    _dictKeys = ("colName", "filter", "val", "combiner", "filter2", "val2")

    @staticmethod
    def _emptyDict():
        empty = dict()
        for i in filter._dictKeys:
            empty[i] = None
        return empty

    @staticmethod
    def parseFilterFromList(data):
        i = 0
        tmp = filter._emptyDict()
        if len(data) > len(filter._dictKeys):
            raise ValueError(f"You can only supply {len(filter._dictKeys)} entries")
        for w in data:
            tmp[filter._dictKeys[i]] = w
            i = i + 1
        return tmp

    # ---------------------------------------------------------------
    # Constructor

    def __init__(self, filterDef, metadata=None):
        """Create a filter instance.

        This constructor instantiates the filter class, creating a
        filter to apply to the DB query. It can be created in one of two
        ways.

        1) By passing a dict with the following keys --
            some are optional:

            colName: The name of the column to filter on

            filter: The filter to apply ('<', '>', 'IS NULL' etc)

            val: The value to apply to the filter, if appropriate. e.g.
                if the filter is '<', val may be 3.1234. If the filter
                takes no arguments (IS [NOT] NULL) this is ignored.
                If the filter takes two arguments (BETWEEN) this should
                be a list.

            combiner: OPTIONAL: This can be AND or OR, if this filter
                has to components.

            filter2: As filter, for the second clause.

            val2: As val, for the second clause.

        2) By passing a list, whose values are the above keys, in order,
           e.g. [
                    'foo',
                    '<',
                    3,
                    'OR',
                    'foo',
                    'BETWEEN',
                    [7,10]
           ]

        Parameters
        ----------

        filterDef :  str or list or tuple
            The filter definition

        metadata : pandas.DataFrame, optional
            Table metadata; used to check filter is valid.

        """
        # The acutal filter is stored in this dict, which starts of with
        # all keys set to None.
        self._data = filter._emptyDict()

        # Parse the constructor into an temp dict, so on fail we leave
        # the original alone.
        tmpdict = filter._emptyDict()

        # If a string was passed, we will parse it.
        if isinstance(filterDef, (list, tuple)):
            filterDef = filter.parseFilterFromList(filterDef)
        elif not isinstance(filterDef, dict):
            raise ValueError("filterDef should be a string or dict.")

        # Now work through keys and try to add.

        # column name
        if "colName" not in filterDef:
            raise ValueError("'colName' is a required key.")
        else:
            tmpdict["colName"] = filterDef["colName"]

        # May have to do this twice, if combiner is set.
        suffs = ("", "2")
        for s in suffs:

            # -------
            # filter
            numArgs = 0
            k = f"filter{s}"
            if k not in filterDef:
                raise ValueError("`{k}` is a required key.")
            else:
                tmp = filterDef[k].upper()
                if tmp not in filter._filters:
                    raise ValueError(f"`{tmp}` is not a valid filter.")
                tmpdict[k] = tmp
                numArgs = filter._filters[tmp]
            # -------
            # Value
            v = f"val{s}"
            if numArgs > 0:
                if v not in filterDef:
                    raise ValueError(f"`{v}` keyword, required for filter `{filterDef[k]}`, not supplied.")

                tmpval = filterDef[v]
                # If a single arg is needed, should be number or text
                if numArgs == 1:
                    if not isinstance(tmpval, (float, int, str)):
                        raise ValueError("`{v}` must be a string, int or float.")
                    tmpdict[v] = tmpval
                # if multiple args should be list/tuple and the right length
                elif not isinstance(tmpval, (list, tuple)):
                    raise ValueError(f"`{v}` must be a list/tuple for filter `{filterDef[k]}`.")
                elif len(tmpval) != numArgs:
                    raise ValueError(f"`{v}` should have {numArgs} elements; you supplied {len(tmpval)}.")
                else:
                    tmpdict[v] = tmpval

            # -------
            # combiner
            if s == "2":
                continue
            if ("combiner" not in filterDef) or (filterDef["combiner"] is None):
                break
            c = filterDef["combiner"].upper()
            if c not in filter._combs:
                raise ValueError(f"`{filterDef['combiner']}` is not a valid combiner value.")
            tmpdict["combiner"] = c

        # OK, parsed all keys, if we made it here we had no error.
        self._data = tmpdict

        # Last thing is to check that we are valid, if metadata was supplied
        if (metadata is not None) and (not self.isValid(metadata)):
            tmp = self._data['colName']
            self._data = None

            raise RuntimeError(f"Cannot create filter, {tmp} is not a valid column.")

    def __repr__(self):
        a = f"A UKSSDC database filter object.\n{self._data}"
        return a

    def __str__(self):
        msg = []
        for i in filter._dictKeys:
            if self._data[i] is None:
                continue
            msg.append(str(self._data[i]))
        return " ".join(msg)

    # ----------------------------------------------------
    # Read-only vars as properties:
    # Results
    @property
    def data(self):
        """The results of the query."""
        return self._data

    def isValid(self, metadata):
        """Check if the filter is valid.

        This receives the metadata for the current catalogue.

        Parameters
        ----------

        metadata : pandas.DataFrame
            The table metadata

        Returns
        -------

        bool
            Whether or not the filter is valid.
        """

        return self._data["colName"] in metadata["ColName"].values
