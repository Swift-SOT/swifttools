__docformat__ = "restructedtext en"
import pandas as pd
from .dataquery_base import dataQuery
from ..data import GRB as dGRB
from .. import plotLightCurve as lcPlot


class GRBQuery(dataQuery):
    """A request to query a GRB cataloguee.

    This inherits from the dataQuery class, and TO BE WRITTEN.
    """

    def __init__(self, cat="UK_XRT", isAux=False, silent=True, verbose=False):
        super().__init__(silent=silent, verbose=verbose)
        """Create a GRBQuery instance.

        May add auxcat in here soon.

        Parameters
        ----------

        cat : str, optional
            Which GRB catalogue to base this query on
            (default: 'UK_XRT').

        isAux : bool, optional
            **For internal use only** whether this is being set as an
            auxilliary catalogue

        silent : bool, optional
            Whether to suppress all console output (default: ``True``).

        verbose : bool, optional
            Whether to give verbose output for everything
            (default: False; overridden by ``silent``).

        """
        # As with SXPS.py, define the tables per catalogue, although
        # in this case there is only one table per catalogue. They still
        # have to be a list for compatibility with the base class.

        self._tablesByCat = {
            "UK_XRT": [
                "XRTLiveCat",
            ],
            "SDC_GRB": [
                "SDC_Data_Table",
            ],
            "BAT_GRB": [
                "BATGRBCat",
            ],
        }
        # Also need the default table to select when a catalogue is selected.
        self._defaultTablesByCat = {"UK_XRT": "XRTLiveCat", "SDC_GRB": "SDC_Data_Table", "BAT_GRB": "BATGRBCat"}

        self._defaultPosSourceByCat = {
            "UK_XRT": "best",
            "SDC_GRB": "BAT",
            "BAT_GRB": "BAT",
        }

        self._posSources = {
            "UK_XRT": {
                "best": ["RA", "Decl"],
                "Onboard": ["Onboard_RA", "Onboard_Decl"],
                "SPER": ["SPER_RA", "SPER_Decl"],
                "Standard": ["PSF_RA", "PSF_Decl"],
                "Enhanced": ["Enh_RA", "SPER_Decl"],
            },
            "SDC_GRB": {
                "BAT": ["BAT_RA", "BAT_Dec"],
                "XRT": ["XRT_RA", "XRT_Dec"],
                "UVOT": ["UVOT_RA", "UVOT_Dec"],
            },
            "BAT_GRB": {
                "BAT": ["RA_ground", "DEC_ground"],
            },
        }

        self._auxCat = None
        self._nameCol = None

        self._prodData.update(
            {
                "lightCurves": None,
                "spectra": None,
                "burstAnalyser": None,
                "positions": None,
            }
        )

        # self._lightCurves = None
        # self._spectra = None
        # self._burstAnalyser = None
        # self._positions = None

        self._isAuxCat = isAux
        self.cat = cat

        # Now set the selected catalogue to that supplied in the constructor.
        # As whichCat is actually a property dectorator, this will check that
        # the catalogue is valid and sert the tables and default table.
        # self.table = table

    # ----------------------------------------------------------
    # Some properties unique to this class.
    @property
    def cat(self):
        """Which GRB catalogue is to be queried."""
        return self._dbName

    @cat.setter
    def cat(self, dbName):
        if dbName in self.cats:
            self._dbName = dbName
            self._tables = self._tablesByCat[dbName]
            self.table = self._defaultTablesByCat[dbName]
            self.posSource = self._defaultPosSourceByCat[dbName]
        else:
            raise ValueError(f"{dbName} is not a known database.")

    @property
    def cats(self):
        """List of queryable GRB catalogues."""
        return list(self._tablesByCat.keys())

    # Need to be able to select which position we use for the search.
    @property
    def posSource(self):
        if self.verbose:
            print(f"Using {self._posSource} for the positions")
            print(f"RA column: {self.raCol}, Dec column: {self.decCol}")
        return self._posSource

    @posSource.setter
    def posSource(self, source):
        if source not in self._posSources[self.cat]:
            raise ValueError(f"`{source}` is not a valid source of position data")
        self._posSource = source
        self._raCol = self._posSources[self.cat][source][0]
        self._decCol = self._posSources[self.cat][source][1]

    @property
    def posSources(self):
        """Possible sources of position data"""
        return list(self._posSources[self.cat].keys())

    @property
    def auxCat(self):
        """Access to the auxilliary catalogue."""
        return self._auxCat

    @property
    def lightCurves(self):
        """GRB light curves."""
        return self._prodData["lightCurves"]

    @property
    def spectra(self):
        """GRB spectra."""
        return self._prodData["spectra"]

    @property
    def burstAnalyser(self):
        """GRB burst analyser data."""
        return self._prodData["burstAnalyser"]

    @property
    def ban(self):
        """GRB burst analyser data."""
        return self._prodData["burstAnalyser"]

    @property
    def positions(self):
        """GRB positions."""
        return self._prodData["positions"]

    # ------------------------------------------------------------------
    # Some functions which override the parent functions

    # Metadata needs to set a name column as well, as this will be used
    # to merge the cat and aux cat.

    def getMetadata(self):
        """Retrieve the metadata for this catalogue from the server.

        This function calls the base class ``getMetadata()`` function,
        for this query and any aux cat.

        """
        super().getMetadata()
        if "IsNameCol" in self._metadata:
            self._metadata["IsNameCol"] = pd.to_numeric(self._metadata["IsNameCol"])
            tmp = self._metadata.loc[self._metadata["IsNameCol"] == 1]["ColName"]
            if len(tmp) > 0:
                self._nameCol = tmp.iloc[0]
                if len(tmp) > 1 and not self.silent:
                    print(
                        "WARNING: Metadata contains TWO name columns! This may be a bug; "
                        "please notify swift-help@leicester.ac.uk"
                    )

    def addConeSearch(self, **kwargs):
        super().addConeSearch(**kwargs)
        if self.auxCat is not None:
            if not self.silent:
                print("Applying cone search to auxilliary catalogue.")
                self.auxCat.addConeSearch(**kwargs)

    def unlock(self):
        super().unlock()
        if self.auxCat is not None:
            self.auxCat.unlock()

    def submit(self, merge=False):
        """Submit the query.

        This wraps the base class ``submit()`` function, but also
        ensures that if there is an aux cat, that is also submitted,
        and the results filtered to only things which match both
        catalogues.
        """

        # If we have an aux cat, we have to ensure that both this
        # and that include the name column, so we can merge.
        if self.auxCat is not None:
            self._forceNameCol()
            self.auxCat._forceNameCol()

        super().submit()
        if self.auxCat is not None:
            self.auxCat.submit()
            # Now we have to merge...
            i1 = self.results.set_index(self._nameCol).index
            i2 = self.auxCat.results.set_index(self.auxCat._nameCol).index
            tmp = self.results[i1.isin(i2)]
            tmp2 = self.auxCat.results[i2.isin(i1)]
            self._results = tmp
            self.auxCat._results = tmp2
            self._results = tmp

            if merge:
                self.mergeResults()

    def mergeResults(self):
        """Merge the results from this and auxCat."""

        if self.results is None:
            if not self.silent:
                print("Cannot merge - there are no results")
            return

        tmp = self.results.merge(self.auxCat.results, how="inner", left_on=self._nameCol, right_on=self.auxCat._nameCol)
        self._results = tmp

    def reset(self, keepAux=False, **kwargs):
        """Reset this query.

        This resets the query so it can be redefined or rerun. It calls
        ``dataquery_base.reset()`` with the specified kwargs, but
        optionally keeps the aux catalogue (but resets it).

        Parameters
        ----------

        keepAux : bool, optional
            Whether the retain (but reset) the auxilliary catalogue
            (default ``False``).

        """
        super().reset(**kwargs)
        if self.auxCat:
            if keepAux:
                # Note, we pass keepAux since in principle the aux
                # cat can have its own aux cat.
                self.auxCat.reset(keepAux=keepAux, **kwargs)
            else:
                self.removeAuxCat()

    # ------------------------------------------------------------------
    # Functions for managing the aux cat

    def getAuxCat(self):
        """Report whether an auxilliary catalogue has been defined.

        Returns
        -------

        str or None:
            If there is no auxilliary catalogue, this will return
            ``None``, otherwise it will return the name of the
            catalogue.
        """

        if self.auxCat is None:
            return None
        return self.auxCat.cat

    def removeAuxCat(self):
        """Remove the auxilliary catalogue"""

        self._auxCat = None

    def setAuxCat(self, cat, silent=None, verbose=None):
        """Set an auxilliary catalogue.

        An auxilliary catalogue allows you to prepare a query which
        combines data from multiple GRB catalogues.
        If you have a cone search then any cone search will be applied
        to the main and auxilliary catalogues; otherwise you can specify
        filters for each catalogue, and then the results returned by
        ``submit()`` will be only GRBs found in both catalogues.

        Parameters
        ----------

        cat : str,
            Which GRB catalogue to use as the auxilliary. **Cannot be
            the same as this catalogue in the main query.**

        silent : bool or None, optional
            Whether to suppress all console output. If ``None`` then it
            will be set to the current query object's ``silent`` value
            (default: ``None``).

        verbose : bool or None, optional
            Whether to give verbose output for everything. If ``None``
            then it will be set to the current query object's
            ``verbose`` value(default: ``None``).

        """
        if cat == self.cat:
            raise ValueError("Cannot have an auxilliary catalogue the same as myself")
        if silent is None:
            silent = self.silent
        if verbose is None:
            verbose = self.verbose
        self._auxCat = GRBQuery(cat=cat, isAux=True, silent=silent, verbose=verbose)

    def _forceNameCol(self):
        """Ensure that the name column is set to be retrieved."""

        if (self.colsToGet is not None) and (self._nameCol not in self.colsToGet):
            self._addCol(self._nameCol)

    # ------------------------------------------------------------------
    # Functions for getting data or products

    # This will look a bit like the SXPS query module, we will allow the
    # user to decide if things are indexed by the targetID or name.

    # getLightCurves
    # getSpectra
    # getBurstAnalyser
    # saveBurstAnalyser

    # Add stuff for positions if I add those.

    # First a function which everything will call, which will handle the
    # byTarget/byName thing:

    def _handleArgs(self, byName=False, byID=False):
        """Decide whether to query on targetID or name.

        This is an internal helper function for any function that gets
        products related to a query. It decides whether to send the
        GRB name or targetID column with the request, depending first,
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
            The name of the argument to send to the data module (GRBName
            or targetID).

        """
        whichCol = None
        whichArg = None

        if byID:
            whichCol = self._targetCol
            whichArg = "targetID"
            if byName:
                raise RuntimeError("You cannot set byName and byID!")
        elif byName:
            whichCol = self._nameCol
            whichArg = "GRBName"
        else:
            cols = {self._nameCol: "GRBName", self._targetCol: "sourceID"}

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

    def getLightCurves(self, subset=None, byName=False, byID=False, returnData=False, **kwargs):
        """Download the light curves for the retrieved GRBs.

        This function downloads the light curves of the GRBs found when
        this query was executed. Of course, this means you have to have
        executed the query first!

        The light curve data will be stored in the ``lightCurves``
        variable of this object, and optionally returned as well. The
        light curves files can also be downloaded directly from the
        website to disk.

        Parameters
        ----------

        subset : pandas.Series, optional
            A pandas series defining a subset of rows in the query
            results to download.

        byName : bool, optional
            Force the results to be indexed by the GRB name.

        byID : bool, optional
            Force the results to be indexed by targetID.
            Requires that column to have been retrieved by your query.

        returnData : bool, optional
            Whether the light curve data should be returned by this
            function, as well as saved in the "lightCurves"
            variable.

        **kwargs : dict
            Other arguments which are passed to
            ``ukssdc.data.GRB.getlightCurves()``.
            See its help for more information.

        """
        if not self.haveResults:
            raise RuntimeError("This query has not been executed, cannot download!")

        # Check if we are doing ID or name.
        data = {}
        (whichCol, whichArg) = self._handleArgs(byName=byName, byID=byID)

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

        # if "returnData" not in kwargs:
        #     kwargs["returnData"] = True
        kwargs["returnData"] = True
        if "saveData" not in kwargs:
            kwargs["saveData"] = False

        tmp = dGRB.getLightCurves(
            silent=self.silent,
            verbose=self.verbose,
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

        if returnData:
            return self._prodData["lightCurves"]

    def saveLightCurves(self, **kwargs):
        """Save the light curves to text files.

        This function is used to save the light curves that have been
        downloaded and are stored in the self.lightCurves
        variable of this GRBQuery object. These light curves
        can be saved as simple text file (with a user-settable
        column separator), or as files formatted for the qdp programme.

        All this function actually does it to call the
        saveLightCurves() in the related module:
        ``ukssdc.data.GRB``; further detail on the parameters that
        can be used are documented for that function.

        Parameters
        ----------

        **kwargs : dict
            A set of parameters to pass to the main save function in
            ``ukssdc.data.GRB``

        """
        # Check that we have downloaded some light curves!
        if self.lightCurves is None:
            raise RuntimeError("There are no light curves to save!")
        dGRB.saveLightCurves(self.lightCurves, silent=self.silent, verbose=self.verbose, **kwargs)

    def clearLightCurves(self):
        """Clear self.lightCurves"""
        self._prodData["lightCurves"] = None

    def getSpectra(self, subset=None, byName=False, byID=False, returnData=False, **kwargs):
        """Download the spectra for the retrieved GRBs.

        This function downloads the spectra of the GRBs found when this
        query was executed. Of course, this means you have to have
        executed the query first!

        The spectral data will be stored in the ``spectra``
        variable of this object, and optionally returned as well. The
        spectral files can also be downloaded directly from the
        website to disk.

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
            Parameters to pass to ukssdc.data.GRB.getSpectra()

        """
        if not self.haveResults:
            raise RuntimeError("This query has not been executed, cannot download!")

        # Check if we are doing ID or name.
        data = {}
        (whichCol, whichArg) = self._handleArgs(byName=byName, byID=byID)

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

        # if "returnData" not in kwargs:
        #     kwargs["returnData"] = True
        kwargs["returnData"] = True
        if "saveData" not in kwargs:
            kwargs["saveData"] = False
        if "saveImages" not in kwargs:
            kwargs["saveImages"] = False

        tmp = dGRB.getSpectra(
            silent=self.silent,
            verbose=self.verbose,
            **data,
            **kwargs,
        )

        if self._prodData["spectra"] is None:
            self._prodData["spectra"] = tmp
        else:
            self._prodData["spectra"].update(tmp)

        if returnData:
            return self._prodData["spectra"]

    def plotLightCurves(self, whichGRB, **kwargs):
        """Plot the light curves of a specific GRB.

        This is a wrapper to the ``ukssdc.plotLightCurve()`` function,
        giving you a plot of the light curve in question.

        You can only plot one GRB at a time (at present) and so you
        must provide the identifier (name or targetID) of a single
        downloaded GRB.

        Parameters
        ----------

        whichGRB : str
            The identifier of a GRB to download. Must be a key to the
            ``lightCurves`` dict.

        **kwargs : dict
            Arguments to pass to ``plotLightCurve()``

        """
        if self.lightCurves is None:
            raise RuntimeError("I don't have any light curves to plot!")

        if whichGRB not in self.lightCurves:
            raise RuntimeError(f"`{whichGRB}` is not a recognised, downloaded GRB.")

        if "silent" not in kwargs:
            kwargs["silent"] = self.silent
        if "verbose" not in kwargs:
            kwargs["verbose"] = self.verbose
        return lcPlot(self.lightCurves[whichGRB], **kwargs)

    def saveSpectra(self, **kwargs):
        """Save the spectra files to disk.

        This function is used to save the spectra that have been
        downloaded and are stored in the self.spectra
        variable of this GRBQuery object.

        All this function actually does it to call the
        saveSpectra() in the related module:
        ``ukssdc.data.GRB``; further detail on the parameters that
        can be used are documented for that function.

        Parameters
        ----------

        **kwargs : dict
            A set of parameters to pass to the main save function in
            ``ukssdc.data.GRB``

        """
        # Check that we have downloaded some light curves!
        if self.spectra is None:
            raise RuntimeError("There are no spectra to save!")

        dGRB.saveSpectra(self.spectra, silent=self.silent, verbose=self.verbose, **kwargs)

    def clearSpectra(self):
        """Clear self.spectra"""
        self._prodData["spectra"] = None

    def getBurstAnalyser(self, subset=None, byName=False, byID=False, returnData=False, **kwargs):
        """Download the burst analyser data for the retrieved GRBs.

        This function downloads the burst analyser data of the GRBs
        found when this query was executed. Of course, this means you
        have to have executed the query first!

        The light curve data will be stored in the ``lightCurves``
        variable of this object, and optionally returned as well. The
        light curves files can also be downloaded directly from the
        website to disk.

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
            Parameters to pass to ukssdc.data.GRB.getSpectra()

        """
        if not self.haveResults:
            raise RuntimeError("This query has not been executed, cannot download!")

        # Check if we are doing ID or name.
        data = {}
        (whichCol, whichArg) = self._handleArgs(byName=byName, byID=byID)

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

        # if "returnData" not in kwargs:
        #     kwargs["returnData"] = True
        kwargs["returnData"] = True
        if "saveData" not in kwargs:
            kwargs["saveData"] = False
        if "downloadTar" not in kwargs:
            kwargs["downloadTar"] = False

        tmp = dGRB.getBurstAnalyser(
            silent=self.silent,
            verbose=self.verbose,
            **data,
            **kwargs,
        )

        if self._prodData["burstAnalyser"] is None:
            self._prodData["burstAnalyser"] = tmp
        else:
            self._prodData["burstAnalyser"].update(tmp)

        if returnData:
            return self._prodData["burstAnalyser"]

    def saveBurstAnalyser(self, **kwargs):
        """Save the burst analyser data to disk.

        This function is used to save the burst analyser data that have
        been downloaded and are stored in the self.burstAnalyser
        variable of this GRBQuery object.

        All this function actually does it to call the
        saveBurstAnalyser() in the related module:
        ``ukssdc.data.GRB``; further detail on the parameters
        that can be used are documented for that function.

        Parameters
        ----------

        **kwargs : dict
            A set of parameters to pass to the ``saveBurstAnalyser()``
            function in ``ukssdc.data.GRB``.

        """
        # Check that we have downloaded some light curves!
        if self.burstAnalyser is None:
            raise RuntimeError("There are no burst analyser data to save!")

        dGRB.saveBurstAnalyser(self.burstAnalyser, silent=self.silent, verbose=self.verbose, **kwargs)

    def clearBurstAnalysers(self):
        """Clear self.burstAnalyser"""
        self._prodData["burstAnalyser"] = None

    def getObsData(self, subset=None, **kwargs):
        """Download the obs data for the retrieved GRBs.

        This function downloads the obs data of the GRBs found when
        this query was executed. Of course, this means you have to have
        executed the query first!

        It basically wraps around ``ukssdc.data.downloadObsData()`` and
        most of the arguments you supply are just passed to that.

        Parameters
        ----------

        subset : pandas.Series, optional
            A pandas series defining a subset of rows in the query
            results to download.

        **kwargs : dict
            Other arguments which are passed to
            ``ukssdc.data.downloadObsData()``.

        """
        if not self.haveResults:
            raise RuntimeError("This query has not been executed, cannot download!")

        whichCol = None
        whichArg = None

        if self._targetCol in self.results.columns:
            whichCol = self._targetCol
            whichArg = "targetID"
        elif self._nameCol in self.results.columns:
            whichCol = self._nameCol
            whichArg = "GRBName"
        else:
            raise RuntimeError("Cannot get data as neither a name or targetID have been retrieved")

        data = {}
        # But before we can populate it, we may have to handle a subset:
        if subset is not None:
            if not isinstance(subset, pd.core.series.Series):
                raise ValueError("Subset parameter must be a pandas series")
            data[whichArg] = self._results.loc[subset][whichCol].tolist()
        else:
            data[whichArg] = self._results[whichCol].tolist()

        dGRB.getObsData(silent=self.silent, verbose=self.verbose, **kwargs, **data)

    def getPositions(self, subset=None, byName=False, byID=False, returnData=False, **kwargs):
        """Download the positions for the retrieved GRBs.

        This function downloads the positions of the GRBs found when
        this query was executed. Of course, this means you have to have
        executed the query first!

        The position data will be stored in the ``positions``
        variable of this object, and optionally returned as well.

        Parameters
        ----------

        subset : pandas.Series, optional
            A pandas series defining a subset of rows in the query
            results to download.

        byName : bool, optional
            Force the results to be indexed by the GRB name.

        byID : bool, optional
            Force the results to be indexed by targetID.
            Requires that column to have been retrieved by your query.

        returnData : bool, optional
            Whether the position data should be returned by this
            function, as well as saved in the "position"
            variable.

        **kwargs : dict
            Other arguments which are passed to
            ``ukssdc.data.GRB.getPositions()``.
            See its help for more information.

        """
        if not self.haveResults:
            raise RuntimeError("This query has not been executed, cannot download!")

        # Check if we are doing ID or name.
        data = {}
        (whichCol, whichArg) = self._handleArgs(byName=byName, byID=byID)

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

        tmp = dGRB.getPositions(
            silent=self.silent,
            verbose=self.verbose,
            **data,
            **kwargs,
        )

        if self._prodData["positions"] is None:
            self._prodData["positions"] = tmp
        else:
            self._prodData["positions"] = {**self._prodData["positions"], **tmp}

        if returnData:
            return tmp

    def clearPositions(self):
        """Clear self.positions"""
        self._prodData["positions"] = None
