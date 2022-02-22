# import json
from . import allowedConeRadiusUnits
from .. import main as base
from ..access import downloadObsData
import pandas as pd
from .DBFilter import filter

if base.HAS_ASTROPY:
    import astropy.coordinates


# allowedConeRadiusUnits = ("arcsec", "arcmin", "degree", "deg")
class dataRequest:
    """The base case for UKSSDC data requests. A 'virtual' class.

    This class should never in itself be instantiated, only those
    dervied from it. In fact, it will contain enough functionality to
    run for the most basic of cases, except that it will never select
    which table / catalogue is being searched.

    MORE DOCS - maybe give a summary of the methods here.
    """

    def __init__(self, silent=True, verbose=False):
        """Create a dataRequest instance.

        Parameters
        ----------
        silent : bool Whether to suppress all console output
               (default: True).

        verbose : bool Whether to give verbose output for everything
                   (default: False; overridden by silent).

        """

        # This 'abstract' class has no table defined.
        self._dbName = None
        self._table = None
        self._silent = silent
        self._verbose = verbose
        self._metadata = None
        self._colsToGet = None
        self._defaultCols = None
        self._defaultColSets = None
        self._tables = []
        self._coneRA = None
        self._coneDec = None
        self._coneName = None
        self._coneRadius = None
        self._coneUnits = "arcsec"
        self._doConeSearch = False
        self._filters = []
        self._sortCol = None
        self._sortDir = "ASC"
        self._results = None
        # numRows and firstRows, if None, means no limits
        self._maxRows = 5000
        self._firstRow = None
        self._numRows = None
        self._resolverDetails = None
        self._resolvedRA = None
        self._resolvedDec = None
        self._locked = False
        self._raw = None  # DEBUG PROPERTY, DELETE LATER
        self._obsCol = None
        self._targetCol = None

        if self._verbose:
            self._silent = False
            print("Disabling silent mode, verbose mode was requested.")

    # End of __init__

    # -----------------------------------------------------------------
    # Now set up variable access, via properties to control read/write
    # etc.

    # Silent
    @property
    def silent(self):
        """Whether to suppress output."""
        return self._silent

    @silent.setter
    def silent(self, silent):
        if not isinstance(silent, bool):
            raise ValueError("Silent must be a bool")
        self._silent = silent

    # Verbose
    @property
    def verbose(self):
        """Whether to write extra output."""
        return self._verbose

    @verbose.setter
    def verbose(self, verbose):
        if not isinstance(verbose, bool):
            raise ValueError("Verbose must be a bool")
        self._verbose = verbose

    # make setting table unimplemented here, allowing the subclasses to
    # decide whether you can change table mid query; also some classes
    # may only support one table so they would want these functions not
    # to work (i.e. set self._table in constructor.
    # table
    @property
    def table(self):
        return self._table

    @table.setter
    def table(self, table):
        self.checkLock()
        if table not in self._tables:
            raise ValueError(f"{table} is not a valid table. The list `tables` shows valid values.")
        self._table = table
        self._metadata = None
        # if (self._defaultColSets is not None) and table in (self._defaultColSets):
        #     self._defaultCols = self._defaultColSets[table]
        # If unlocking the table, we have to forget results as various results handling functions are tied to the table
        # that was used.
        self.reset()
        if self.verbose:
            print(f"Selecting table `{table}`")

    # dbName is also unset here, may not be changeable depending on sub-class.
    # dbName
    @property
    def dbName(self):
        """Which database is to be queried."""
        if self._dbName is None:
            raise NotImplementedError
        return self._dbName

    @dbName.setter
    def dbName(self, dbName):
        raise NotImplementedError

    # coneRA
    @property
    def coneRA(self):
        """The RA on which to centre a cone search (J2000)."""
        return self._coneRA

    @coneRA.setter
    def coneRA(self, RA):
        self.checkLock()
        gotRA = False
        if base.HAS_ASTROPY:
            if isinstance(RA, astropy.coordinates.Angle):
                RA = float(RA.deg)
                gotRA = True
            elif isinstance(RA, str):
                tmp = astropy.coordinates.Angle(RA)
                RA = float(tmp.deg)
                gotRA = True
        # If we don't have astropy, or it wasn't something astropy has
        # parsed, then it must be int or float and we will parse it
        if not gotRA:
            if not isinstance(RA, (int, float)):
                raise ValueError("RA must be int or float")
            self._coneRA = float(RA)

    # coneDEC
    @property
    def coneDec(self):
        """The Dec on which to centre a cone search (J2000)."""
        return self._coneDec

    @coneDec.setter
    def coneDec(self, Dec):
        self.checkLock()
        gotDec = False
        if base.HAS_ASTROPY:
            if isinstance(Dec, astropy.coordinates.Angle):
                Dec = float(Dec.deg)
                gotDec = True
            elif isinstance(Dec, str):
                tmp = astropy.coordinates.Angle(Dec)
                Dec = float(tmp.deg)
                gotDec = True
        # If we don't have astropy, or it wasn't something astropy has
        # parsed, then it must be int or float and we will parse it
        if not gotDec:
            if not isinstance(Dec, (int, float)):
                raise ValueError("Dec must be int or float")
            self._coneDec = float(Dec)

    # coneName
    @property
    def coneName(self):
        """The name of the object on which to centre a cone search."""
        return self._coneName

    @coneName.setter
    def coneName(self, name):
        self.checkLock()
        if not isinstance(name, str):
            raise ValueError("Name must be a string")
        self._coneName = name

    # coneRadius
    @property
    def coneRadius(self):
        """The Radius on which to centre a cone search."""
        return self._coneRadius

    @coneRadius.setter
    def coneRadius(self, Radius, Units=None):
        self.checkLock()
        if not isinstance(Radius, (int, float)):
            raise ValueError("Radius must be int or float")
        self._coneRadius = float(Radius)
        if Units is not None:
            self.coneUnits = Units

    # coneUnits
    @property
    def coneUnits(self):
        """The units of the cone-search radius."""
        return self._coneUnits

    @coneUnits.setter
    def coneUnits(self, Units):
        self.checkLock()
        if not isinstance(Units, str):
            raise ValueError(f"Units must be a string, one of: {', '.join(allowedConeRadiusUnits)}")
        if Units in allowedConeRadiusUnits:
            self._coneUnits = Units
        else:
            raise ValueError(f"Units must be one of: {', '.join(allowedConeRadiusUnits)}")

    # maxRows
    @property
    def maxRows(self):
        """How many rows to retrieve. None=all."""
        self.checkLock()
        return self._maxRows

    @maxRows.setter
    def maxRows(self, num):
        if not isinstance(num, (int, float)) and (num is not None):
            raise ValueError("num must be a number or None")
        self._maxRows = num

    # firstRow
    @property
    def firstRow(self):
        """The first row to retrieve. None=auto."""
        return self._firstRow

    @firstRow.setter
    def firstRow(self, num):
        self.checkLock()
        if (not isinstance(num, (int, float))) and (num is not None):
            raise ValueError("num must be a number or None")
        self._firstRow = num

    # ---------------------------
    # And some which we want to be read-only when accessed as a variable.

    # doConeSearch
    @property
    def doConeSearch(self):
        """Whether a cone search will be done."""
        return self._doConeSearch

    # allowedConeRadiusUnits
    @property
    def allowedConeRadiusUnits(self):
        """The allowedConeRadiusUnits for with the selected table. Read-only."""
        return allowedConeRadiusUnits

    # metadata
    @property
    def metadata(self):
        """The metadata for with the selected table. Read-only."""
        # Need to get metadata if we don't have it:
        if self._metadata is None:
            if not self.silent:
                print("Need to get the metadata.")
            self.getMetadata()

        return self._metadata

    # colsToGet
    @property
    def colsToGet(self):
        """The columns selected for retrieval."""
        return self._colsToGet

    # filters
    @property
    def filters(self):
        """The filters that will be applied."""
        return self._filters

    # Results
    @property
    def results(self):
        """The results of the query."""
        return self._results

    # haveResults
    @property
    def haveResults(self):
        """Whether we have results from this query."""
        return self._results is not None

    @property
    def locked(self):
        """Is this object locked?"""
        return self._locked

    @property
    def numRows(self):
        """The number of rows returned by the query."""
        return self._numRows

    @property
    def resolverDetails(self):
        """The ouput of the name resolver."""
        return self._resolverDetails

    @property
    def resolvedRA(self):
        """The RA returned by the name resolver."""
        return self._resolvedRA

    @property
    def resolvedDec(self):
        """The dec returned by the name resolver."""
        return self._resolvedDec

    @property
    def tables(self):
        """The tables that can be selected."""
        return self._tables

    @property
    def defaultCols(self):
        """The columns that are retrieved if no selection is created."""

        if self._defaultCols is None:
            # self._checkMetaData()
            if "Class" in self.metadata.columns:
                # Can do this all in one line, but it's a bit hard to read, so lets be nice:
                # First, filter the metadata on cases where Class has "BASIC" in it
                tmp = self.metadata.loc[self.metadata["Class"].str.contains("BASIC")]
                # Now get the columns in this:
                self._defaultCols = tmp["ColName"].tolist()

        return self._defaultCols

    @property
    def cols(self):
        """Columns in this table."""
        return self.metadata["ColName"].values

    @property
    def obsColumn(self):
        """Which column contains the observation identifier."""
        return self._obsCol

    @property
    def targetColumn(self):
        """Which column contains the target identifier."""
        return self._targetCol

    # ---------------------------------------------------------------
    # Functions. First some standard things:

    def __str__(self):
        str = f"PRINTING AN {type(self)} object."
        return str

    def __repr__(self):
        str = f"I AM AN {type(self)} object."
        return str

    def checkLock(self):
        """Check if this object is locked."""
        if self._locked:
            raise RuntimeError("Cannot edit this request as it is locked.")

    def unlock(self):
        """Unlock the object for editing."""
        self._locked = False

    # ---------------------------------------------------------------
    # Metadata
    def getMetadata(self):
        """Retrieve the metadata for this catalogue from the server.

        This queries the server for the metadata associated with the
        database/table of the current object, and saves it into the
        metadata variable as a pandas object? Or a dict? TBC

        """
        self.checkLock()
        sendData = {"database": self.dbName, "table": self.table}
        if self.verbose:
            print(f"Getting metadata for {self.dbName}.{self.table}")

        ret = base.submitAPICall("getMetadata", sendData, minKeys=["metadata"], verbose=self._verbose)

        # metadata should have two entries: 'columns' and 'data'
        self._metadata = pd.DataFrame(ret["metadata"]["metadata"], columns=ret["metadata"]["columns"])

        self._obsCol = None
        self._targetCol = None
        if "IsObsCol" in self._metadata:
            self._metadata["IsObsCol"] = pd.to_numeric(self._metadata["IsObsCol"])
            tmp = self._metadata.loc[self._metadata["IsObsCol"] == 1]["ColName"]
            if len(tmp) > 0:
                self._obsCol = tmp.iloc[0]
                if len(tmp) > 1 and not self.silent:
                    print(
                        "WARNING: Metadata contains TWO obs columns! This may be a bug; "
                        "please notify swift-help@leicester.ac.uk"
                    )

        if "IsTargetCol" in self._metadata:
            self._metadata["IsTargetCol"] = pd.to_numeric(self._metadata["IsTargetCol"])
            tmp = self._metadata.loc[self._metadata["IsTargetCol"] == 1]["ColName"]
            if len(tmp) > 0:
                self._targetCol = tmp.iloc[0]
                if len(tmp) > 1 and not self.silent:
                    print(
                        "WARNING: Metadata contains TWO target columns! This may be a bug; "
                        "please notify swift-help@leicester.ac.uk"
                    )

    # --------------------------------------------------------------
    # Misc
    def reset(self):
        """Remove all results - reset this object."""

        if not self.silent:
            print("Resetting query details")
        self.unlock()
        self.removeAllFilters()
        self.removeConeSearch()
        self._colsToGet = None
        self._resolverDetails = None
        self._resolvedRA = None
        self._resolvedDec = None
        self._results = None
        self.sortCol = None
        self._metadata = None
        self._defaultCols = None

        self._raw = None  # TEMP LINE

    # ---------------------------------------------------------------
    # Cone search functions
    # These allow a cone search to be build, or requested.
    # Note that simply setting coneRA/Dec above on their own doesn't force
    # a cone search to run unless doConeSearch is set. These methods are
    # preferred ways of managing the cone search.

    def addConeSearch(self, ra=None, dec=None, radius=None, name=None, coords=None, units="arcsec"):
        """Include a cone search filter on the dataRequest.

        This function adds a cone search to the set of filters to be
        applied to your request. If a cone serach already existed, this
        will overwrite it; you cannot (at present) have multiple cone
        searches combined with an OR function; you will have to do
        multiple cone searches instead.

        Note: name, or ra & dec must be specified, but they cannot
        both be specified. If you supply both, an error will be raised.

        Parameters
        ----------
        ra : Union[float, astropy.coordiantes.Angle] Central RA
            of the cone, in J2000.

        dec : Union[float, astropy.coordiantes.Angle] Central Dec
            of the cone, in J2000.

        name: str The name of an object to centre on. Will be resolved.

        coords : str Free-form coordinates to attempt to parse

        radius : float Radius of the cone search.

        units : str The units of coneRadius. Default 'arcsec', permitted
            values are given in the allowedConeRadiusUnits variable.

        """
        self.checkLock()
        # Set mainly via @property functions so that checks on values are done.
        if name is not None:
            if (ra is not None) or (dec is not None) or (coords is not None):
                raise ValueError("You must supply name OR position, not both.")
            self._coneRA = None
            self._coneDec = None
            self.coneName = name
        elif coords is not None:
            self.coneName = coords
        elif (ra is None) or (dec is None):
            raise ValueError("You must supply name or position.")
        else:
            self.coneRA = ra
            self.coneDec = dec
            self._coneName = None

        if radius is None:
            raise ValueError("radius must be supplied")

        self.coneRadius = radius
        self.coneUnits = units

        self._doConeSearch = True

    def editConeSearch(self, coneRA, coneDec, coneRadius, coneUnits="arcsec"):
        """Changes the cone search. Just a wrapper to addConeSearch."""
        self.addConeSearch(coneRA, coneDec, coneRadius, coneUnits)

    def removeConeSearch(self):
        """Remove the cone search from the filters to apply."""
        self.checkLock()
        self._coneRA = None
        self._coneDec = None
        self._coneRadius = None
        self._coneUnits = "arcsec"
        self._doConeSearch = False

    def isValid(self):
        """Whether the current request is valid and can be submitted."""

        # Need to get metadata if we don't have it:
        if self._metadata is None:
            if not self.silent:
                print("Need to get the metadata to check the query is valid.")
            self.getMetadata()

        # This needs to check:
        # All columns are permissable
        # If not set, check defaults as user could have been naughty.
        if self.verbose:
            print("Checking requested columns...")
        tmp = self._colsToGet
        if tmp is None:
            tmp = self.defaultCols
            if tmp is None:
                print("No columns selected to retrieve!")
                return False
        if tmp != "*":
            for c in tmp:
                if c not in self.metadata["ColName"].values:
                    if not self.silent:
                        print(f"Requested column {c} does not exist.")
                    return False

        # Now check filters
        # Filters
        if self.verbose:
            print("Checking filters...")
        for f in self._filters:
            if not f.isValid(self.metadata):
                return False

        # And check the cone search
        if self._doConeSearch:
            if self.verbose:
                print("Checking cone search parameters...")
            # Need a radius
            if self.coneRadius is None:
                if not self.silent:
                    print("A cone search is selected, but radius is not set")
                return False
            # Need name or ra AND dec
            if (self.coneName is None) and ((self.coneRA is None) or (self.coneDec is None)):
                if not self.silent:
                    print("A cone search is selected, but neither name, nor RA & Dec are set.")
                return False
            if (self.coneName is not None) and ((self.coneRA is not None) or (self.coneDec is not None)):
                if not self.silent:
                    print("You should supply name OR position for a cone search.")
                return False

        return True

    # ---------------------------------------------------------------
    # Column functions

    def _addCol(self, colName):
        """Internal function to add a column to the list.

        This is called by addCol() (which can support strings or lists)
        but must recieve a string. It adds the item to _colsToGet, after
        verifying it.

        The table metadata must be known, so it will retrieve it if it
        doesn't exist.

        Will raise ValueError if the supplied parameter is not a string,
        or is not a valid column (or '*').

        Parameters
        ----------

            colName : str  The column to add.

        """
        self.checkLock()
        # First, check whether the metadata is retrieved and up to date.
        if not isinstance(colName, str):
            raise ValueError("colName should be a string")

        if colName == "*":
            if self.verbose:
                print("Setting to retrieve all columns.")
            self._colsToGet = self.metadata["ColName"].values.tolist()
        else:
            # Is the column name valid?
            if colName not in self.metadata["ColName"].values:
                raise ValueError(f"`{colName}` is not a valid column name.")
            # If previously we had selected all, then warn if not silent.
            if self._colsToGet == "*":
                if not self.silent:
                    print("WARNING: previously you were selecting all data; you are now requesting specific columns.")
                self._colsToGet = [
                    colName,
                ]

            # If this is the first column, create the list
            if self._colsToGet is None:
                self._colsToGet = [
                    colName,
                ]
                if self.verbose:
                    print(f"Will retrieve column {colName}")
            else:
                # This 'else' assumes a list, i.e. colsToGet is either '*', None or a list.
                # If it is not, then likely this will throw an error. That's OK, since if it is
                # not one of these then a user has edited this "hidden" field directly, and they
                # deserve what they get.
                if colName in self._colsToGet:
                    if not self.silent:
                        print(f"Cannot add column {colName}; it is already selected.")
                else:
                    self._colsToGet.append(colName)
                    if self.verbose:
                        print(f"Will retrieve column {colName}")

    def addCol(self, colName):
        """Add a column/columns to the list of those to retrieve.

        This can receive either a string, which is a column name or '*',
        or a list of column names to add to the list to retrieve.
        Note: '*' cannot appear in a list.

        The names are checked against valid column names, so if it has
        not already been called, getMetadata() will run first.

        Parameters
        ----------

            colName : Union[str,list]  The column(s) to add.

        """
        self.checkLock()
        if isinstance(colName, str):
            self._addCol(colName)
        elif isinstance(colName, (list, tuple)):
            if "*" in colName:
                raise ValueError("You cannot include '*' in a list of columns.")
            for c in colName:
                self._addCol(c)
        else:
            raise ValueError("colName must be a string or list")

        if self.verbose:
            print(f"Set to retrieve columns: {self._colsToGet}")

    def removeAllCols(self):
        """Empty the list of defined columns to retrieve."""
        self.checkLock()
        self._colsToGet = None

    def _removeCol(self, colName):
        """Internal function to remove a column from the list.

        This is called by removeCol() (which supports strings or lists)
        but must recieve a string. It removes the item to _colsToGet.

        Parameters
        ----------

            colName : str  The column to remove.

        """
        self.checkLock()
        if not isinstance(colName, str):
            raise ValueError("colName should be a string")

        self.colsToGet.remove(colName)

    def removeCol(self, colName):
        """Remove a column/columns to the list of those to retrieve.

        This can receive either a string, which is a column name or a
        list of column names to add to the list to retrieve.

        Parameters
        ----------

            colName : Union[str,list]  The column(s) to add.

        """
        self.checkLock()
        if isinstance(colName, str):
            self._removeCol(colName)
        elif isinstance(colName, (list, tuple)):
            for c in colName:
                self._removeCol(c)
        else:
            raise ValueError("colName must be a string or list")

        if len(self._colsToGet) == 0:
            self._colsToGet = None

        if self.verbose:
            print(f"Will retrieve columns: {self._colsToGet}")

    # ----------------------
    # Filter functions

    # addFilter
    # editFilter
    # removeFilter
    # showFilters (maybe with option for 'as SQL' vs as Dict)

    def removeAllFilters(self):
        """Remove all defined search filters."""
        self.checkLock()
        self._filters = []

    def addFilter(self, filterDef):
        """Add a filter to the query.

        This can be done two ways:

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

        filterDef : Union[string,list,tuple] The filter definition

        """
        self.checkLock()
        # colname is 
        self._filters.append(filter(filterDef, self.metadata))

    def showFilters(self):
        """List all filters currently applied"""
        i = 0
        for f in self._filters:
            print(f"{i}:\t{f}")
            i = i + 1

    def removeFilter(self, ix):
        """Remove a filter, by index.

        To see filters and their indices, call showFilters

        Parameters
        ----------

        ix : int    Index of filter to remove

        """
        self.checkLock()
        if not isinstance(ix, int):
            raise ValueError("ix must be an int")
        if (ix < 0) or (ix >= len(self._filters)):
            raise ValueError(f"ix must be between 0 and {len(self._filters)-1}")
        del self._filters[ix]
        if not self._silent:
            self.showFilters()

    # ---------------------------------------------------------------
    # Actual search functions

    def submit(self):
        """Submit the query."""
        self.checkLock()

        # First, check validity. Do this by function call
        if not self.isValid():
            if not self.silent:
                print("Cannot submit query - it is not valid.")
            return False

        # Build the API request dict:
        sendData = {
            "database": self.dbName,
            "table": self.table,
            "adUnits": self._coneUnits,
            "sortDir": self._sortDir,
            "numRows": base.MAXROWS,
        }

        # Specify columns, if we can
        if self._colsToGet is not None:
            sendData["cols"] = self._colsToGet
        elif self.defaultCols is not None:
            sendData["cols"] = self.defaultCols

        # And the sort Col:
        if self._sortCol is not None:
            sendData["sortBy"] = self._sortCol

        # Add filters
        if len(self._filters) > 0:
            sendData["constraints"] = []
            for f in self._filters:
                sendData["constraints"].append(f.data)

        # Add cone information
        if self._doConeSearch:
            if self._coneName is None:
                if (self._coneRA is None) or (self._coneDec is None):
                    raise RuntimeError("You have requested a cone search but without specifying name/position")
                sendData["searchRA"] = self._coneRA
                sendData["searchDec"] = self._coneDec
                # print("SETTING CONE BY POSITION")
            else:
                sendData["searchName"] = self._coneName
                # print("SETTING CONE BY NAME")

            sendData["searchRad"] = self._coneRadius

        # Now do the actual work. Note - the server can only return so
        # many rows at once because of memory constraints. I will limit
        # the max in one go to base.MAXROWS. NB, if you try to return
        # more than this and the allocated memory is overrun you just
        # get a 500 error.

        fR = 0  # First row from this query
        if self._firstRow is not None:
            fR = int(self._firstRow)

        maxRows = 1e80  # i.e. BIG
        if self._maxRows is not None:
            maxRows = int(self._maxRows)
            # If we want < the maximum in one go, need to ammend numRows
            if maxRows < base.MAXROWS:
                sendData["numRows"] = maxRows

        # Create a local variable for the result for now, I don't want
        # to update self._results until the query has definitely succeeded.
        result = None

        done = False
        while not done:
            # Update the first row to get
            sendData["firstRow"] = fR

            if not self._silent:
                print(f"Calling DB look-up for rows {fR} -- {sendData['numRows']+fR}")

            ret = base.submitAPICall(
                "queryDB",
                sendData,
                minKeys=["Results", "NumRows"],
                verbose=self._verbose,
            )
            if result is None:
                result = ret
            else:
                result["NumRows"] = result["NumRows"] + ret["NumRows"]
                result["Results"].extend(ret["Results"])

            # Are we done? If we did not get as many rows as was requested then we are
            if ret["NumRows"] < sendData["numRows"]:
                done = True
                if self._verbose:
                    print(f"Received {ret['NumRows']} rows / {sendData['numRows']} requested. Query complete.")
            # If we have now hit the user-set limit, then we are done:
            elif (self._maxRows is not None) and (result["NumRows"] >= self._maxRows):
                done = True
                if self._verbose:
                    print(f"{result['NumRows']} rows retrieved in total. Query complete.")
            else:
                # Increase the start row for the next call
                fR = fR + sendData["numRows"]
                # We may need to decrease the number of rows
                if (self._maxRows is not None) and (self._maxRows < result["NumRows"] + sendData["numRows"]):
                    sendData["numRows"] = self._maxRows - result["NumRows"]
                    if self._verbose:
                        print(f"Reducing the number of rows requested to {sendData['numRows']}.")
        # End of while not Done
        # We now should have our results. Maybe do one sanity check:
        if result["NumRows"] != len(result["Results"]):
            raise RuntimeError(f"Should have {result['NumRows']} rows, but have {len(result['Results'])}!")

        if (self._doConeSearch) and (not self.silent) and ("ResolvedInfo" in result):
            print(result["ResolvedInfo"])

        self._numRows = result["NumRows"]
        if (self._doConeSearch) and ("ResolvedInfo" in result):
            self._resolverDetails = result["ResolvedInfo"]
            self._resolvedRA = result["ResolvedRA"]
            self._resolvedDec = result["ResolvedDec"]
        self._results = pd.DataFrame(result["Results"])

        useAst = None
        if base.HAS_ASTROPY:
            useAst = "_apy"
        if not self.silent:
            print(f"Received {self.numRows} rows.")
        base.manageResults(self._results, self._metadata, "_s", useAst, self.silent, self.verbose)
        self._locked = True

        self._raw = result  # TEMPORARY LINE

    # ---------------------------------------------------------------
    # Data retrieval

    def downloadObsData(self, subset=None, **kwargs):
        """Download data for the observations returned by the query.

        If the excuted query returned a column which includes
        observation identifiers, then this function will download the
        data for those columns. This function essentially wraps
        ukssdc.access.downloadObsData(), so for valid values of the
        **kwargs, see the documentation for that function.

        The subset parameter is optional, and can be used to apply
        a filter to the results this query has obtained. The easiest way
        to generate this is using the pandas syntax for filtering on
        value.

        e.g. if your datarequest object is called 'req' then:

        => req.downloadObsData(subset=req.results['xrt_expo_pc']<1000)

        would request a download of all observations that the request
        found, which had a value of less than 1000 in the 'xrt_expo_pc'
        column.

        Obviously, this function cannot be called before this request
        has been submitted and has completed; if you try, your computer
        will explode and your eyeballs will be eaten by ants (just
        kidding; you'll get a RuntimeError).

        Parameters
        ----------

        subset : pandas.Series OPTIONAL: A pandas series defining a
            subset of rows to download.

        """

        if not self.haveResults:
            raise RuntimeError("This query has not been executed, cannot download!")

        if self._obsCol is None:
            raise RuntimeError("These is no column containing observation ID, cannot download.")

        if self._obsCol not in self.results.columns:
            raise RuntimeError(
                f"The column {self._obsCol} was not retrieved as part of your query. Cannot download. "
                "You may need to unlock this object, add {self._obsCol} to those to retrieve, and repeat the query."
            )

        obslist = []
        if subset is not None:
            if not isinstance(subset, pd.core.series.Series):
                raise ValueError("Subset parameter must be a pandas series")
            obslist = self._results.loc[subset][self._obsCol].tolist()
        else:
            obslist = self.results[self._obsCol].tolist()

        # # DEBUG LINE:
        # print(f"Downloading obs: {obslist}")
        # return

        downloadObsData(obslist, silent=self.silent, verbose=self.verbose, **kwargs)

    