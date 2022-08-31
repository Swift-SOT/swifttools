"""File with the for the SXPSQuery class.

"""
__docformat__ = "restructedtext en"

import pandas as pd
from .dataquery_base import dataQuery
from ..data import SXPS as dcat
from .. import plotLightCurve as lcPlot


class SXPSQuery(dataQuery):
    """A request to query the SXPS catalogues.

    This inherits from the dataQuery class, providing access to the
    SXPS catalogues; 2SXPS and LSXPS.

    This adds additional functionality, for selecting which SXPS
    catalogue to query and for obtaining more data than is available
    from a simple catalogue query.

    """

    def __init__(self, cat="LSXPS", table=None, silent=True, verbose=False):
        super().__init__(silent=silent, verbose=verbose)
        """Create an SXPSQuery instance.

        Parameters
        ----------

        cat : str, optional
            Which SXPS catalogue to base this query on
            (default: 'LSXPS').

        table : str or ``None``
            Which table to base the query on. If ``None``, uses the
            catalogue default.

        silent : bool
            Whether to suppress all console output (default: ``True``).

        verbose : bool
            Whether to give verbose output for everything
            (default: False; overridden by ``silent``).

        """

        # This constructor is slightly more involved than the basic, because
        # we support multiple catalogues = multiple datasets.
        # This means that I need to list the supported catalogues, and which
        # tables they support.
        # This can be done all in one, by a dict of tablesByCat, where the keys
        # are the catalogues and the
        self._tablesByCat = {
            "LSXPS": [
                "sources",
                "datasets",
                "detections",
                "obssources",
                "xcorr",
                "transients",
                "oldstacks",
            ],
            "2SXPS": [
                "sources",
                "datasets",
                "detections",
                "xcorr",
            ],
        }
        # Also need the default table to select when a catalogue is selected.
        self._defaultTablesByCat = {
            "LSXPS": "sources",
            "2SXPS": "sources",
        }

        # Default ID col for astroquery lookups
        self._defaultIDColBySource = {
            "LSXPS": {
                "sources": "LSXPS_ID",
                "datasets": "Dataset_ID",
                "transients": "TransientID",
            },
            "2SXPS": {"sources": "2SXPS_ID", "datasets": "ObsID"},
        }

        self._subsets = {
            "LSXPS": {
                "sources": ("clean", "ultraclean"),
                "datasets": ("clean", "ultraclean"),
            },
            "2SXPS": {
                "sources": ("clean", "ultraclean"),
                "datasets": ("clean", "ultraclean"),
            },
        }

        # Now set the selected catalogue to that supplied in the constructor.
        # As cat is actually a property dectorator, this will check that
        # the catalogue is valid and sert the tables and default table.
        self.cat = cat
        self._subset = None
        if table is not None:
            self.table = table

        self._prodData.update(
            {
                "sourceDetails": None,
                "lightCurves": None,
                "spectra": None,
                "datasetDetails": None,
                "transientDetails": None,
                "fullTable": None,
                "sourceObsList": None,
            }
        )

        self._lcbinning = None
        self._lctimeformat = None

    # ----------------------------------------------------------
    # Some properties unique to this class.
    @property
    def cat(self):
        """Which SXPS catalogue is to be queried."""
        return self._dbName

    @cat.setter
    def cat(self, dbName):
        if dbName in self.cats:
            self._dbName = dbName
            self._tables = self._tablesByCat[dbName]
            self.table = self._defaultTablesByCat[dbName]
        else:
            raise ValueError(f"{dbName} is not a known database.")

    @property
    def cats(self):
        """List of queryable SXPS catalogues."""
        return list(self._tablesByCat.keys())

    @property
    def sourceDetails(self):
        """Detailed source information."""
        return self._prodData["sourceDetails"]

    @property
    def transientDetails(self):
        """Detailed transient information."""
        return self._prodData["transientDetails"]

    @property
    def lightCurves(self):
        """Source light curves."""
        return self._prodData["lightCurves"]

    @property
    def spectra(self):
        """Source spectra."""
        return self._prodData["spectra"]

    @property
    def datasetDetails(self):
        """Detailed dataset information."""
        return self._prodData["datasetDetails"]

    @property
    def fullTable(self):
        """The full catalogue."""
        return self._prodData["fullTable"]

    @property
    def sourceObsList(self):
        """Detailed dataset information."""
        return self._prodData["sourceObsList"]

    @property
    def subsets(self):
        """The available subsets for the selected table"""
        return self._subsets[self._dbName][self.table]

    @property
    def subset(self):
        """The selected subset"""
        return self._subset

    @subset.setter
    def subset(self, set):
        if set is None:
            self._subset = None
            if self.verbose:
                print("Removing subset filters.")
        elif self._subsets is None:
            raise RuntimeError(f"{self.cat}.{self.table} has no subset.")
        elif set.lower() in self._subsets[self._dbName][self.table]:
            self._subset = set
            if self.verbose:
                print(f"Selecting `{set}` subset.")
        else:
            raise ValueError(f"`{set}` is not a valid subset.")

    # Also override the table setter property, so that we can accept
    # short-form table names and correct them.
    @dataQuery.table.setter
    def table(self, table):
        if table.lower() in dcat.tableLookup:
            table = dcat.tableLookup[table.lower()]
            if not self.silent:
                print(f"Adjusting table name to `{table}`")
        dataQuery.table.fset(self, table.lower())

        # Update default ID col if necessary
        if table in self._defaultIDColBySource[self._dbName]:
            self._defaultIDCol = self._defaultIDColBySource[self._dbName][table]
        else:
            self._defaultIDCol = None

        self.subset = None

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
    # Need to override the submit function.
    def submit(self):
        """Submit the query.

        This checks if a subset needs adding before calling the parent
        submit() function.

        """
        if self.subset is None:
            return super().submit()
        else:
            return super().submit(subset=self.subset)

    # And reset
    def reset(self, **kwargs):
        super().reset(**kwargs)
        self.clearLightCurves()

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

        byName : bool
            Whether to force use of the source name.

        byID : bool
            Whether to force use of the source ID

        Returns
        -------
        whichCol : str
            The name o the column to index on in the returned query.
        whichArg : str
            The name of the argument to send to the API.

        """
        whichCol = None
        whichArg = None

        if byName:
            whichCol = "IAUName"
            whichArg = "sourceName"
            if byID:
                raise RuntimeError("You cannot set byName and byID!")
        elif byID:
            whichCol = self._defaultIDCol  # f"{self.cat}_ID"
            whichArg = "sourceID"
        else:
            cols = {f"{self._defaultIDCol}": "sourceID", "IAUName": "sourceName"}

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

    def _handleDatasetArgs(self, byObsID=False, byDatasetID=False):
        """Decide whether to query on sourceID or name.

        This is an internal helper function for any function that gets
        products related to a query. It decides whether to send the
        DatasetID or obsID column with the request, depending first,
        on whether either was explicitly requested, and if not, based
        on which columns have been retrieved.

        Parameters
        ----------

        byObsID : bool
            Whether to force use of the ObsID.

        byDatasetID : bool
            Whether to force use of the DatasetID

        Returns
        -------
        whichCol : str
            The name o the column to index on in the returned query.
        whichArg : str
            The name of the argument to send to the API.

        """
        whichCol = None
        whichArg = None

        if byObsID:
            whichCol = "ObsID"
            whichArg = "ObsID"
            if byDatasetID:
                raise RuntimeError("You cannot set byName and byID!")
        elif byDatasetID:
            whichCol = "DatasetID"
            whichArg = "DatasetID"
        else:
            cols = ("ObsID", "DatasetID")

            for c in cols:
                if c in self.results.columns:
                    whichCol = c
                    whichArg = c
                    break
            if whichCol is None:
                raise RuntimeError(f"Cannot get dataset info, as none of the columns: {cols} are in your results.")

        if whichCol not in self.results.columns:
            raise RuntimeError(f"Cannot get dataset info, as the column `{whichCol}` is not in your results.")

        return (whichCol, whichArg)

    def getSourceDetails(self, subset=None, byName=False, byID=False, returnData=False):
        """Get the full set of information for retrieved sources.

        This function is primarily a wrapper to the function
        swifttools.ukssdc.data.SXPS.getSourceDetails; calling that
        function for the source(s) which this query object has returned.
        For obvious reasons, it will fail if you have not yet executed
        the query.

        The retrieved information will be saved in the "sourceDetails"
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

        e.g. if your dataQuery object is called 'q' then:

        => q.getSourceDetails(subset=q.results['Err90']<5)

        would get details of those sources in your result with Err90
        values <5.

        Parameters
        ----------

        subset : pandas.Series, optional
            A pandas series defining a subset of rows to download.

        byName : bool, optional
            Force the results to be indexed by IAUName.
            Requires that column to have been retrieved by your query.

        byID : bool, optional
            Force the results to be indexed by SXPS_ID.
            Requires that column to have been retrieved by your query.

        returnData : bool, optional
            Whether to return the data, as well as storing it in the
            "sourceDetails" variable.

        """
        if not self.haveResults:
            raise RuntimeError("This query has not been executed, cannot download!")

        if self.table != "sources":
            return RuntimeError("Cannot get source info for anything except sources!")

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

        tmp = dcat.getSourceDetails(cat=self.cat, silent=self.silent, verbose=self.verbose, **data)

        if self._prodData["sourceDetails"] is None:
            self._prodData["sourceDetails"] = tmp
        else:
            self._prodData["sourceDetails"].update(tmp)

        if not self.silent:
            print("Saved source information as sourceDetails varable.")
        if returnData:
            return self._prodData["sourceDetails"]

    def getDatasetDetails(self, byObsID=False, byDatasetID=False, subset=None, returnData=False):
        """Get the full set of information for retrieved datasets.

        This function is primarily a wrapper to the function
        swifttools.ukssdc.data.SXPS.getDatasetDetails; calling that
        function for the source(s) which this query object has returned.
        For obvious reasons, it will fail if you have not yet executed
        the query.

        The retrieved information will be saved in the "datasetDetails"
        variable of this object; it will also be returned by this
        function call if returnedData=True

        Left alone, this will get the details for all datasets supplied,
        identified, and index them by DatasetID (if that was retrieved),
        or ObsID otherwise. If neither column was retrieved, expect an
        error.

        The subset parameter is optional, and can be used to apply
        a filter to the results this query has obtained. The easiest way
        to generate this is using the pandas syntax for filtering on
        value.

        e.g. if your dataQuery object is called 'q' then:

        => q.getDatasetDetails(subset=q.results['ExposureUsed']>10000)

        would get details of all those datasets in your result with
        exposures longer than 10ks.

        Parameters
        ----------

        byObsID : bool, optional
            Index the results by ObsID (default: False).

        byDatasetID : bool, optional
            Index the results by DatasetID (default: False).

        subset : pandas.Series, optional
            A pandas series defining a subset of rows to download.

        returnData : bool, optional
            Whether to return the data, as well as storing it in the
            "datasetDetails" variable.

        """
        if not self.haveResults:
            raise RuntimeError("This query has not been executed, cannot download!")

        if self.table != "datasets":
            return RuntimeError("Cannot get dataset info for anything other than datasets!")

        # Check if we are doing ID or name.
        data = {}

        if not self.haveResults:
            raise RuntimeError("This query has not been executed, cannot download!")

        (whichCol, whichArg) = self._handleDatasetArgs(byObsID=byObsID, byDatasetID=byDatasetID)

        obslist = []
        if subset is not None:
            if not isinstance(subset, pd.core.series.Series):
                raise ValueError("Subset parameter must be a pandas series")
            obslist = self._results.loc[subset][whichCol].tolist()
        else:
            obslist = self.results[whichCol].tolist()

        # Now set up data, which will will pass as **data which will be received either as
        # sourceID = [...] or sourceName = [...]
        data[whichCol] = obslist

        tmp = dcat.getDatasetDetails(cat=self.cat, silent=self.silent, verbose=self.verbose, **data)

        if self._prodData["datasetDetails"] is None:
            self._prodData["datasetDetails"] = tmp
        else:
            self._prodData["datasetDetails"].update(tmp)

        if not self.silent:
            print("Saved dataset information as datasetDetails varable.")
        if returnData:
            return self._prodData["datasetDetails"]

    def getTransientDetails(self, subset=None, byName=False, byID=False, returnData=False):
        """Get the full set of information for retrieved transients.

        This function is primarily a wrapper to the function
        swifttools.ukssdc.data.SXPS.getTransientDetails; calling that
        function for the source(s) which this query object has returned.
        For obvious reasons, it will fail if you have not yet executed
        the query.

        The retrieved information will be saved in the "transientDetails"
        variable of this object; it will also be returned by this
        function call if returnedData=True

        Left alone, this will get the details for all sources your query
        identified, and index them by TransientID (if that was retrieved),
        or IAUName if the ID was not retrieved. If neither column was
        retrieved, expect an error.

        The subset parameter is optional, and can be used to apply
        a filter to the results this query has obtained. The easiest way
        to generate this is using the pandas syntax for filtering on
        value.

        e.g. if your dataQuery object is called 'q' then:

        => q.getTransientDetails(subset=q.results['Err90']<5)

        would get details of those sources in your result with Err90
        values <5.

        Parameters
        ----------

        subset : pandas.Series, optional
            A pandas series defining a subset of rows to download.

        byName : bool, optional
            Force the results to be indexed by IAUName.
            Requires that column to have been retrieved by your query.

        byID : bool, optional
            Force the results to be indexed by SXPS_ID.
            Requires that column to have been retrieved by your query.

        returnData : bool, optional
            Whether to return the data, as well as storing it in the
            "transientDetails" variable.

        """
        if not self.haveResults:
            raise RuntimeError("This query has not been executed, cannot download!")

        if self.table != "transients":
            raise RuntimeError("Cannot get transient info for anything except transients!")

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

        self._prodData["transientDetails"] = dcat.getTransientDetails(
            cat=self.cat, silent=self.silent, verbose=self.verbose, **data
        )
        if not self.silent:
            print("Saved transient information as transientDetails varable.")
        if returnData:
            return self._prodData["transientDetails"]

    def getDetails(self, **kwargs):
        """A wrapper to call the appropriate function."""
        if self.table == "sources":
            self.getSourceDetails(**kwargs)
        elif self.table == "datasets":
            self.getDatasetDetails(**kwargs)
        elif self.table == "transients":
            self.getTransientDetails(**kwargs)
        else:
            raise NotImplementedError

    def getFullTable(self, returnData=False, **kwargs):
        """Get the full catalogue data.

        This downloads the entire table in one go, storing it in the
        ``fullTable`` variable. You can optionally supply a subset, for
        the tables which have defined subset.

        This wraps swifttools.ukssdc.data.SXPS.getFullTable, and the
        ``**kwargs`` are passed to that function.

        Parameters
        ----------

        subset : str, optional
            Some tables have subsets you can select, e.g. the 'clean'
            set of sources. You can specify that subset using
            this parameter or, if this is not supplied, the default
            subset will be obtained.

        returnData : bool, optional
            Whether to return the data, as well as storing it in the
            ``fullTable`` variable.

        """

        if "saveData" not in kwargs:
            kwargs["saveData"] = False

        self._prodData["fullTable"] = dcat.getFullTable(
            cat=self.cat,
            table=self.table,
            subset=self.subset,
            returnData=True,
            silent=self.silent,
            verbose=self.verbose,
            **kwargs,
        )
        if returnData:
            return self.fullTable

    # ------------------------------------------------
    # Functions to retrieve products

    def getLightCurves(
        self,
        subset=None,
        byName=False,
        byID=False,
        bands="all",
        binning=None,
        timeFormat=None,
        returnData=False,
        **kwargs,
    ):
        """Get the full light curves for retrieved sources.

        This function is primarily a wrapper to the function
        swifttools.ukssdc.data.SXPS.getLightCurves; calling that
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

        e.g. if your dataQuery object is called 'q' then:

        => q.getLightCurves(subset=q.results['Err90']<5)

        would get lightcurves of all of the sources in your result with
        Err90 values <5.


        The light curves returned are stored in the ``lightCurves``
        variable of this object, and optionally returned. For their
        format see the help for
        swifttools.ukssdc.data.SXPS.getLightCurves.

        Parameters
        ----------

        subset : pandas.Series, optional
            A pandas series defining a subset of rows to download.

        byName : bool, optional
            Force the results to be indexed by IAUName.
            Requires that column to have been retrieved by your query.

        byID : bool, optional
            Force the results to be indexed by SXPS_ID.
            Requires that column to have been retrieved by your query.

        bands : str or list or tuple
            Either 'all', or a list of labels of the energy bands to
            retrieve ('total', 'soft', 'medium', 'hard', 'HR1', 'HR2')

        binning : str
            Which of the two binning methods you want: either
            'observation' or 'snapshot'

        timeFormat : str
            Which units to use for the time axis. Must be 'met' or 'tdb'
            or 'mjd'.

        returnData : bool, optional
            Whether the light curve data should be returned by this
            function, as well as saved in the "lightCurves"
            variable.

        **kwargs : dict
            Other arguments which are passed to
            swifttools.ukssdc.data.SXPS.getlightCurves.
            See its help for more information.

        """
        if self.table not in ("sources", "transients"):
            raise RuntimeError("Cannot get light curves for anything other than sources or transients!")

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
            if binning not in dcat.LC_BINNING:
                raise ValueError(f"{binning} is not an acceptable binning method.")
            binning = dcat.LC_BINNING[binning]

        if timeFormat is not None:
            timeFormat = timeFormat.lower()
            if timeFormat not in dcat.LC_TIMEFORMAT:
                raise ValueError(f"{timeFormat} is not an acceptable time system.")
            timeFormat = dcat.LC_TIMEFORMAT[timeFormat]

        if self._prodData["lightCurves"] is not None:
            if binning is None:
                binning = self._lcbinning
            if timeFormat is None:
                timeFormat = self._lctimeformat
            if (binning != self._lcbinning) or (timeFormat != self._lctimeformat):
                raise ValueError("Cannot get more light curves with different binning / timeformat.")

        useTrans = False
        if self.table == "transients":
            useTrans = True

        if "saveData" not in kwargs:
            kwargs["saveData"] = False

        tmp = dcat.getLightCurves(
            cat=self.cat,
            silent=self.silent,
            verbose=self.verbose,
            bands=bands,
            binning=binning,
            transient=useTrans,
            timeFormat=timeFormat,
            returnData=True,
            **data,
            **kwargs,
        )

        if self._prodData["lightCurves"] is None:
            self._prodData["lightCurves"] = tmp
        else:
            # Can't just merge the dicts, annoyingly, because this is not a deep (recursive) merge, so will not
            # add extra bands. However, I don't need a full recurse, just at the source level, so it's not too hard.
            for i in tmp.keys():
                if i in self._prodData["lightCurves"]:
                    tmpDS = self._prodData["lightCurves"][i]["Datasets"]
                    tmpDS.extend(x for x in tmp[i]["Datasets"] if x not in tmpDS)
                    self._prodData["lightCurves"][i].update(tmp[i])
                    # self._prodData['lightCurves'][i] = {**self._prodData['lightCurves'][i], **tmp[i]}
                    self._prodData["lightCurves"][i]["Datasets"] = tmpDS
                else:
                    self._prodData["lightCurves"][i] = tmp[i]

        # Now get the binning and timeformat, assuming any exist
        tmp = list(self._prodData["lightCurves"].keys())
        firstLC = tmp[0]
        if "Binning" in self._prodData["lightCurves"][firstLC]:
            self._lcbinning = self._prodData["lightCurves"][firstLC]["Binning"]
        if "TimeFormat" in self._prodData["lightCurves"][firstLC]:
            self._lctimeformat = self._prodData["lightCurves"][firstLC]["TimeFormat"]

        if returnData:
            return self._prodData["lightCurves"]

    def saveLightCurves(self, **kwargs):
        """Save the light curves to text files.

        This function is used to save the light curves that have been
        downloaded and are stored in the self.lightCurves
        variable of this SXPSQuery object. These light curves
        can be saved as simple text file (with a user-settable
        column separator), or as files formatted for the qdp programme.

        All this function actually does it to call the
        saveLightCurves() in the related module:
        swifttools.ukssdc.data; further detail on the parameters that
        can be used are documented for that function.

        Parameters
        ----------

        **kwargs : dict
            A set of parameters to pass to the main save function in
            swifttools.ukssdc.data

        """
        # Check that we have downloaded some light curves!
        if self.lightCurves is None:
            raise RuntimeError("There are no light curves to save!")
        dcat.saveLightCurves(self.lightCurves, silent=self.silent, verbose=self.verbose, **kwargs)

    def clearLightCurves(self):
        """Forget all light curves."""
        self._prodData["lightCurves"] = None
        self._lcbinning = None
        self._lctimeformat = None

    def plotLightCurves(self, whichSource, **kwargs):
        """Plot the light curves of a specific GRB.

        This is a wrapper to the ``ukssdc.plotLightCurve()`` function,
        giving you a plot of the light curve in question.

        You can only plot one GRB at a time (at present) and so you
        must provide the identifier (name or targetID) of a single
        downloaded GRB.

        Parameters
        ----------

        whichSource : str
            The identifier of a GRB to download. Must be a key to the
            ``lightCurves`` dict.

        **kwargs : dict
            Arguments to pass to ``plotLightCurve()``

        """
        if self.lightCurves is None:
            raise RuntimeError("I don't have any light curves to plot!")

        if whichSource not in self.lightCurves:
            raise RuntimeError(f"`{whichSource}` is not a recognised, downloaded GRB.")

        if "silent" not in kwargs:
            kwargs["silent"] = self.silent
        if "verbose" not in kwargs:
            kwargs["verbose"] = self.verbose

        return lcPlot(self.lightCurves[whichSource], **kwargs)

    def getSpectra(self, subset=None, byName=False, byID=False, returnData=False, **kwargs):
        """Get the spectral information for the retrieved source(s).

        This function is primarily a wrapper to the function
        swifttools.ukssdc.data.SXPS.getSpectra; calling that
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

        e.g. if your dataQuery object is called 'q' then:

        => q.getSpectra(subset=q.results['Err90']<5)

        would get spectra for the sources in your result with Err90
        values <5.

        The light curves returned are stored in the ``spectra``
        variable of this object, and optionally returned. For their
        format see the help for swifttools.ukssdc.data.SXPS.getSpectra.

        Parameters
        ----------

        subset : pandas.Series, optional
            A pandas series defining a subset of rows to download.

        byName : bool, optional
            Force the results to be indexed by IAUName.
            Requires that column to have been retrieved by your query.

        byID : bool, optional
            Force the results to be indexed by SXPS_ID.
            Requires that column to have been retrieved by your query.

        returnData : bool, optional
            Whether the light curve data should be returned by this
            function, as well as saved in the "lightCurves"
            variable.

        **kwargs : dict, optional
            Any arguments to pass to ``data.SXPS.getSpectra``, e.g.
            specType if this is a transient.

        """
        if self.table not in ("sources", "transients"):
            raise RuntimeError("Cannot get spectra for anything other than sources or transients!")

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

        useTrans = False
        if self.table == "transients":
            useTrans = True

        if "saveData" not in kwargs:
            kwargs["saveData"] = False

        tmp = dcat.getSpectra(
            cat=self.cat,
            silent=self.silent,
            verbose=self.verbose,
            transient=useTrans,
            returnData=True,
            **data,
            **kwargs,
        )

        if self._prodData["spectra"] is None:
            self._prodData["spectra"] = tmp
        else:
            self._prodData["spectra"].update(tmp)

        if returnData:
            return self._prodData["spectra"]

    def saveSpectra(self, **kwargs):
        """Save the spectra files to disk.

        This function is used to save the spectra that have been
        downloaded and are stored in the self.spectra
        variable of this SXPSQuery object.

        All this function actually does it to call the
        saveSpectra() in the related module:
        swifttools.ukssdc.data; further detail on the parameters that
        can be used are documented for that function.

        Parameters
        ----------

        **kwargs : dict
            A set of parameters to pass to the main save function in
            swifttools.ukssdc.data

        """
        # Check that we have downloaded some light curves!
        if self.spectra is None:
            raise RuntimeError("There are no spectra to save!")
        dcat.saveSpectra(self.spectra, silent=self.silent, verbose=self.verbose, **kwargs)

    def clearSpectra(self):
        """Forget all spectra."""
        self._prodData["spectra"] = None

    def saveSourceImages(self, byName=False, byID=False, subset=None, **kwargs):
        """Download and save the images for retrieved datasets.

        This function is primarily a wrapper to the function
        swifttools.ukssdc.data.SXPS.saveSoureImages; calling that
        function for the source(s) which this query object has returned.
        For obvious reasons, it will fail if you have not yet executed
        the query.

        Left alone, this will get the images for all sources your query
        identified, and save them all into a single directory. If you
        set ``subDirs=True`` then instead the images will be saved into
        one directory per source, with directories named by sourceID
        or name, depending on your byID/byName values.

        The subset parameter is optional, and can be used to apply
        a filter to the results this query has obtained. The easiest way
        to generate this is using the pandas syntax for filtering on
        value.

        e.g. if your dataQuery object is called 'q' then:

        => q.getDatasetDetails(subset=q.results['ExposureUsed']>10000)

        would get images for all those datasets in your result with
        exposures longer than 10ks.

        Parameters
        ----------

        byName : bool, optional
            Index the results by sourceName (default: False).

        byID : bool, optional
            Index the results by sourceName (default: False).


        subset : pandas.Series, optional
            A pandas series defining a subset of rows to download.

        **kwargs : dict
            Arguments to pass to
            swifttools.ukssdc.data.SXPS.saveDatasetImages.

        """

        if self.table not in ("sources", "transients"):
            raise RuntimeError("Cannot get source images for anything other than sources or transients!")

        if not self.haveResults:
            raise RuntimeError("This query has not been executed, cannot download!")

        # Check if we are doing ID or name.
        data = {}

        if not self.haveResults:
            raise RuntimeError("This query has not been executed, cannot download!")
        (whichCol, whichArg) = self._handleSourceArgs(byName=byName, byID=byID)

        data[whichArg] = []
        if self.table == "transients":
            data["transient"] = True

        # But before we can populate it, we may have to handle a subset:
        if subset is not None:
            if not isinstance(subset, pd.core.series.Series):
                raise ValueError("Subset parameter must be a pandas series")
            data[whichArg] = self._results.loc[subset][whichCol].tolist()
        else:
            data[whichArg] = self._results[whichCol].tolist()

        dcat.saveSourceImages(cat=self.cat, silent=self.silent, verbose=self.verbose, **data, **kwargs)

    def saveTransientImages(self, **kwargs):
        """Download and save the images for retrieved transients.

        Literally just redirects to saveSourceImages!
        """
        return self.saveSourceImages(**kwargs)

    def saveDatasetImages(self, byObsID=False, byDatasetID=False, subset=None, **kwargs):
        """Download and save the images for retrieved datasets.

        This function is primarily a wrapper to the function
        swifttools.ukssdc.data.SXPS.saveDatasetImages; calling that
        function for the source(s) which this query object has returned.
        For obvious reasons, it will fail if you have not yet executed
        the query.

        Left alone, this will get the images for all datasets your query
        identified, and save them all into a single directory. If you
        set ``subDirs=True`` then instead the images will be saved into
        one directory per dataset, with directories named by DatasetID.
        If you set ``byObsID=True`` then the subdirectories will instead
        be the ObsIDs.

        The subset parameter is optional, and can be used to apply
        a filter to the results this query has obtained. The easiest way
        to generate this is using the pandas syntax for filtering on
        value.

        e.g. if your dataQuery object is called 'q' then:

        => q.getDatasetDetails(subset=q.results['ExposureUsed']>10000)

        would get images for all those datasets in your result with
        exposures longer than 10ks.

        Parameters
        ----------

        byObsID : bool, optional
            Index the results by ObsID (default: False).

        byDatasetID : bool, optional
            Index the results by DatasetID (default: False).

        subset : pandas.Series, optional
            A pandas series defining a subset of rows to download.

        **kwargs : dict
            Arguments to pass to
            swifttools.ukssdc.data.SXPS.saveDatasetImages.

        """

        if self.table != "datasets":
            raise RuntimeError("Cannot get dataset images for anything other than datasets!")

        if not self.haveResults:
            raise RuntimeError("This query has not been executed, cannot download!")

        # Check if we are doing ID or name.
        data = {}

        if not self.haveResults:
            raise RuntimeError("This query has not been executed, cannot download!")

        (whichCol, whichArg) = self._handleDatasetArgs(byObsID=byObsID, byDatasetID=byDatasetID)

        obslist = []
        if subset is not None:
            if not isinstance(subset, pd.core.series.Series):
                raise ValueError("Subset parameter must be a pandas series")
            obslist = self._results.loc[subset][whichCol].tolist()
        else:
            obslist = self.results[whichCol].tolist()

        # Now set up data, which will will pass as **data which will be received either as
        # sourceID = [...] or sourceName = [...]
        data[whichCol] = obslist

        self._prodData["datasetDetails"] = dcat.saveDatasetImages(
            cat=self.cat, silent=self.silent, verbose=self.verbose, **data, **kwargs
        )

    def saveImages(self, **kwargs):
        """A wrapper to call the appropriate function."""
        if self.table == "sources":
            self.saveSourceImages(**kwargs)
        elif self.table == "datasets":
            self.saveDatasetImages(**kwargs)
        elif self.table == "transients":
            self.saveTransientImages(**kwargs)
        else:
            raise NotImplementedError

    # ------------------------------------------------
    # Interaction with xrt_prods
    def makeProductRequest(self, email, byName=False, byID=False, subset=None, **kwargs):
        """Create XRTProductRequest objects for your sources.

        This function is primarily a wrapper to the function
        ``swifttools.ukssdc.data.SXPS.makeProductRequest()``; calling
        that function for the source(s) which this query object has
        returned. For obvious reasons, it will fail if you have not yet
        executed the query.

        This will get the XRTProductRequests for all sources your query
        identified. For full details, see the help for
        swifttools.ukssdc.data.SXPS.makeProductRequest

        The subset parameter is optional, and can be used to apply
        a filter to the results this query has obtained. The easiest way
        to generate this is using the pandas syntax for filtering on
        value.

        e.g. if your dataQuery object is called 'q' then:

        => q.getDatasetDetails(subset=q.results['ExposureUsed']>10000)

        would get images for all those datasets in your result with
        exposures longer than 10ks.

        Parameters
        ----------

        email : str
            The email address with which you registered to submit
            XRTProductRequest objects to the servers.

        byName : bool, optional
            Index the results by ObsID, instead of the DatasetID
            (default: False).

        subset : pandas.Series, optional
            A pandas series defining a subset of rows to download.

        **kwargs : dict
            Arguments to pass to
            swifttools.ukssdc.data.SXPS.saveDatasetImages.

        """
        if self.table not in ("sources", "transients"):
            raise RuntimeError("Cannot get XRTProductRequests for anything other than sources or transients!")
        if not self.haveResults:
            raise RuntimeError("This query has not been executed, cannot download!")

        # Check if we are doing ID or name.
        data = {}

        if not self.haveResults:
            raise RuntimeError("This query has not been executed, cannot download!")
        (whichCol, whichArg) = self._handleSourceArgs(byName=byName, byID=byID)

        data[whichArg] = []
        if self.table == "transients":
            data["transient"] = True

        # But before we can populate it, we may have to handle a subset:
        if subset is not None:
            if not isinstance(subset, pd.core.series.Series):
                raise ValueError("Subset parameter must be a pandas series")
            data[whichArg] = self._results.loc[subset][whichCol].tolist()
        else:
            data[whichArg] = self._results[whichCol].tolist()

        return dcat.makeProductRequest(
            email,
            cat=self.cat,
            sourceDetails=self.sourceDetails,
            silent=self.silent,
            verbose=self.verbose,
            **data,
            **kwargs,
        )

    def getObsList(self, byName=False, byID=False, subset=None, returnData=False, **kwargs):
        """Get the list of observations covering a source.

        This function is primarily a wrapper to the function
        ``swifttools.ukssdc.data.SXPS.getObsList()``; calling
        that function for the source(s) which this query object has
        returned. For obvious reasons, it will fail if you have not yet
        executed the query.

        The subset parameter is optional, and can be used to apply
        a filter to the results this query has obtained. The easiest way
        to generate this is using the pandas syntax for filtering on
        value.

        Parameters
        ----------

        byName : bool, optional
            Index the results by source name (default: ``False``).

        byID : bool, optional
            Index the results by source ID (default: ``False``).

        subset : pandas.Series, optional
            A pandas series defining a subset of rows to download.

        returnData : bool, optional
            Whether to return the obslist found by this function call
            (default: ``False``).

        **kwargs : dict
            Arguments to pass to
            ``swifttools.ukssdc.data.SXPS.getObsList``.

        """
        if self.table != "sources":
            raise RuntimeError("Cannot get observation list for anything other than sources!")
        if not self.haveResults:
            raise RuntimeError("This query has not been executed, cannot get extra data!")

        # Check if we are doing ID or name.
        data = {}

        if not self.haveResults:
            raise RuntimeError("This query has not been executed, cannot download!")
        (whichCol, whichArg) = self._handleSourceArgs(byName=byName, byID=byID)

        data[whichArg] = []

        # But before we can populate it, we may have to handle a subset:
        if subset is not None:
            if not isinstance(subset, pd.core.series.Series):
                raise ValueError("Subset parameter must be a pandas series")
            data[whichArg] = self._results.loc[subset][whichCol].tolist()
        else:
            data[whichArg] = self._results[whichCol].tolist()

        tmp = dcat.getObsList(
            sourceDetails=self.sourceDetails,
            cat=self.cat,
            silent=self.silent,
            verbose=self.verbose,
            **data,
            **kwargs,
        )

        if self._prodData["sourceObsList"] is None:
            self._prodData["sourceObsList"] = tmp
        else:
            self._prodData["sourceObsList"].update(tmp)

        if returnData:
            return tmp

    # ----------------------------------------------------------------
    # astroquery-based functions

    def doSIMBADSearch(self, byName=False, byID=False, **kwargs):
        """Do a SIMBAD search around the object(s).

        This function is primarily a wrapper to the function
        swifttools.ukssdc.query.doSIMBADSearch; calling that
        function for the source(s) which this query object has returned.
        For obvious reasons, it will fail if you have not yet executed
        the query.

        Parameters
        ----------

        byName : bool, optional
            Force the results to be indexed by IAUName.
            Requires that column to have been retrieved by your query.

        byID : bool, optional
            Force the results to be indexed by SXPS_ID.
            Requires that column to have been retrieved by your query.

        """
        (whichCol, whichArg) = self._handleSourceArgs(byName=byName, byID=byID)

        return super().doSIMBADSearch(**kwargs, idCol=whichCol)

    def doVizierSearch(self, byName=False, byID=False, **kwargs):
        """Do a Vizier search around the object(s).

        This function is primarily a wrapper to the function
        swifttools.ukssdc.query.doVizierSearch; calling that
        function for the source(s) which this query object has returned.
        For obvious reasons, it will fail if you have not yet executed
        the query.

        Parameters
        ----------

        byName : bool, optional
            Force the results to be indexed by IAUName.
            Requires that column to have been retrieved by your query.

        byID : bool, optional
            Force the results to be indexed by SXPS_ID.
            Requires that column to have been retrieved by your query.

        """
        (whichCol, whichArg) = self._handleSourceArgs(byName=byName, byID=byID)

        return super().doVizierSearch(**kwargs, idCol=whichCol)
