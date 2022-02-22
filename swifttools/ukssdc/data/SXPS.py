import pandas as pd
from .datarequest_base import dataRequest
from ..access import getSXPSSourceInfo, getSXPSLightCurve, saveSXPSSourceLightCurves, SXPS_LC_BINNING, SXPS_LC_TIMEFORMAT


class SXPSDataRequest(dataRequest):
    """A request to query the SXPS catalogues.

    This inherits from the dataRequest class, providing access to the
    SXPS catalogues; for now, only LSXPS.

    This adds additional functionality, for selecting which SXPS
    catalogue to query and for obtaining more data than is available
    from a simple catalogue query.

    """

    def __init__(self, catalogue="LSXPS", table=None, silent=True, verbose=False):
        super().__init__(silent=silent, verbose=verbose)

        # This constructor is slightly more involved than the basic, because
        # we support multiple catalogues = multiple datasets.
        # This means that I need to list the supported catalogues, and which
        # tables they support.
        # This can be done all in one, by a dict of tablesByCat, where the keys
        # are the catalogues and the
        self._tablesByCat = {
            "LSXPS": [
                "Public_Sources",
                "Public_Datasets",
                "Public_Detections",
                "Public_ObsSources",
                "Public_xCorr",
                "Public_Transients",
                "Public_OldStacks",
            ],
            "2SXPS": [
                "Public_Sources",
                "Public_Datasets",
                "Public_Detections",
                "Public_xCorr",
            ],
        }
        # Also need the default table to select when a catalogue is selected.
        self._defaultTablesByCat = {
            "LSXPS": "Public_Sources",
            "2SXPS": "Public_Sources",
        }

        # A user-friendly hack; allow them to select tables by a more colloquial/natural label
        self._tableLookup = {"sources": "Public_Sources", "datasets": "Public_Datasets"}

        # Now set the selected catalogue to that supplied in the constructor.
        # As whichCat is actually a property dectorator, this will check that
        # the catalogue is valid and sert the tables and default table.
        self.whichCat = catalogue
        if table is not None:
            self.table = table

        self._sourceInfo = None
        self._sourceLightCurves = None
        self._lcbinning = None
        self._lctimeformat = None

    # ----------------------------------------------------------
    # Some properties unique to this class.
    @property
    def whichCat(self):
        """Which SXPS catalogue is to be queried."""
        return self._dbName

    @whichCat.setter
    def whichCat(self, dbName):
        if dbName in self.catalogues:
            self._dbName = dbName
            self._tables = self._tablesByCat[dbName]
            self.table = self._defaultTablesByCat[dbName]
        else:
            raise ValueError(f"{dbName} is not a known database.")

    @property
    def catalogues(self):
        """List of queryable SXPS catalogues."""
        return self._tablesByCat.keys()

    @property
    def sourceInfo(self):
        """Detailed source information."""
        return self._sourceInfo

    @property
    def sourceLightCurves(self):
        """Source light curves."""
        return self._sourceLightCurves

    # Also override the table setter property, so that we can accept
    # short-form table names and correct them.
    @dataRequest.table.setter
    def table(self, table):
        if table.lower() in self._tableLookup:
            table = self._tableLookup[table.lower()]
            if not self.silent:
                print(f"Adjusting table name to `{table}`")
        dataRequest.table.fset(self, table)

    # Work out which new fns or functionality must be added:
    # (Labels on these are not final):
    #
    # getDetails() - for sources/datasets essentially gets all the web page info
    # Something to get products; images, LC, spectra &c
    #   Both of the above need to be able to run for a set of results
    #
    # setSubset() - need to be able to choose clean/ultraclean
    #           EXTRA NOTE: Ideally handle this at the back end, so that
    #             the subset definitions are only defined once. Have to
    #             then incorporate that into website.
    #             IDEA: Function to "get subset" which creates and returns a filter object/list?
    #
    # Upper limit generator.

    # ------------------------------------------------
    # Functions to retrieve information.

    def _handleSourceArgs(self, byName=False, byID=False):
        """Decide whether to query on sourceID or name.

        This is an internal helper function for any function that gets
        products related to a query. It decides whether to send the
        sourceName or ID column with the request, depending first,
        on whether either was explicitly requested, and if not, based
        on which columns have been retrieved.

        Parameters
        ----------

        byName : bool Whether to force use of the source name.
        byID : bool Whether to force use of the source ID

        Return
        ------
        list (whichCol, whichArg)

            whichCol is the name of the column to index on, in the
                returned query.

            whichArg is the name of the argument to send to the API.

        """
        whichCol = None
        whichArg = None

        if byName:
            whichCol = "IAUName"
            whichArg = "sourceName"
            if byID:
                raise RuntimeError("You cannot set byName and byID!")
        elif byID:
            whichCol = f"{self.whichCat}_ID"
            whichArg = "sourceID"
        else:
            cols = {f"{self.whichCat}_ID": "sourceID", "IAUName": "sourceName"}

            for c, n in cols.items():
                if c in self.results.columns:
                    whichCol = c
                    whichArg = n
                    break
            if whichCol is None:
                raise RuntimeError(f"Cannot get source info, as none of the columns: {cols} are in your results.")

        if whichCol not in self.results.columns:
            raise RuntimeError(f"Cannot get source info, as the column `{whichCol}` is not in your results.")

        return (whichCol, whichArg)

    def getSourceInfo(self, subset=None, byName=False, byID=False, returnData=False):
        """Get the full set of information for retrieved sources.

        This function is primarily a wrapper to the function
        swifttools.ukssdc.access.getSXPSSourceInfo; calling that
        function for the source(s) which this query object has returned.
        For obvious reasons, it will fail if you have not yet executed
        the query.

        The retrieved information will be saved in the "sourceInfo"
        variable of this object; it will also be returned by this
        function call if returnedData=True

        Left alone, this will get the details for all sources your query
        identified, and index them by SXPS ID (if that was retrieved),
        or IAUName if the ID was not retrieved. If neither column was
        retrieved, expect an error.

        The subset parameter is optional, and can be used to apply
        a filter to the results this query has obtained. The easiest way
        to generate this is using the pandas syntax for filtering on
        value.

        e.g. if your datarequest object is called 'req' then:

        => req.getSourceInfo(subset=req.results['Err90']<5)

        would get details of all of the sources in your result, with
        Err90 values <5.

        Parameters
        ----------

        subset : pandas.Series OPTIONAL: A pandas series defining a
            subset of rows to download.

        byName : bool Force the results to be indexed by IAUName.
            Requires that column to have been retrieved by your query.

        byID : bool Force the results to be indexed by SXPS_ID.
            Requires that column to have been retrieved by your query.

        returnData : bool Whether to return the data, as well as storing
            it in the "sourceInfo" variable.


        """

        if not self.haveResults:
            raise RuntimeError("This query has not been executed, cannot download!")

        # Check if we are doing ID or name.
        data = {}
        (whichCol, whichArg) = self._handleSourceArgs(byName=byName, byID=byID)

        # Now set up data, which will will pass as **data which will be received either as
        # sourceID = [...] or sourceName = [...]
        data[whichArg] = []

        # But before we can populate it, we may have to handle a subset:
        if subset is not None:
            if not isinstance(subset, pd.core.series.Series):
                raise ValueError("Subset parameter must be a pandas series")
            data[whichArg] = self._results.loc[subset][whichCol].tolist()
        else:
            data[whichArg] = self._results[whichCol].tolist()

        self._sourceInfo = getSXPSSourceInfo(catalogue=self.whichCat, silent=self.silent, verbose=self.verbose, **data)
        if not self.silent:
            print("Saved source information as sourceInfo varable.")
        if returnData:
            return self._sourceInfo

    def getDatasetInfo(self, **kwargs):
        pass

    def getInfo(self, **kwargs):
        """A wrapper to call the appropriate function."""
        if self.table == "Public_Sources":
            self.getSourceInfo(**kwargs)
        elif self.table == "Public_Datasets":
            self.getDatasetInfo(**kwargs)
        else:
            raise NotImplementedError

    # ------------------------------------------------
    # Functions to retrieve products

    def getLightCurves(
        self, subset=None, byName=False, byID=False, bands="all", binning=None, timeFormat=None, returnData=False, **kwargs
    ):
        """Get the full set of information for retrieved sources.

        This function is primarily a wrapper to the function
        swifttools.ukssdc.access.getSXPSLightCurve; calling that
        function for the source(s) which this query object has returned.
        For obvious reasons, it will fail if you have not yet executed
        the query.

        Left alone, this will get the details for all sources your query
        identified, and index them by SXPS ID (if that was retrieved),
        or IAUName if the ID was not retrieved. If neither column was
        retrieved, expect an error.

        The subset parameter is optional, and can be used to apply
        a filter to the results this query has obtained. The easiest way
        to generate this is using the pandas syntax for filtering on
        value.

        e.g. if your datarequest object is called 'req' then:

        => req.getSourceInfo(subset=req.results['Err90']<5)

        would get details of all of the sources in your result, with
        Err90 values <5.


        The light curves returned are stored in the "sourceLightCurves"
        variable of this object, and optionally returned. For their
        format see the help for
        swifttools.ukssdc.access.getSXPSSourceInfo.

        Parameters
        ----------

        subset : pandas.Series OPTIONAL: A pandas series defining a
            subset of rows to download.

        byName : bool Force the results to be indexed by IAUName.
            Requires that column to have been retrieved by your query.

        byID : bool Force the results to be indexed by SXPS_ID.
            Requires that column to have been retrieved by your query.

        bands : Union(str,list): Either 'all', or a list of labels of
            the energy bands to retrieve ('total', 'soft', 'medium',
            'hard', 'HR1', 'HR2')

        binning : str Which of the two binning methods you want: either
            'observation' or 'snapshot'

        timeFormat : str Which units to use for the time axis. Must be
            'met' or 'tdb' or 'mjd'.

        returnData : bool Whether the light curve data should be
            returned by this function, as well as saved in the
            "sourceLightCurves" variable.

        **kwargs : dict Other arguments which are passed to:
             swifttools.ukssdc.access.getSXPSSourceInfo.
             See its help for more information.

        """

        if not self.haveResults:
            raise RuntimeError("This query has not been executed, cannot download!")

        # Check if we are doing ID or name.
        data = {}
        (whichCol, whichArg) = self._handleSourceArgs(byName=byName, byID=byID)

        # Now set up data, which will will pass as **data which will be received either as
        # sourceID = [...] or sourceName = [...]
        data[whichArg] = []

        # But before we can populate it, we may have to handle a subset:
        if subset is not None:
            if not isinstance(subset, pd.core.series.Series):
                raise ValueError("Subset parameter must be a pandas series")
            data[whichArg] = self._results.loc[subset][whichCol].tolist()
        else:
            data[whichArg] = self._results[whichCol].tolist()

        # If we already have light curves, then we have to make sure
        # that the binning and timeformat match. If none were supplied then
        # we will set them to what was got before.
        if binning is not None:
            binning = binning.lower()
            if binning not in SXPS_LC_BINNING:
                raise ValueError(f"{binning} is not an acceptable binning method.")
            binning = SXPS_LC_BINNING[binning]

        if timeFormat is not None:
            timeFormat = timeFormat.lower()
            if timeFormat not in SXPS_LC_TIMEFORMAT:
                raise ValueError(f"{timeFormat} is not an acceptable time system.")
            timeFormat = SXPS_LC_TIMEFORMAT[timeFormat]

        if self._sourceLightCurves is not None:
            if binning is None:
                binning = self._lcbinning
            if timeFormat is None:
                timeFormat = self._lctimeformat
            if (binning != self._lcbinning) or (timeFormat != self._lctimeformat):
                print(f"ARSE: Binning: {binning} vs {self._lcbinning}")
                print(f"ARSE: TimeFormat: {timeFormat} vs {self._lctimeformat}")
                raise ValueError("Cannot get more light curves with different binning / timeformat.")

        tmp = getSXPSLightCurve(
            catalogue=self.whichCat,
            silent=self.silent,
            verbose=self.verbose,
            bands=bands,
            binning=binning,
            timeFormat=timeFormat,
            **data,
            **kwargs,
        )

        if self._sourceLightCurves is None:
            self._sourceLightCurves = tmp
        else:
            # Can't just merge the dicts, annoyingly, because this is not a deep (recursive) merge, so will not
            # add extra bands. However, I don't need a full recurse, just at the source level, so it's not too hard.
            for i in tmp.keys():
                if i in self._sourceLightCurves:
                    tmpDS = self._sourceLightCurves[i]["datasets"]
                    tmpDS.extend(x for x in tmp[i]["datasets"] if x not in tmpDS)
                    self._sourceLightCurves[i].update(tmp[i])
                    # self._sourceLightCurves[i] = {**self._sourceLightCurves[i], **tmp[i]}
                    self._sourceLightCurves[i]["datasets"] = tmpDS
                else:
                    self._sourceLightCurves[i] = tmp[i]

        # Now get the binning and timeformat, assuming any exist
        tmp = list(self._sourceLightCurves.keys())
        firstLC = tmp[0]
        if "Binning" in self._sourceLightCurves[firstLC]:
            self._lcbinning = self._sourceLightCurves[firstLC]["Binning"]
        if "TimeFormat" in self._sourceLightCurves[firstLC]:
            self._lctimeformat = self._sourceLightCurves[firstLC]["TimeFormat"]

        if returnData:
            return self._sourceLightCurves

    def saveLightCurves(self, **kwargs):
        """Save the light curves to text files.

        This function is used to save the light curves that have been
        downloaded and are stored in the self.sourceLightCurves
        variable of this SXPSDataRequest object. These light curves
        can be saved as simple text file (with a user-settable
        column separator), or as files formatted for the qdp programme.

        All this function actually does it to call the
        saveSXPSSourceLightCurves() in the related module:
        swifttools.ukssdc.access; further detail on the parameters that
        can be used are documented for that function.

        Parameters
        ----------

        **kwargs : dict A set of parameters to pass to the main save
            function in swifttools.ukssdc.access

        """
        # Check that we have downloaded some light curves!
        if self.sourceLightCurves is None:
            raise RuntimeError("There are no light curves to save!")
        saveSXPSSourceLightCurves(self.sourceLightCurves, silent=self.silent, verbose=self.verbose, **kwargs)

    def clearSourceLightCurves(self):
        """Forget all source light curves."""
        self._sourceLightCurves = None
        self._lcbinning = None
        self._lctimeformat = None
