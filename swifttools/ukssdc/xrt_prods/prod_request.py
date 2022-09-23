import requests
import json
from .prod_common import *  # noqa
from .prod_base import ProductRequest
from .productVars import skipGlobals, globalParTriggers
import os
import re
import warnings
import numpy as np
import pandas as pd
from distutils.version import StrictVersion
from .version import _apiVersion
from ..data import download as dl
from ..main import plotLightCurve as mplot

# from ..ukssdc.data.SXPS import _saveSingleSpectrum

_apiWarned = False
_apiDepWarned = {}
_localDepWarned = {}


def listOldJobs(userID):
    """List all of the jobs you have submitted.

    This asks the server to return a list of all of the jobs you have
    ever submitted using your registered email address (`userID`).

    It returns list of dictionaries, where each entry has the following
    keys:

    * JobID : int - the jobID
    * Name : str - the name you gave to the object
    * DateSubmitted : str - the date you submitted the job (UTC)
    * LightCurve : bool - Whether you requested a light curve
    * Spectrum : bool - Whether you requested a spectrum
    * StandardPos : bool - Whether you requested a standard position
    * EnhancedPos : bool - Whether you requested an enhanced position
    * AstromPos : bool - Whether you requested an astrometric position
    * Image : bool - Whether you requested an image
    * hasProd : bool - Whether the products are still available on the server

    Parameters
    ----------
    userID : str
        Your username.

    Returns
    -------
    list
        The list of your previous jobs, described above, most recent
        first.

    Raises
    ------
    RuntimeError
        If the server does not return the expected data.

    """
    jsonDict = {
        "api_name": XRTProductRequest._apiName,
        "api_version": XRTProductRequest._apiVer,
        "UserID": userID,
    }
    submitted = requests.post("https://www.swift.ac.uk/user_objects/listOldJobs.php", json=jsonDict)
    if submitted.status_code != 200:  # Check that this is int!
        raise RuntimeError(f"An HTTP error occured - HTTP return code {submitted.status_code}: {submitted.reason}")

    # OK, submitted alright, now, was it successful?
    # Do I want to try/catch just in case?

    returnedData = json.loads(submitted.text)

    # Request was submitted fine, return is OK, but the return reports an error
    checkAPI(returnedData)

    if returnedData["OK"] == 0:
        if "ERROR" not in returnedData:  # Invalid JSON
            return {
                "submitError": "The server return does not confirm to the expected JSON structure; "
                "do you need do update this module?"
            }

        errString = returnedData["ERROR"] + "\n"
        print(f"ERROR: {errString}")
        return None

    if "jobs" not in returnedData:  # Invalid JSON
        raise RuntimeError(
            "The server return does not confirm to the expected JSON structure; do you need do update this module?"
        )

    # oldJobs=dict()
    # for j in returnedData["jobs"]:
    #     id = str(j.pop("JobID"))
    #     oldJobs[id]=j
    # return oldJobs

    return returnedData["jobs"]


def countActiveJobs(userID):
    """Count how many active jobs you have in the queue.

    This asks the server how many jobs are currently in the queue -
    either running or awaiting execution - with your username.

    Parameters
    ----------
    userID : str
        Your username.

    Returns
    ------
    int
        The number of jobs.

    Raises
    ------
    RuntimeError
        If the server does not return the expected data.

    """
    jsonDict = {
        "api_name": XRTProductRequest._apiName,
        "api_version": XRTProductRequest._apiVer,
        "UserID": userID,
    }
    submitted = requests.post("https://www.swift.ac.uk/user_objects/getNumJobs.php", json=jsonDict)
    if submitted.status_code != 200:  # Check that this is int!
        raise RuntimeError(f"An HTTP error occured - HTTP return code {submitted.status_code}: {submitted.reason}")

    # OK, submitted alright, now, was it successful?
    # Do I want to try/catch just in case?
    returnedData = json.loads(submitted.text)

    # Request was submitted fine, return is OK, but the return reports an error
    checkAPI(returnedData)

    if returnedData["OK"] == 0:
        if "ERROR" not in returnedData:  # Invalid JSON
            return {
                "submitError": "The server return does not confirm to the expected JSON structure; "
                "do you need do update this module?"
            }

        errString = returnedData["ERROR"] + "\n"
        print(f"ERROR: {errString}")
        return -1

    if "numJobs" not in returnedData:  # Invalid JSON
        raise RuntimeError(
            "The server return does not confirm to the expected JSON structure; do you need do update this module?"
        )
    return returnedData["numJobs"]


def checkAPI(returnedData):
    """Carry out some checks on data returned from the server.

    This checks that the API version returned by the server is
    cosistent with the version in this API, and warns if not. It
    also checks that the OK value exists. It does NOT handle the
    case that OK=0 or ERROR is set - that is function-specific.

    """
    if "APIVersion" not in returnedData:  # Invalid JSON
        raise RuntimeError(
            "The server return does not confirm to the expected JSON structure; do you need do update this module?"
        )

    global _apiWarned

    if StrictVersion(str(returnedData["APIVersion"])) > StrictVersion(XRTProductRequest._apiVer):
        if not _apiWarned:
            warnings.warn(
                f"WARNING: you are using version {XRTProductRequest._apiVer} of the xrt_prods API component; "
                f"the latest version is {returnedData['APIVersion']}, it would be advisable to update your version."
            )

    if "deprecationWarning" in returnedData:
        if ("type" not in returnedData["deprecationWarning"]) or ("message" not in returnedData["deprecationWarning"]):
            raise RuntimeError(
                "The server return does not confirm to the expected JSON structure; do you need do update this module?"
            )
        t = returnedData["deprecationWarning"]["type"]
        msg = returnedData["deprecationWarning"]["message"]
        if t not in _apiDepWarned:
            _apiDepWarned[t] = msg
            warnings.warn(f"The server returned the following DEPRECATION WARNING:\n{msg}")


class XRTProductRequest:
    """This is the main class for requesting XRT products.

    To request a product you must be registered with the service,
    register at: https://www.swift.ac.uk/user_objects/register.php

    This object is created with your registered email address.  You add
    to it the products you wish to request, and then submit the request.
    If submission succeeds you can then check up on the status of the
    processing job thus created, cancel it if you wish, and download the
    products on completion.

    Please send feedback, bug reports etc to swifthelp@leicester.ac.uk
    """

    # Some 'static' variables, i.e. only need defining once, not per
    # instance.  These are tuples so that they can't be changed, and
    # they're only designed for use internally, begin with _.

    # The mandatory global variables
    _neededGlobals = ("centroid", "name", "useSXPS", "RA", "Dec", "targ")

    # Some globals are mandatory, but one of two options is mandatory.
    # For example, either "targ" or "getTarg" is needed so here we
    # define the normal parameter (targ) as having an alternate in
    # getTarg.
    _altGlobals = {"targ": "getTargs", "RA": "getCoords", "Dec": "getCoords"}

    # All globals - with their types
    _globalTypes = {
        "name": (str,),
        "targ": (str,),
        "T0": (float, int),
        "SinceT0": (bool,),
        "RA": (float,),
        "Dec": (float,),
        "centroid": (bool,),
        "centMeth": (str,),
        "maxCentTries": (int,),
        "posErr": (float, int),
        "sss": (bool,),
        "useSXPS": (bool,),
        "wtPupRate": (float, int),
        "pcPupRate": (float, int),
        "notify": (bool,),
        "getCoords": (bool,),
        "getTargs": (bool,),
        "getT0": (bool,),
        "posRadius": (float, int),
        "posobs": (str,),
        "useposobs": (str,),
        "posobstime": (float, int),
        "detMeth": (str,),
        "detornot": (str,),
    }

    # Pars which cause the server to do some work to calculate other pars
    _makeWorkPars = ["getCoords", "getTargs", "getT0"]

    # Some parameters I am giving slightly different names in the python
    # API than the main web one.  I may change my mind about this, but I
    # think it makes the Python interface much easier
    _globalPythonParsToJSONPars = {
        "centroid": "cent",
        "T0": "Tstart",
        "posErr": "poserr",
        "wtPupRate": "wtpuprate",
        "pcPupRate": "pcpuprate",
    }
    # Some parameters have to have a specific subset of values, as
    # defined here:
    _globalSpecificParValues = {
        "centMeth": ["simple", "iterative"],
        "posobs": ["all", "user", "hours"],
        "detornot": ["detect", "centroid"],
        "detMeth": ["simple", "iterative"],
    }

    # Some parameters are mandatory if something else is set to true
    # _globalDeps lists this in the form of {a:b} meaning that if a is
    # set then parameters b (always a list, so more than one are
    # allowed) are needed.
    # NB, this is still only for globals, products will have their own
    # equivalent of this.  The only way in which the products are
    # involved here is that some global parameters are needed for
    # certain products
    _globalDeps = {"centroid": {"True": ("posErr",)}, "posobs": {"hours": ("posobstime",), "user": ("useposobs",)}}

    # sharedGlobals are parerameters which are listed under globals but
    # are actually product pars, just shared by some products
    _sharedGlobals = ("posRadius", "posobs", "useposobs", "posobstime", "detMeth", "detornot")

    # Status wil be returned as a code (from 0) and text; here are the textual meanings of the numbers
    _statuses = (
        "Preparing the request",
        "Request submitted",
        "Job finished, all products complete or failed",
        "Error, something has gone wrong",
    )

    # Also set the API name and version, this will not be processed (by
    # default) but may be useful for future debugging
    _apiName = "xrt_prods"
    _apiVer = _apiVersion  # "1.8"
    useDeprecate = True

    # Now begin the instantiated stuff.  First what to output when this
    # instance is entered in an ipython shell.
    def __str__(self):
        str = f"XRTProductRequest object for user `{self.UserID}`, with the following products requested:\n"
        for key in self._productList:
            str = str + f"* {longProdName[key]}\n"
        return str

    def __repr__(self):
        str = "XRTProductRequest object"
        return str

    # Could create a __str__ as well if I want the print(this) to be
    # different from just typing (this) on the cmnd line

    # Constructor - requires the userID
    def __init__(self, user, JSONVals=None, fromServer=False, silent=True, useDeprecate=None, showDepWarnings=True):
        """
        Constructs an XRTProductRequest object.

        Parameters
        ----------

        user : str
            Your User ID, as registered via
            https://www.swift.ac.uk/user_objects/register.php

        JSONVals : str or dict or None, optional
            If this is set then the request will be created with the
            parameters are defined in the JSON dict or string. This
            should be of the correct format, i.e. either that you can
            get from myRequest.jobPars or myRequest.getJSON() - where
            myRequest as an object of this class (default: ``None``).

        fromServer : bool, optional
            Only allowed if JSON is set. This specifies whether the JSON
            is that which was returned by the UKSSDC server upon
            successful submission of a request (True), or that created
            by this class, ready to submit (False). i.e. if the object
            was obtained via myRequest.jobPars this should be true; if
            from myRequest.getJSON() then it should be false.
            (default: ``False``)

        silent : bool, optional
            Whether to suppress output from the various functions
            (default: ``True``).

        useDeprecate : bool or None, optional
            Whether to use the deprecated functionality of this module
            (for details, see the online documentation). If `None`
            this will revert to the `XRTProductRequest.useDeprecate`
            value (default: `None`).

        showDepWarnings : bool, optional
            Whether to print warnings when deprecated functionality is
            used for the first time. Such warnings are printed
            regardless of the ``silent`` property (default: ``True``).

        """
        # _userID is the user, which can only be set at construct time,
        # decorator should prevent more
        self._userID = user
        # _productList is a dictionary which will contain the products
        #  requested, i.e. _productList['lc'] = an XRTLightCurveRequest
        #  instance
        self._productList = dict()
        # Whether this request has been submitted yet
        self._submitted = False
        # The global vars: will be stored in a dictionary, but
        # accessible by individual par name or the property decorator
        self._globalPars = dict()
        # Will hold the jobID, again, decorator access which also
        # prevents setting by the user.
        self._jobID = None
        # Status, related to the _statuses static variable
        self._status = 0
        # The data returned by a successful request submission, again
        # will be read only
        self._retData = dict()
        self._complete = False
        self._lcData = None
        self._sourceList = None
        self._specData = None
        self._oldSpecCols = False
        self._standardPos = None
        self._enhancedPos = None
        self._astromPos = None
        self._silent = silent
        self._depWarning = False
        self._oldLCCols = False

        # Deprecation controls
        self._deprecate = XRTProductRequest.useDeprecate
        if useDeprecate is not None:
            if not isinstance(useDeprecate, bool):
                raise ValueError("Deprecate must be bool or None.")
            self._deprecate = useDeprecate
        self._depVersion = 1.9
        self._showDepWarnings = showDepWarnings

        # Details of functionality:

        self._baseURL = "https://www.swift.ac.uk/user_objects"
        self._funcURL = {
            "submit": "run_userobject.php",
            "cancel": "canceljob.php",
            "checkProductStatus": "checkProductStatus.php",
            "getPSFPos": "tprods/getPSFPos.php",
            "getEnhPos": "tprods/getEnhPos.php",
            "getAstromPos": "tprods/getAstromPos.php",
            "getSourceList": "tprods/getSourceDetResults.php",
            "getLightCurve": "tprods/getLCData.php",
            "getSpectrum": "tprods/getSpecData.php",
            "getOldProduct": "getOldProduct.php",
        }

        # Also create a look up from the par names returned in the JSON
        # to the Python globals shown to the user.  Do this on the flu
        # so I only have one list to maintain, and therefore can't get
        # them out of sync.
        self._JSONParsToGlobalPars = dict()
        for gpar in XRTProductRequest._globalPythonParsToJSONPars:
            jpar = XRTProductRequest._globalPythonParsToJSONPars[gpar]
            self._JSONParsToGlobalPars[jpar] = gpar

        if JSONVals is not None:
            self.setFromJSON(JSONVals, fromServer)

    ##
    # Now some property decorators for read-only varaiables

    # UserID
    @property
    def UserID(self):
        """The registered ID of the user."""
        return self._userID

    @UserID.setter
    def UserID(self, email):
        if self.submitted:
            raise RuntimeError("Cannot change the userID of a request after submission")
        self._userID = email

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
        for what in self._productList.keys():
            self._productList[what].silent = silent

    # deprecate
    @property
    def deprecate(self):
        """Whether to run with deprecated settings active."""
        return self._deprecate

    @deprecate.setter
    def deprecate(self, deprecate):
        if not isinstance(deprecate, bool):
            raise ValueError("deprecate must be a bool")
        self._deprecate = deprecate

    # showDepWarning
    @property
    def showDepWarnings(self):
        """Whether to run with showDepWarningd settings active."""
        return self._showDepWarnings

    @showDepWarnings.setter
    def showDepWarnings(self, showWarn):
        if not isinstance(showWarn, bool):
            raise ValueError("showDepWarning must be a bool")
        self._showDepWarnings = showWarn

    # submitted

    @property
    def submitted(self):
        """Whether the request has been successfully submitted."""
        return self._submitted

    # JobID
    @property
    def JobID(self):
        """JobID assigned on successful submission."""
        if not self.submitted:
            raise RuntimeError("JobID is not set until the request is successfully submitted")
        return self._jobID

    # rebinID
    @property
    def RebinID(self):
        """RebinID assigned on successful submission of a rebin job."""
        return self._rebinID

    # complete
    @property
    def complete(self):
        """Whether all of the build jobs are complete.

        To query an individual product use checkProductStatus.
        """
        if not self.submitted:
            raise RuntimeError("You have not submitted the request, so cannot check if it is complete.")
        if self._complete:  # If it's complete, don't need to check the status
            return True

        # If it's not complete, then do a status check on everything
        # which will update the _complete status
        self.checkProductStatus("all")
        return self._complete

    # retData
    @property
    def subRetData(self):
        """All of the data returned by the server after job submission."""
        return self._retData

    # jobPars
    @property
    def jobPars(self):
        """Dictionary built from subRetData."""
        if not self.submitted:
            raise RuntimeError("jobpars is not set until the request is submitted")
        return self._retData["jobPars"]

    # URL
    @property
    def URL(self):
        """URL where the products will appear."""
        if not self.submitted:
            raise RuntimeError("URL is not set until the request is successfully submitted")
        return self._retData["URL"]

    # submitError
    @property
    def submitError(self):
        """Textual description of why a request submission failed."""
        if self._status != 3:
            raise RuntimeError("There is no submitError unless request submission failed, which it didn't")
        return self._retData["submitError"]

    # all globals
    @property
    def globalPars(self):
        """Dictionary of all global parmeters."""
        return self._globalPars

    # status
    @property
    def status(self):
        """Current status of the job.

        This is a list with two elements describing the status:
        the code, then the textual description.
        """
        return (self.statusCode, self.statusText)

    # statusCode
    @property
    def statusCode(self):
        """Numerical code describing the status."""
        return self._status

    # statusText
    @property
    def statusText(self):
        """Textual description of the status."""
        if self.statusCode < 0 or self.statusCode > len(XRTProductRequest._statuses):
            return "Unknown status"
        else:
            return XRTProductRequest._statuses[self.statusCode]

    # lcData
    @property
    def lcData(self):
        """Dict containing the light curve, if retrieved."""
        return self._lcData

    # specData
    @property
    def specData(self):
        """Dict containing the spectra, if retrieved."""
        return self._specData

    # sourceList
    @property
    def sourceList(self):
        """Dict of source lists as DataFrames, if retrieved."""
        return self._sourceList

    # standardPos
    @property
    def standardPos(self):
        """The standard position dict."""
        return self._standardPos

    # enhancedPos
    @property
    def enhancedPos(self):
        """The enhanced position dict."""
        return self._enhancedPos

    # astromPos
    @property
    def astromPos(self):
        """The astrom position dict."""
        return self._astromPos

    @property
    def productList(self):
        """The list of requested products."""
        return list(self._productList.keys())

    # -----------------------------------------------------------------
    # Pre-submission functions

    # Now the global variables: This is basically a dictionary, but
    # where I have controlled what keys can be set.  I could add a load
    # of property functions as well if I wanted so that you could call
    # this.centroid for example but I think I'd prefer to keep them
    # accessed as "globals" to keep them logically separate This needs
    # to check if the passed parameter(s) are real parameters, and if
    # so, check whether the supplied values are valid.

    # Set a global parameter
    def setGlobalPars(self, **globPars):
        """
        Set one more more of the XRTProduct global parameters.

        Raises a ValueError if an invalid parameter is set, or a
        parameter is set to an invalid value

        Parameters
        ----------

        **globPars : dict
            Sets of parameter = value keywords. Parameter must be a
            valid global parameter.

        Raises
        ------
        ValueError
            If invalid parameter or value is specified.

        TypeError
            If a value passed is the wrong type for the parameter.

        """
        #  Go through everything we were sent.
        # Check that it's a valid parameter
        # Check that it has the right type
        # If it has only specific allowable values, check that it's one of these
        # Set it
        for gvar in globPars:
            val = globPars[gvar]
            if gvar not in XRTProductRequest._globalTypes:
                # They may have used an JSON parameter instead of a python one
                if gvar in self._JSONParsToGlobalPars:
                    gvar = self._JSONParsToGlobalPars[gvar]
                else:
                    raise ValueError(f"{gvar} is not a recognised global parameter")
            if not isinstance(val, XRTProductRequest._globalTypes[gvar]):
                raise TypeError(
                    f"{gvar} should be a {XRTProductRequest._globalTypes[gvar]} but you supplied a {type(val)}."
                )
            if (gvar in XRTProductRequest._globalSpecificParValues) and (
                val not in XRTProductRequest._globalSpecificParValues[gvar]
            ):
                raise ValueError(
                    f"'{val}' is not a valid value for {gvar}. "
                    f"Options are: {','.join(XRTProductRequest._globalSpecificParValues[gvar])}."
                )
            # OK if we got here then we can set it:
            self._globalPars[gvar] = val
            # Are there any dependencies to set?
            if gvar in globalParTriggers:
                if val in globalParTriggers[gvar]:
                    for depPar, depVal in globalParTriggers[gvar][val].items():
                        if depVal is None and depPar in self._globalPars:
                            del self._globalPars[depPar]
                        elif depVal is not None:
                            self._globalPars[depPar] = depVal
                        if not self.silent:
                            print(f"Also setting {depPar} = {depVal}")
                if "ANY" in globalParTriggers[gvar] and val is not None and val != "None":
                    for depPar, depVal in globalParTriggers[gvar]["ANY"].items():
                        if depVal is None and depPar in self._globalPars:
                            del self._globalPars[depPar]
                        elif depVal is not None:
                            self._globalPars[depPar] = depVal
                        if not self.silent:
                            print(f"Also setting global {depPar} = {depVal}")
                if "NONE" in globalParTriggers[gvar] and (val is None or val == "None"):
                    for depar, depVal in globalParTriggers[gvar]["NONE"].items():
                        self._globalPars[depPar] = depVal
                        if not self.silent:
                            print(f"Also setting global {depar} = {depVal}")

    # Get a global parameter
    def getGlobalPars(self, globPar="all", omitShared=True, showUnset=False):
        """Return the current value of the requested global parameter.

        Raises a ValueError if an invalid parameter is requested.

        Parameters
        ----------

        globPar : str
            The parameter to get (default 'all')

        omitShared : bool
            There are some 'shared' variables which are not really
            'global', but are shared between products (this are
            currently only those controlling which data are used to
            generate positions). This parameter controls whether these
            are shown in the returned list of globals. Only relevant if
            globPar=='all'. Default: false

        showUnset : bool
            Only used if globPar is 'all', will include all of the
            global parameters not yet set in the returned dict
            (default: False).

        Returns
        -------

        Multiple
            If a single parameter was specified returns the parameter
            value (or None).
            If all parameters were specified, returns a dict of all
            parameters.

        Raises
        ------

        ValueError
            If `globPar` is not a valid global parameter.

        """
        if globPar == "all":
            ret = dict()
            for par in self._globalTypes:
                if (par not in self.globalPars) and (not showUnset):
                    continue
                skipPar = False
                if omitShared:
                    # Need to check if this parameter is a shared par:
                    skipPar = par in XRTProductRequest._sharedGlobals
                if not skipPar:
                    if par in self.globalPars:
                        ret[par] = self.globalPars[par]
                    else:
                        ret[par] = None
            return ret

        if globPar not in XRTProductRequest._globalTypes:
            raise ValueError(f"`{globPar}` is not a recognised global parameter")
        if globPar in self.globalPars:
            return self.globalPars[globPar]
        else:
            return None

    # isValid returns whether this is ready to submit.
    # To achieve this it must:
    # * Check that all mandatory global Pars are set
    # * Check that any optional global pars are set, if their dependent it set
    # * Check that at least one product is set
    # * Check that each product is OK

    def isValid(self, what="all"):
        """Return whether the jobs is ready to submit.

        This checks whether all of the required parameters are set. It
        does NOT check that the parameter values are valid, so does not
        guarantee that the submission will succeed; those checks are
        carried out by the server upon submission.

        The return is a tuple with two entries:

        * status : bool - Whether or not the request is valid.
        * expln : str - A string explaning why the request is invalid
          (if it is)


        Parameters
        ----------

        what : list or tuple, optional
           A list of the products to check (e.g. ['lc', 'spec' etc] )
           If this is not set, then the validity of the entire request
           is checked.

        Returns
        -------
        tuple
            A 2-element tuple described above.

        Raises
        ------
        ValueError
            If the `what` argument is invalid.

        """
        status = True
        report = ""

        if type(what) == str:
            if what == "all":
                what = self._productList.keys()
            else:
                raise ValueError(f"what should be 'all' or a list/tuple, not `{what}`")

            # Check globals and all prods:
            what = [*self._productList.keys()]
            if len(what) == 0:
                status = False
                report = report = "* No products have been requested.\n"

            # Sometimes a global is not needed. e.g. if sourceDet is
            # the only product, we don't need coords.
            skipPars = []

            if len(what) == 1 and what[0] in skipGlobals:
                skipPars = skipGlobals[what[0]]

            for gpar in XRTProductRequest._neededGlobals:
                if gpar in skipPars:
                    continue

                tmp = self._checkGlobalIsSet(gpar)
                status = status and tmp[0]
                report = report + tmp[1]

            # Now check any dependencies, i.e. parameters where par b is mandatory if par a is set
            for gpar in XRTProductRequest._globalDeps:
                # is par a set?
                if gpar in self.globalPars:
                    # Yes, does its value trigger a dependency?
                    keyVal = self.globalPars[gpar]
                    if str(keyVal) in XRTProductRequest._globalDeps[gpar]:
                        for needPar in XRTProductRequest._globalDeps[gpar][str(keyVal)]:
                            tmp = self._checkGlobalIsSet(needPar)
                            status = status and tmp[0]
                            report = report + tmp[1]
                    # And does gpar have an 'ANY' entry?
                    if "ANY" in XRTProductRequest._globalDeps[gpar]:
                        for needPar in XRTProductRequest._globalDeps[gpar]["ANY"]:
                            tmp = self._checkGlobalIsSet(needPar)
                            status = status and tmp[0]
                            report = report + tmp[1]
        for prod in what:
            if prod in longToShort:
                prod = longToShort[prod]
            prodStat = True
            prodRep = ""
            if not (self.hasProd(prod)):
                prodStat = False
                prodRep = prodRep + f"* You have not requested a {longProdName[prod]}."
            else:
                for gpar in self._productList[prod].needGlobals:
                    tmp = self._checkGlobalIsSet(gpar)
                    prodStat = prodStat and tmp[0]
                    prodRep = prodRep + tmp[1]
                (tmpStat, tmpRep) = self._productList[prod].isValid()
                prodStat = prodStat and tmpStat
                if not tmpStat:
                    prodRep = prodRep + tmpRep
            if not prodStat:
                report = report + f"\n{longProdName[prod]} problems:\n" + prodRep
                status = False

        if not status:
            report = "The following problems were found:\n" + report
        return (status, report)

    # _checkGlobalIsSet checks if a global is set
    def _checkGlobalIsSet(self, gpar):
        """Check if a given global parameter is set.

        (Internal / hidden function).

        This checks if the supplied parameter is set, or if its
        alternative (if there is one) is set.
        Return is a tuple with 2 elements:

        * status : bool - Whether the parameter is found or not
        * report : string - Text to report the absence


        Parameters
        ----------

        gpar : str
            The parameter to check

        Returns
        -------
        tuple
            A 2-element tuple described above.

        """
        status = True
        report = ""
        # If it's not yet set (i.e. in _globalPars) the product isn't valid
        # - unless it has an alternative property which is set
        if (gpar not in self.globalPars) and (
            (gpar not in XRTProductRequest._altGlobals) or (XRTProductRequest._altGlobals[gpar] not in self.globalPars)
        ):
            status = False
            report = report + f"* Global parameter `{gpar}` is not set"
            if gpar in XRTProductRequest._altGlobals:
                report = report + f", and nor is the alternative: `{XRTProductRequest._altGlobals[gpar]}`"
            report = report + ".\n"
        return (status, report)

    # ---------- FUNCTIONS RELATED TO ADDING PRODUCTS TO THE REQUEST ------------

    # First we create the generic functions which will actually do the work,
    # then we will add some friendly 'aliases' for the user.

    # Add a product:

    def addProduct(self, what, clobber=False, **prodArgs):
        """Add a specific product to the request.

        The product is defined by 'what'. If such a product has already
        been added, this will raise a RuntimeError, unless the 'clobber'
        argument is set to True, in which case the existing product will
        be deleted and a new one added.

        If the product type is not recognised a ValueError will be
        raised.

        Any other arguments will be passed to the product constructor.

        Parameters
        ----------

        what : str
            The product to add (lc, spec, psf etc)

        **prodArgs : dict, optional
            Arguments to pass to the product constructor.

        Raises
        ------

        RuntimeError
            If the request has already been submitted, or if the product
            being added already exists, and you have not specified
            `clobber=True`.

        """
        if self.submitted:
            raise RuntimeError(
                "You cannot add a product after request is successfully submitted; you must create a new request"
            )

        if what in longToShort:
            what = longToShort[what]

        # hasProd checks that 'what' is a valid product, and throws an
        # error if not, so don't need to repeat that check here.
        if self.hasProd(what):
            if clobber:
                if not self.silent:
                    print(f"Deleting old {longProdName[what]} request")
                self._removeProcuct(what)
            else:
                raise RuntimeError(
                    f"Can't add a {longProdName[what]} as you already have one."
                    "Remove it or set clobber=True to remove it."
                )

        # Now add the product
        self._productList[what] = ProductRequest(what, self.silent)
        if len(prodArgs) > 0:
            self.setProductPars(what, **prodArgs)

    # Remove a product
    def removeProduct(self, what):
        """Removes the specific product 'what' from the product request.

        Parameters
        ----------

        what : str
            The product to remove (lc, spec, psf etc)

        Raises
        ------

        RuntimeError
            If your request doesn't include the specified product.

        """
        if self.submitted:
            raise RuntimeError(
                "You cannot remove a product from a request after it has been successfully submitted; "
                "did you want to call cancelProducts()"
            )

        if what in longToShort:
            what = longToShort[what]

        # self.hasProd checks that 'what' is a valid product, and throws
        # an error if not, so don't need to repeat that check here.
        if not self.hasProd(what):
            raise RuntimeError(f"Can't remove a {longProdName[what]} as you don't have one!")
        # Remove the product
        del self._productList[what]
        if not self.silent:
            print(f"Successfully removed {longProdName[what]}")

    # Return the product
    def getProduct(self, what):
        """Return the requested product object.

        This is mainly of use for copying the product to another request.
        It will raise a RuntimeError if you haven't added the product
        in question.

        Parameters
        ----------

        what : str
                The product to return

        Returns
        -------

        ProductRequest
            The instance of the product requested.

        Raises
        ------
        RuntimeError
            If the product requested hasn't been added.

        """
        if what in longToShort:
            what = longToShort[what]

        if not self.hasProd(what):
            raise RuntimeError(f"You have not added a {longProdName[what]} to this request!")
        return self._productList[what]

    # Set the parameters
    def setProductPars(self, what, **prodArgs):
        """Set the arguments for a product.

        Set the arguments for the product 'what' to be those in the
        prodArgs list.

        Parameters
        ----------

        what : str
            The product to set the parameters for (lc, spec, psf etc)

        **prodArgs : dict
            The arguments to set

        Raises
        ------

        ValueError
            If invalid values are specified.

        RuntimeError
            If the request has already been submitted, so cannot be
            edited.

        """
        if self.submitted:
            raise RuntimeError(
                "You cannot edit product properties after the request has been successfully submitted; "
                "you must create a new job"
            )

        if what in longToShort:
            what = longToShort[what]

        # Check we have this product?
        if not self.hasProd(what):
            raise RuntimeError(f"Can't set the parameters for  a {longProdName[what]} as you don't have one!")

        # This may send back some globals that need changing, as a dict
        globChange = self._productList[what].setPars(**prodArgs)
        if len(globChange) > 0:
            if not self.silent:
                print("WARNING: Changing some parameters which affect multiple products:")
                for par, val in globChange.items():
                    print(f"      {par} => {val}")
            self.setGlobalPars(**globChange)

        # Run getProductPar now as well (don't print anything), this syncs
        # the shared parameters for the positions
        self.getProductPars(what)

    # get a specific parameter

    def getProductPars(self, what, parName="all", showUnset=False):
        """Return the specified parameter(s).

        Return is a dictionary of par:value pairs, for the requested
        parameters, or all parameters if parName is unspecified or set
        to the string "all"

        It will raise a ValueError 'parName' or 'what' are invalid

        Parameters
        ----------

        what : str
            The product to get the parameter for (lc, spec, psf etc)

        parName
            The parameter to get, if "all" will return a dictionary of
            all parameters

        showUnset : bool
            Only used if parName is 'all', will return all of the
            parameters for this product, even if they have not
            have values explicitly assigned to them (default: False).

        Returns
        -------

        Multiple
            The value of the requested parameter, or a dict of
            parameter:value pairs if 'all' was requested.

        Raises
        ------

        RuntimeError
            If the product requested hasn't been added.

        """
        if what in longToShort:
            what = longToShort[what]

        # Check we have this product
        if not self.hasProd(what):
            raise RuntimeError(f"Can't get the parameters for  a {longProdName[what]} as you don't have one!")

        if parName in self._productList[what].useGlobals:
            newPName = parName
            if newPName in self._productList[what].pythonParsToJSONPars:
                newPName = self._productList[what].pythonParsToJSONPars[newPName]
            return self.getGlobalPars(newPName)

        tmp = self._productList[what].getPars(parName, showUnset)

        if parName == "all":
            for gpar in self._productList[what].useGlobals:
                tpar = gpar
                if tpar in self._productList[what].pythonParsToJSONPars:
                    tpar = self._productList[what].pythonParsToJSONPars[tpar]
                if (tpar in self.globalPars) or showUnset:
                    tmp[gpar] = self.getGlobalPars(tpar)
                elif (tpar not in self.globalPars) and (gpar in tmp):
                    del tmp[gpar]
        return tmp

    def removeProductPar(self, what, parName):
        """Remove (unset) a product parameter.

        Removes the parameter 'parName' from the product 'what'.

        Parameters
        ----------

        what : str
            The product to get the parameter for (lc, spec, psf etc)

        parName
            The parameter to get, if "all" will return a dictionary
            of all parameters

        Raises
        ------

        RuntimeError
            If the parameter or product specified are not valid.

        """
        if what in longToShort:
            what = longToShort[what]

        # Check we have this product
        if not self.hasProd(what):
            raise RuntimeError(f"Can't remove a parameter from a {longProdName[what]} as you don't have one!")
        return self._productList[what].removePar(parName)

    def copyProd(self, what, copyFrom):
        """Copy a product from one request to another.

        Parameters
        ----------

        what : str
            The product type

        copyFrom
            The product you wish to copy. Must be of the correct type.
            i.e. if 'what' is 'lc' then 'copyFrom' must be a
            light curve.

        Raises
        ------

        ValueError
            If the specified product doesn't exist, or doesn't match,
            e.g. if you try to copy a spectrum to a light curve.

        """
        if what in longToShort:
            what = longToShort[what]

        # is what a valid product?
        if not ProductRequest.validType(what):
            raise ValueError(f"The product type {what} does not exist.")

        # is copyfrom a what?
        if not isinstance(copyFrom, ProductRequest):
            raise ValueError("The supplied object to copy from is not a ProductRequest!")
        if copyFrom.prodType != what:
            raise ValueError(
                f"The supplied object to copy is a {longProdName[copyFrom.prodType]}, "
                f"it cannot be assigned to a {longProdName[what]}!"
            )

        self._productList[what] = copyFrom

    def getAllPars(self, showUnset=False):
        """Return all parameters that have been set.

        Return a dictionary of all parameters set so far. The dictionary
        is nested: the top level contains the global parameters and
        an entry for each product. The latter are themselves
        dictionaries of the parameters for that product.

        Parameters
        ----------

        showUnset : bool
            Return all possible parameters, including those not yet set
            (default: False).

        Returns
        -------

        dict
            Dictionary of parameters

        """
        retDict = self.getGlobalPars(omitShared=True)
        for prod in self._productList.keys():
            retDict[shortToLong[prod]] = self.getProductPars(prod, showUnset=showUnset)
        return retDict

    # Now we'll supply some user friendly aliases to these different products, because I'm nice
    # These will be:
    # * A decorated property to allow access, e.g. this.lc (or this.lc=)
    # * Wrappers for add/remove/setPars/getPar

    # ------------------------------------------------------------------
    # -------------- START PRODUCT SPECIFICATIONS ----------------------
    # ------------------------------------------------------------------

    # ----- LIGHT CURVE ------

    # First property getter and setter so that the LC can be accessed as this.LightCurve
    # Getter

    @property
    def LightCurve(self):
        """LightCurve request."""
        return self.getProduct("lc")

    # Remove setter but replace with copyFrom
    # Setter
    @LightCurve.setter
    def LightCurve(self, oldLightCurve):
        self.copyProd("lc", oldLightCurve)

    @property
    def hasLightCurve(self):
        """Whether the current request has a light curve."""
        return self.hasProd("lc")

    def addLightCurve(self, clobber=False, **lcArgs):
        """Add a light curve to the current request.

        A wrapper to `addProduct("lc", clobber, **lcArgs)`.

        """
        self.addProduct("lc", clobber, **lcArgs)

    def removeLightCurve(self):
        """Remove a light curve from te current request.

        A wrapper to `removeProduct("lc")`.

        """
        self.removeProduct("lc")

    def setLightCurvePars(self, **lcPars):
        """Set the light curve parameters.

        A wrapper to `setProductPars("lc", **lcPars)`.

        """
        self.setProductPars("lc", **lcPars)

    def getLightCurvePars(self, parName="all", showUnset=False):
        """Get a light curve parameter.

        A wrapper to `getProductPar('lc', parName, showUnset)`.

        """
        return self.getProductPars("lc", parName, showUnset)

    def removeLightCurvePar(self, parName):
        """Remove a light curve parameter.

        A wrapper to `removeProductPar("lc", parName)`.

        """
        self.removeProductPar("lc", parName)

    # ------ SPECTRUM ------

    # First property getter and setter so that the spectrum can be
    # accessed as this.Spectrum
    # Getter
    @property
    def Spectrum(self):
        """Spectrum request."""
        return self.getProduct("spec")

    # Remove setter but replace with copyFrom
    # Setter
    @Spectrum.setter
    def Spectrum(self, oldSpectrum):
        self.copyProd("spec", oldSpectrum)

    @property
    def hasSpectrum(self):
        """Whether the current request has a spectrum."""
        return self.hasProd("spec")

    def addSpectrum(self, clobber=False, **specArgs):
        """Add a spectrum to the current request.

        A wrapper to `addProduct("spec", clobber, **specArgs)`.

        """
        self.addProduct("spec", clobber, **specArgs)

    def removeSpectrum(self):
        """Remove the spectrum from the current request.

        A wrapper to `removeProduct("spec")`.

        """
        self.removeProduct("spec")

    def setSpectrumPars(self, **specPars):
        """Set the spectrum parameters.

        A wrapper to `setProductPars("spec", **specPars)`.

        """
        self.setProductPars("spec", **specPars)

    def getSpectrumPars(self, parName="all", showUnset=False):
        """Get a spectrum parameter.

        A wrapper to `getProductPar('spec', parName, showUnset)`.

        """
        return self.getProductPars("spec", parName, showUnset)

    def removeSpectrumPar(self, parName):
        """Remove a spectrum parameter.

        A wrapper to `removeProductPar("spec", parName)`.

        """
        self.removeProductPar("spec", parName)

    # ------ STANDARD POSITION ------

    # First property getter and setter so that the LC can be accessed as this.StandardPos
    # Getter
    @property
    def StandardPos(self):
        """Standard position request."""
        return self.getProduct("psf")

    # Remove setter but replace with copyFrom
    # Setter
    @StandardPos.setter
    def StandardPos(self, oldStandardPos):
        self.copyProd("psf", oldStandardPos)

    @property
    def hasStandardPos(self):
        """Whether the current request has a standard position."""
        return self.hasProd("psf")

    def addStandardPos(self, clobber=False, **psfArgs):
        """Add a standard position to the current request.

        A wrapper to `addProduct("psf", clobber, **psfArgs)`.

        """
        self.addProduct("psf", clobber, **psfArgs)

    def removeStandardPos(self):
        """Remove the standard position from the current request.

        A wrapper to `removeProduct("psf")`.

        """
        self.removeProduct("psf")

    def setStandardPosPars(self, **psfPars):
        """Set the standard position parameters.

        A wrapper to `setProductPars("psf", **psfPars)`.

        """
        self.setProductPars("psf", **psfPars)

    def getStandardPosPars(self, parName="all", showUnset=False):
        """Get a standard position parameter.

        A wrapper to `getProductPar('psf', parName, showUnset)`.

        """
        return self.getProductPars("psf", parName, showUnset)

    def removeStandardPosPar(self, parName):
        """Remove a standard position parameter.

        A wrapper to `removeProductPar("psf", parName)`.

        """
        self.removeProductPar("psf", parName)

    # ------ EHHANCED POSITION ------

    # First property getter and setter so that the LC can be accessed as this.EnhancedPos
    # Getter
    @property
    def EnhancedPos(self):
        """Enhanced position request."""
        return self.getProduct("enh")

    # Remove setter but replace with copyFrom
    # Setter
    @EnhancedPos.setter
    def EnhancedPos(self, oldEnhancedPos):
        self.copyProd("enh", oldEnhancedPos)

    @property
    def hasEnhancedPos(self):
        """Whether the current request has an enhanced position."""
        return self.hasProd("enh")

    def addEnhancedPos(self, clobber=False, **enhArgs):
        """Add a enhanced position to the current request.

        A wrapper to `addProduct("enh", clobber, **enhArgs)`.

        """
        self.addProduct("enh", clobber, **enhArgs)

    def removeEnhancedPos(self):
        """Remove the enhanced position from the current request.

        A wrapper to `removeProduct("enh")`.

        """
        self.removeProduct("enh")

    def setEnhancedPosPars(self, **enhPars):
        """Set the enhanced position parameters.

        A wrapper to `setProductPars("enh", **enhPars)`.

        """
        self.setProductPars("enh", **enhPars)

    def getEnhancedPosPars(self, parName="all", showUnset=False):
        """Get an enhanced position parameter.

        A wWrapper to `getProductPar('enh', parName, showUnset)`.

        """
        return self.getProductPars("enh", parName, showUnset)

    def removeEnhancedPosPar(self, parName):
        """Remove an enhanced position parameter.

        A wrapper to `removeProductPar("enh", parName)`.

        """
        self.removeProductPar("enh", parName)

    # ------ ASTROMETRIC POSITION ------

    # First property getter and setter so that the LC can be accessed as this.AstromPos
    # Getter
    @property
    def AstromPos(self):
        """Astrometric position request."""
        return self.getProduct("xastrom")

    # Remove setter but replace with copyFrom
    # Setter
    @AstromPos.setter
    def AstromPos(self, oldAstromPos):
        self.copyProd("xastrom", oldAstromPos)

    @property
    def hasAstromPos(self):
        """Whether the current request has an astrometric position."""
        return self.hasProd("xastrom")

    def addAstromPos(self, clobber=False, **xastromArgs):
        """Add an astrometric position to the current request.

        A wrapper to `addProduct("xastrom", clobber, **xastromArgs)`.

        """
        self.addProduct("xastrom", clobber, **xastromArgs)

    def removeAstromPos(self):
        """Remove the astrometric position from the current request.

        A wrapper to `removeProduct("xastrom")`.

        """
        self.removeProduct("xastrom")

    def setAstromPosPars(self, **xastromPars):
        """Set the astrometric position parameters.

        A wrapper to `setProductPars("xastrom", **xastromPars)`.

        """
        self.setProductPars("xastrom", **xastromPars)

    def getAstromPosPars(self, parName="all", showUnset=False):
        """Get an astrometric position parameter.

        A wrapper to `getProductPar('xastrom', parName, showUnset)`.

        """
        return self.getProductPars("xastrom", parName, showUnset)

    def removeAstromPosPar(self, parName):
        """Remove an astrometric position parameter.

        A wrapper to `removeProductPar("xastrom", parName)`.

        """
        self.removeProductPar("xastrom", parName)

    # ------ IMAGE ------

    # First property getter and setter so that the LC can be accessed as this.Image
    # Getter
    @property
    def Image(self):
        """The image request."""
        return self.getProduct("image")

    # Remove setter but replace with copyFrom
    # Setter
    @Image.setter
    def Image(self, oldImage):
        self.copyProd("image", oldImage)

    @property
    def hasImage(self):
        """Whether the current request has an image."""
        return self.hasProd("image")

    def addImage(self, clobber=False, **imageArgs):
        """Add an image to the current request.

        A wrapper to `addProduct("image", clobber, **imageArgs)`.

        """
        self.addProduct("image", clobber, **imageArgs)

    def removeImage(self):
        """Remove the image from the current request.

        A wrapper to `removeProduct("image")`.

        """
        self.removeProduct("image")

    def setImagePars(self, **imagePars):
        """Set the image parameters.

        A wrapper to `setProductPars("image", **imagePars)`.

        """
        self.setProductPars("image", **imagePars)

    def getImagePars(self, parName="all", showUnset=False):
        """Get an image parameter.

        A wrapper to `getProductPar('image', parName, showUnset)`.

        """
        return self.getProductPars("image", parName, showUnset)

    def removeImagePar(self, parName):
        """Remove an image parameter.

        A wrapper to `removeProductPar("image", parName)`.

        """
        self.removeProductPar("image", parName)

    # ------SOURCE DETECTION ------

    # First property getter and setter so that the sourceDet can be accessed as this.SourceDet
    # Getter
    @property
    def SourceDet(self):
        """SourceDet request."""
        return self.getProduct("sourceDet")

    # Remove setter but replace with copyFrom
    # Setter
    @SourceDet.setter
    def SourceDet(self, oldSourceDet):
        self.copyProd("sourceDet", oldSourceDet)

    @property
    def hasSourceDet(self):
        """Whether the current request has a source detect."""
        return self.hasProd("sourceDet")

    def addSourceDet(self, clobber=False, **sourceDetArgs):
        """Add a source detect to the current request.

        A wrapper to `addProduct("sourceDet", clobber, **sourceDetArgs)`.

        """
        self.addProduct("sourceDet", clobber, **sourceDetArgs)

    def removeSourceDet(self):
        """Remove a source detect from te current request.

        A wrapper to `removeProduct("sourceDet")`.

        """
        self.removeProduct("sourceDet")

    def setSourceDetPars(self, **sourceDetPars):
        """Set the source detect parameters.

        A wrapper to `setProductPars("sourceDet", **sourceDetPars)`.

        """
        self.setProductPars("sourceDet", **sourceDetPars)

    def getSourceDetPars(self, parName="all", showUnset=False):
        """Get a source detect parameter.

        A wrapper to `getProductPar('sourceDet', parName, showUnset)`.

        """
        return self.getProductPars("sourceDet", parName, showUnset)

    def removeSourceDetPar(self, parName):
        """Remove a source detect parameter.

        A wrapper to `removeProductPar("sourceDet", parName)`.

        """
        self.removeProductPar("sourceDet", parName)

    # ------------------------------------------------------------------
    # --------------- END OF PRODUCT SPECIFICATIONS ---------------------
    # ------------------------------------------------------------------

    # Check how many active jobs this user has
    def countActiveJobs(self):
        """Count how many jobs the user has actively in the queue.

        This asks the server how many jobs are currently in the queue -
        either running or awaiting execution - with your username.
        Just a wrapper to call xrt_prods.countActiveJobs().

        Parameters
        ----------
        None

        Returns
        -------
        int
            The number of jobs.

        """
        return countActiveJobs(self.UserID)

    # Get details of old jobs
    def listOldJobs(self):
        """List all of the jobs you have submitted.

        A wrapper to call xrt_prods.listOldJobs().

        Parameters
        ----------
        None

        Returns
        -------

        list
            A list of your old jobs. See xrt_prods.listOldJobs() for
            details.

        """
        return listOldJobs(self.UserID)

    # ----------- END OF PRODUCT ADDING SECTION -----------

    # ----------- FUNCTIONS FOR SUBMITTING THE JOB -----------

    # First, we need to build the JSON. This will work by going through
    # the global variables first, converting any argument names as
    # necessary, and copying them into a dictionary, then it will merge
    # that with the dictionary that we get from each product.

    def getJSONDict(self):
        """Get the data to upload.

        This returns the dictionary of values to upload to the server,
        built from the current request configuration.

        This does *not* submit the request.

        Returns
        -------
        dict
            The dictionary which will be converted to JSON.

        """

        jsonDict = {
            "api_name": XRTProductRequest._apiName,
            "api_version": XRTProductRequest._apiVer,
            "UserID": self.UserID,
        }
        # Go through globals:
        for gPar in self.globalPars:
            val = self.globalPars[gPar]
            # Bools need converting to 0/1
            if type(val) == bool:
                if val:
                    val = 1
                else:
                    val = 0
            # Do we change the par name for JSON?
            if gPar in XRTProductRequest._globalPythonParsToJSONPars:
                jsonDict[XRTProductRequest._globalPythonParsToJSONPars[gPar]] = val
            else:
                jsonDict[gPar] = val

        for prod in self._productList:
            jsonDict[classReqPar[prod]] = 1
            jsonDict = {**jsonDict, **self._productList[prod].getJSONDict()}

        return jsonDict

    def getJSON(self):
        """Get the JSON-formatted string to upload.

        This calls getJSONDict(), and then converts the dictionary
        returned into a JSON string.

        Returns
        -------
        str
            The JSON object (in string format)

        """
        return json.dumps(self.getJSONDict())

    def _submitAPICall(self, data, func, minKeys=None):
        """Function to submit an API query and do simple validation.

        This function is designed for internal use by codes within the
        XRTProductRequest class; it is not intended for public use.

        This is a simple function to handle all the interaction with the
        back-end servers. It prepares and sends the function, checks the
        returned data are OK (raising a RuntimeError if not) and handles
        things like warning of old API versions of deprecation.

        Parameters
        ----------
        data : dict
            A JSON dictionary to send to the server.

        func : str
            The function to be carried out.

        minKeys: tuple, optional
            A list of minimum keys that must be included in the return
            from the server. Default: None. NB, the "OK" key will ALWAYS
            be needed.

        Returns
        -------

        dict
            The set of returned data. If an error occurred then this
            will contain key "ERROR" with a message.

        """
        data["api_name"] = XRTProductRequest._apiName
        data["api_version"] = XRTProductRequest._apiVer
        if func not in self._funcURL:
            raise ValueError(f"`{func}` is not a valid function call.")

        url = f"{self._baseURL}/{self._funcURL[func]}"

        submitted = requests.post(url, json=data)

        if submitted.status_code != 200:  # Check that this is int!
            return {"ERROR": f"An HTTP error occured - HTTP return code {submitted.status_code}: {submitted.reason}"}

        # OK, submitted alright, now, was it successful?
        # Do I want to try/catch just in case?
        returnedData = json.loads(submitted.text)

        if "OK" not in returnedData:  # Invalid JSON
            raise RuntimeError(
                "The server return does not confirm to the expected JSON structure; do you need do update this module?"
            )

        # Check the API - that is not a class function - and give deprecation warning if need be
        checkAPI(returnedData)

        # Check for an error
        if returnedData["OK"] == 0:
            if "ERROR" not in returnedData:  # Invalid JSON
                return {
                    "ERROR": "The server return does not confirm to the expected JSON structure; "
                    "do you need do update this module?"
                }

            errString = self._fixErrString(returnedData["ERROR"]) + "\n"
            if "listErr" in returnedData:
                for err in returnedData["listErr"]:
                    errString = errString + self._fixErrString(err["label"]) + "\n"
                    for terr in err["list"]:
                        errString = errString + self._fixErrString(f"* {terr}\n")

            return {"ERROR": errString}

        if minKeys is not None:
            bad = []
            for k in minKeys:
                if k not in returnedData:
                    bad.append(k)
            if len(bad) > 0:
                msg = (
                    "Several required properties were missing from the data returnedDataurned by the server.\n"
                    "This may mean that your swifttools version is out of date.\n"
                    "If you have the latest version, please contact swift-help@leicester.ac.uk. The missing keys are\n"
                )
                msg = msg + ", ".join(bad) + "\n"
                return {"ERROR": msg}

        # If we got here, then all is OK, so just returnedDataurn the dict we decoded from JSON
        # but first remove the keys we've handled.
        returnedData.pop("OK", None)
        returnedData.pop("APIVersion", None)

        return returnedData

    # Do the submission
    def submit(self, updateProds=True):
        """Submit the job to the UKSSDC server.

        This carries out the actual job submission. It checks that the
        request is valid, and if so, submits it.  It parses the data
        returned by the UKSSDC servers and adds them to this object.
        (e.g. the JobID, UserID, URL, etc will be set; or submitError
        will be set on failure).

        By default, if the submission is successful it will update the
        properties of the requested products.  That is, any values you
        did not supply will have the accepted defaults completed, and
        any calculated values (e.g. position, targetIDs) will also be
        saved, with the request to calculate disabled.  This allows you
        to use this request as a template for another.

        Parameters
        ----------

        updateProds : bool  (default: True)
            Whether or not the product definitions in this request
            should be updated to have the derived or
            default parameters added.

        Returns
        -------

        bool
            True if the request was submitted and accepted by the
            server, otherwise false. On failure the 'submitError'
            attribute of this request object will be set to the
            error message.

        Raises
        ------

        RuntimeError
            If the request has already been submitted.

        """
        if self._submitted:
            raise RuntimeError("Cannot submit a request that has already been submitted.")

        # Clear retData, in case we had a previous submit attempt
        self._retData = dict()
        # Likewise ensure that this is not complete, as it isn't!
        self._complete = False
        self._retData["submitError"] = None

        valid = self.isValid()
        if not valid[0]:
            return self._submitFail("The request is not ready to submit:\n\n" + valid[1])

        returnedData = self._submitAPICall(self.getJSONDict(), "submit", minKeys=("URL", "JobID", "jobPars"))
        if "ERROR" in returnedData:
            return self._submitFail(returnedData["ERROR"])

        self._status = 1
        self._submitted = True  # Woo! It worked
        self._jobID = returnedData["JobID"]
        self._retData["URL"] = returnedData["URL"]
        self._retData["jobPars"] = returnedData["jobPars"]
        if not self.silent:
            print(f"Job submitted OK, with ID: {self._jobID}")

        if updateProds:
            try:
                # The _makeWorkPars will not be in return, and we want to
                # remove them from here as well, because otherwise in a new
                # submission they would override the values
                for par in XRTProductRequest._makeWorkPars:
                    if par in self.globalPars:
                        del self.globalPars[par]
                self._setFromJSON(self._retData["jobPars"], True)
            except Exception:
                warnings.warn("The job was submitted OK, but an error occured updating the parameters.")
        return True

    def _submitFail(self, msg):
        self._status = 3
        self._retData["submitError"] = msg
        return False

    # This will go through every word in a string and change the JSON
    # names to Python names

    def _fixErrString(self, fixMe):
        """Convert JSON parameter names to python parameter names.

        Parameters
        ----------

        fixMe : str
            String to fix

        Returns
        -------

        Corrected string

        """
        retString = ""
        for word in fixMe.split(" "):
            extra = ""
            m = re.search(r"([^\w]+)$", word)
            if m:
                extra = m.group(1)
                word = re.sub(r"[^\w]+$", "", word)
            if word in self._JSONParsToGlobalPars:
                word = self._JSONParsToGlobalPars[word]
            else:
                for what in self._productList.keys():
                    if word in self._productList[what]._JSONParsToPythonPars:
                        word = f"{shortToLong[what]}: {self._productList[what]._JSONParsToPythonPars[word]}"
            retString = retString + word + extra + " "

        return retString

    # -------- END OF FUNCTIONS FOR SUBMITTING THE JOB --------

    # -------- FUNCTIONS FOR MANIPULATING THE SUBMITTED JOB --------

    # Utility function to convert the user-supplied 'what' for cancel/query, into the list of products for the
    # 'what' field in the JSON

    def _getWhatList(self, what):
        """Return a list of products in interal key form.

        Internal function - this takes a list of products, or 'all',
        and produces a list of the internal keys used to identify the
        designated products. Throws a ValueError if the requested
        product has not been selected or isn't recognised.

        Parameters
        ----------

        what : str or list
            Either the string "all" (the default) or a list of products.

        Returns
        -------

        list
            A list of the products with the internal keys.

        """
        if type(what) == str:
            if what == "all":
                what = self._productList.keys()
            else:
                raise ValueError(f"what should be 'all' or a list/tuple, not `{what}`")

        elif type(what) not in [list, tuple]:
            raise ValueError(f"what should be 'all', or a list/tuple. It is of type {type(what)} which is not valid")

        # Lets just check that everything in what is valid and was requested:
        reqWhat = []
        for prod in what:
            # May need to convert long name into short name
            if prod in longToShort:
                prod = longToShort[prod]
            if not self.hasProd(prod):
                raise ValueError(f"You did not request a {prod}!")
            reqWhat.append(prod)

        return reqWhat

    def cancelProducts(self, what="all"):
        """Cancel some requested products.

        This function can only be called one the request has been
        submitted successfully. It asks the UKSSDC servers to cancel
        one more more of the requested products.

        The return value is a tuple of (status,cancelStatus), defined
        thus:

        status : int - a status code:
        : -1 = HTTP/other error
        :  0 = error in cancellation
        :  1 = success
        :  2 = partial success, not all jobs were cancelled.
        cancelStatus: dict.

        The nature of the cancelStatus dictionary depends on the success
        status. If the job was unsuccessful (code <=0) then this contains a
        single entry: ERROR, describing the problem.

        Otherwise, it contains an entry for each product you
        requested to cancel, each of which is also a dictionary with
        entries "code" and "text". The latter describes the status
        of the attempt to cancel the job, the former gives a numeric
        code defined in the main API documentation.

        Parameters
        ----------

        what : str or list
            Either the string "all" (the default) or a list of products
            to cancel (default: "all").

        Returns
        -------

        tuple
            Defined above.

        Raises
        ------

        RuntimeError
            If the request has not been submitted, or the job is no
            longer running.

        """
        if not self.submitted:
            raise RuntimeError("Can't cancel this request as it hasn't been submitted!")
        if self.statusCode != 1:
            raise RuntimeError("Can't cancel this request as it doesn't correspond to a running job")

        reqWhat = self._getWhatList(what)

        if len(reqWhat) == 0:
            raise ValueError("You have not requested any products to cancel")

        # Make the request as a dictionary and then convert that to JSON as it removes any typos in the JSON by me, here
        jsonDict = {
            "UserID": self.UserID,
            "JobID": self.JobID,
            "what": ",".join(reqWhat),
        }

        returnedData = self._submitAPICall(jsonDict, "cancel", minKeys=("status", "statusCodes"))
        if "ERROR" in returnedData:
            return (-1, returnedData)

        # OK got here;
        retDict = dict()
        for prod in reqWhat:
            if (prod not in returnedData["statusCodes"]) or (prod not in returnedData["status"]):
                return (
                    -1,
                    {
                        "ERROR": "The server return does not confirm to the expected JSON structure; "
                        "do you need do update this module?"
                    },
                )
            retDict[shortToLong[prod]] = {
                "code": returnedData["statusCodes"][prod],
                "text": returnedData["status"][prod],
            }

        return (1, retDict)
        # If submission is OK then go through all prods in what again
        # and get the status etc, and put this into cancelStatus but
        # with the long keys, not the short ones.

    # For getting the status I'm going to have a few functions.
    # The main one is updateJobStatus() - deliberately "job" because this
    # has now been submitted so it's a job, not a request

    def checkProductStatus(self, what="all"):
        """Check the status of your submitted job.

        This can only be called once your request has been successfully
        submitted. It checks the status of the products specified in
        what (default: 'all'), and returns a dictionary with one entry
        per product, giving the progress.

        If called with 'all' then this will update the 'complete'
        variable.

        The dictionary returned has the following entries:

        statusCode : int
            :A code indicating the status of the job - see the API
            documentation for a description. A code of -10 indicates
            that the status was not reported by the server.
        statusText : str
            :A textual description of the job status.
        progress : dict
            :A dictionary describing the details of the progress -
            see the API documentation for a description.
        progressText : str
            :A human-readable string describing the details of the
            progress, formatted as a list, deduced from the 'progress'
            entry.

        Parameters
        ----------

        what : str or list
            Either the string "all" (the default) or a list of products
            to check (default: all)

        Returns
        -------

        dict
            Described above - or with the entry "ERROR" if an error
            occurred.

        Raises
        ------

        RuntimeError
            If the request has not been submitted, or the job is no
            longer running.

        """
        if not self.submitted:
            raise RuntimeError("Can't query this request as it hasn't been submitted!")
        if self.statusCode != 1 and self.statusCode != 2:
            # raise RuntimeError("Can't query this request as it doesn't correspond to a running job")
            return self.statusCode

        reqWhat = self._getWhatList(what)

        if len(reqWhat) == 0:
            raise ValueError("You have not identified any products to query")

        qprodList = ",".join(reqWhat)
        # Make the request as a dictionary and then convert that to JSON as it removes any typos in the JSON by me, here
        jsonDict = {
            "UserID": self.UserID,
            "JobID": self.JobID,
            "what": qprodList,
            "whatProg": qprodList,
        }
        returnedData = self._submitAPICall(jsonDict, "checkProductStatus")
        if "ERROR" in returnedData:
            return returnedData

        # Now go through each requested product and add them to the dict to return
        allDone = True  # Will set this to false for any product that is not complete
        retDict = dict()
        for prod in reqWhat:
            if prod in returnedData:
                # Will be a dict already
                retDict[shortToLong[prod]] = returnedData[prod]
                if returnedData[prod]["progress"]["GotProgress"] == 1:
                    retDict[shortToLong[prod]]["progressText"] = self._buildProgressString(
                        returnedData[prod]["progress"]
                    )
                else:
                    retDict[shortToLong[prod]]["progressText"] = "No progress information available"
                status = int(returnedData[prod]["statusCode"])
                if status < 0 or status == 4:  # Complete
                    self._productList[prod].complete = True
                else:
                    allDone = False
            else:
                retDict[shortToLong[prod]] = {
                    "statusCode": -10,
                    "statusText": "The server did not return the status",
                    "progress": {},
                    "progressText": "No progress information available",
                }
                allDone = False

        # If the request was for 'all' then check if they are complete,
        # and update self._complete (True) and self._status (2) if so
        if (what == "all") and allDone:
            self._complete = True
            self._status = 2

        return retDict

    # Function to build the progress string
    # Based on the javascript used to create the progress reports on the web page
    def _buildProgressString(self, progress):
        """Construct a textual description of the product progress.

        This internal function builds the textual description of the
        progress of a product from the 'progress' object within the
        the JSON returned by the server.

        Parameters
        ----------

        progress : dict
            The dictionary built from the 'progress' object in the
            JSON returned by a job query request

        Returns
        ------

        str
            A description of the progress.

        """
        retString = ""
        if "PreProgress" in progress:
            retString = retString + progress["PreProgress"] + "\n"
        if "ProgressSteps" in progress:
            retString = retString + self._showProgressList(progress["ProgressSteps"])
        if "TimeRunning" in progress:
            retString = retString + f"\nThe job has been running for {progress['TimeRunning']}\n"
        return retString

    # The recursive function to write the progress
    def _showProgressList(self, steps, prefix="  "):
        """Recursively build the progress text.

        Internal function called by _buildProgressString to take a given
        progress step and convert it into text.

        Parameters
        ----------

        steps : list
            The list of steps
        prefix : str
            The current prefix to print before each line

        Returns
        -------
        str
            A string describing these steps

        """
        retString = ""
        for i in steps:
            retString = retString + prefix
            if i["StepStatus"] == 1:
                retString = retString + "** "
            retString = retString + i["StepLabel"]
            if i["StepStatus"] == 1:
                retString = retString + " - ACTIVE"
                if "StepExtra" in i:
                    retString = retString + " -- " + i["StepExtra"]
                retString = retString + "**"
            elif i["StepStatus"] == 2:
                retString = retString + " - DONE"
            retString = retString + "\n"
            # Sub steps?
            if "SubStep" in i:
                retString = retString + self._showProgressList(i["SubStep"], "  " + prefix)

        return retString

    # -------- END OF  FOR MANUPULATING THE JOB --------

    # -------- FUNCTIONS FOR GETTING THE PRODUCTS --------

    def downloadProducts(self, dir, what="all", silent=True, format="tar.gz", stem=None, clobber=False):
        """Retrieve completed products.

        This downloads the data for completed products into the
        specified directory.  If 'what' is 'all' it will only try to
        download products which are complete.  If 'what' is a list of
        specific products this will raise a ValueError if you request a
        product which is not complete.

        Parameters
        ----------

        dir : str
            The  directory into which the products will be downloaded.

        what : str or list
            Either the string "all" (the default) or a list of products
            to check (default: all).

        format: str
            The format to download the file in; see API documentation
            for options (default: tar.gz).

        silent : bool
            Whether to suppress status output to STDOUT (default: False)

        clobber : bool
            Whether the downloaded files can overwrite existing ones
            (default: False).

        stem : str
            An optional string to prepend to the downloaded filenames
            (default: None)

        Returns
        -------

        dict
            A dictionary with an entry for each requested product,
            either set to None (if the product was incomplete), a string
            giving the path to the downloaded file, or the string
            "ERROR: $msg" where $msg is the reason that the product was
            not downloaded.

        Raises
        ------

        ValueError
            If the product requested is not complete.

        """
        if stem is not None and type(stem) != str:
            raise TypeError(f"Stem must be str or None, cannot be {type(stem)}")

        if format not in downloadFormats:
            raise ValueError(f"{format} is not a valid format. Options are: {downloadFormats}")

        reqWhat = self._getWhatList(what)

        # Create the directory
        if not os.path.isdir(dir):
            os.mkdir(dir)

        retDict = dict()
        for prod in reqWhat:
            if not (self._productList[prod].complete):
                if what == "all":  #  OK, just skip:
                    retDict[shortToLong[prod]] = None
                else:
                    raise ValueError(f"The {longProdName[prod]} is not complete, so can't be downloaded")
            else:
                retDict[shortToLong[prod]] = self._productList[prod].downloadProd(
                    self.URL, dir, format, clobber, silent, stem
                )

        return retDict

    def retrieveStandardPos(self, returnData=None):
        """Get the standard position.

        This function queries the server for the standard position and
        if available stores it in a ``dict``.

        This is saved to the ``standardPos`` class variable and
        (optionally) returned.

        The ``dict`` contains these keys:

        GotPos : bool
        : Whether a position was retrieved.

        If GotPos is True then the following keys are present:

        RA : float
        : The RA (J2000) in decimal degrees.

        Dec : float
        : The declination (J2000) in decimal degrees.

        Err90 : float
        : The 90% confidence radial postion error, in arcseconds.

        FromSXPS : bool
        : Whether the position was taken from an SXPS catalogue instead
        of being calculated afresh.

        WhichSXPS : str
        : Which SXPS catalogue the position came from (only if FromSXPS
        is True)

        If GotPos was False then the following key is present:

        Reason : str
        : The reason no position was retrieved.

        Parameters
        ----------

        returnData : bool, optional
            Whether this function should return the downloaded data
            (default: ``False``).


        Returns
        -------

        dict
            A dictionary with the position and information as described
            above.

        Raises
        ------

        RuntimeError
            If the job has not been submitted, or didn't contain a
            standard position.

        """
        if not self.submitted:
            raise RuntimeError("Can't query this request as it hasn't been submitted!")
        if not self.hasProd("psf"):
            raise RuntimeError("Can't retrieve the standard position as none was requested.")

        if returnData is None:
            returnData = self.deprecate
            if not self._depWarning:
                self._depWarning = True
                print(
                    "DEPRECATION WARNING: In the future this function will not return the position, unless "
                    "called with returnData=True. The position will still be stored in the self.standardPos variable."
                )

        self._status = self.checkProductStatus(("psf",))

        jsonDict = {
            "UserID": self.UserID,
            "JobID": self.JobID,
        }

        returnedData = self._submitAPICall(jsonDict, "getPSFPos")

        if "ERROR" in returnedData:
            self._standardPos = None
            if returnedData:
                return {
                    "GotPos": False,
                    "Reason": returnedData["ERROR"],
                }

        returnedData["GotPos"] = bool(returnedData["GotPos"])
        if returnedData["GotPos"]:  # Position found
            returnedData["FromSXPS"] = bool(returnedData["FromSXPS"])
        else:
            returnedData["Reason"] = "No position could be determined."

        self._standardPos = returnedData
        if returnData:
            return returnedData

    def retrieveEnhancedPos(self, returnData=None):
        """Get the enhanced position.

        This function queries the server for the standard position and
        if available stores it in a ``dict``.

        This is saved to the ``enhancedPos`` class variable and
        (optionally) returned.

        The `dict` contains the following:

        GotPos : bool
        : Whether a position was retrieved.

        If GotPos is True then the following keys are present:

        RA : float
        : The RA (J2000) in decimal degrees.

        Dec : float
        : The declination (J2000) in decimal degrees.

        Err90 : float
        : The 90% confidence radial postion error, in arcseconds.

        If GotPos was False then the following key is present:

        Reason : str
        : The reason no position was retrieved.

        Parameters
        ----------

        returnData : bool, optional
            Whether this function should return the downloaded data
            (default: ``False``).

        Returns
        -------

        dict
            A dictionary with the position and information as described
            above.

        Raises
        ------

        RuntimeError
            If the job has not been submitted, or didn't contain a
            enhanced position.

        """
        if not self.submitted:
            raise RuntimeError("Can't query this request as it hasn't been submitted!")
        if not self.hasProd("enh"):
            raise RuntimeError("Can't retrieve the enhanced position as none was requested.")

        if returnData is None:
            returnData = self.deprecate
            if not self._depWarning:
                self._depWarning = True
                print(
                    "DEPRECATION WARNING: In the future this function will not return the position, unless "
                    "called with returnData=True. The position will still be stored in the self.enhancedPos variable."
                )

        jsonDict = {
            "UserID": self.UserID,
            "JobID": self.JobID,
        }

        returnedData = self._submitAPICall(jsonDict, "getEnhPos")

        if "ERROR" in returnedData:
            self._standardPos = None
            if returnedData:
                return {
                    "GotPos": False,
                    "Reason": returnedData["ERROR"],
                }

        returnedData["GotPos"] = bool(returnedData["GotPos"])
        if not returnedData["GotPos"]:  # No position found
            returnedData["Reason"] = "No position could be determined."

        self._enhancedPos = returnedData
        if returnData:
            return returnedData

    def retrieveAstromPos(self, returnData=None):
        """Get the astrometric position.

        This function queries the server for the standard position and
        if available stores it in a ``dict``.

        This is saved to the ``astromPos`` class variable and
        (optionally) returned.

        The `dict` contains the following:

        GotPos : bool
        : Whether a position was retrieved.

        If GotPos is True then the following keys are present:

        RA : float
        : The RA (J2000) in decimal degrees.

        Dec : float
        : The declination (J2000) in decimal degrees.

        Err90 : float
        : The 90% confidence radial postion error, in arcseconds.

        If GotPos was False then the following key is present:

        Reason : str
        : The reason no position was retrieved.

        Parameters
        ----------

        returnData : bool, optional
            Whether this function should return the downloaded data
            (default: ``False``).

        Returns
        -------

        dict
            A dictionary with the position and information as described
            above.

        Raises
        ------

        RuntimeError
            If the job has not been submitted, or didn't contain a
            enhanced position.

        """
        if not self.submitted:
            raise RuntimeError("Can't query this request as it hasn't been submitted!")
        if not self.hasProd("xastrom"):
            raise RuntimeError("Can't retrieve the enhanced position as none was requested.")

        if returnData is None:
            returnData = self.deprecate
            if not self._depWarning:
                self._depWarning = True
                print(
                    "DEPRECATION WARNING: In the future this function will not return the position, unless "
                    "called with returnData=True. The position will still be stored in the self.astromPos variable."
                )

        jsonDict = {
            "UserID": self.UserID,
            "JobID": self.JobID,
        }

        returnedData = self._submitAPICall(jsonDict, "getAstromPos")

        if "ERROR" in returnedData:
            self._standardPos = None
            if returnedData:
                return {
                    "GotPos": False,
                    "Reason": returnedData["ERROR"],
                }

        returnedData["GotPos"] = bool(returnedData["GotPos"])
        if returnedData["GotPos"]:  # Position found
            returnedData["FromSXPS"] = bool(returnedData["FromSXPS"])
        else:
            returnedData["Reason"] = "No position could be determined."

        self._astromPos = returnedData

        if returnData:
            return returnedData

    def retrieveSourceList(self, returnData=None):
        """Get the sources found by source detection

        This function queries the server for the list of sources found
        in source detection and if available stores it in a ``dict``.

        This is saved to the ``sourceList`` class variable and
        (optionally) returned.

        The ``dict`` contains the following keys:

        * total
        * soft
        * medium
        * hard

        (the latter three only present if all energy bands were made).
        Each entry is a list, one entry per source detected in that
        band. The list is itself made up of dicts, giving the source
        detection details.

        If an error occured the return dict will just have entries:
        * ERROR = true
        * Reason = description of the error.

        Returns
        -------

        dict
            A dictionary with the source information.

        Parameters
        ----------

        returnData : bool, optional
            Whether this function should return the downloaded data
            (default: ``False``).

        Raises
        ------

        RuntimeError
            If the job has not been submitted, or didn't contain a
            standard position.

        """
        if not self.submitted:
            raise RuntimeError("Can't query this request as it hasn't been submitted!")
        if not self.hasProd("sourceDet"):
            raise RuntimeError("Can't retrieve the source list as none was requested.")

        if returnData is None:
            returnData = self.deprecate
            if not self._depWarning:
                self._depWarning = True
                print(
                    "DEPRECATION WARNING: In the future this function will not return the source list, unless "
                    "called with returnData=True. The source list will still be stored in the self.sourceList variable."
                )

        self._status = self.checkProductStatus(("sourceDet",))

        jsonDict = {
            "UserID": self.UserID,
            "JobID": self.JobID,
        }

        returnedData = self._submitAPICall(jsonDict, "getSourceList")

        if "ERROR" in returnedData:
            return {"ERROR": True, "Reason": returnedData["ERROR"]}

        self._sourceList = {}

        # Now convert everything I can into numbers:
        for band in returnedData:
            self._sourceList[band] = pd.DataFrame(returnedData[band])
            for src in range(len(returnedData[band])):
                for par in returnedData[band][src]:
                    v = returnedData[band][src][par]
                    if re.search(r"\d", v):
                        if re.search(r"\.", v):
                            returnedData[band][src][par] = float(returnedData[band][src][par])
                        else:
                            returnedData[band][src][par] = int(returnedData[band][src][par])

        if returnData:
            return returnedData

    def retrieveLightCurve(self, nosys="no", incbad="no", returnData=None):
        """Get the light curve data

        This function queries the server for the light curve, and
        onbtains a ``dict`` with the results, conforming to the standard
        light curve ``dict`` of this module. This is saved to the
        ``lcData`` class variable and (optionally) returned.

        On failure, the dict will contain: ERROR and Reason.

        Parameters
        ----------

        nosys : str
            Whether to return the light curves from which the WT
            systematic error has been removed. Can be 'yes', 'no',
            'both' -- the latter returning datasets with and without the
            systematic error (default: 'no').

        incbad : str
            Whether to return the light curves in which the datapoints
            flagged as potentially unreliable to due centroiding issues
            have been included. Can be 'yes', 'no', 'both' -- the latter
            returning datasets with and without the unreliable
            datapoints (default: 'no').

        returnData : bool, optional
            Whether this function should return the downloaded data
            (default: ``False``).

        Returns
        -------

        dict
            A dictionary with the light curve information as described
            above.

        Raises
        ------

        RuntimeError
            If the job has not been submitted, or didn't contain a
            light curve.

        """
        if not self.submitted:
            raise RuntimeError("Can't query this request as it hasn't been submitted!")
        if not self.hasProd("lc"):
            raise RuntimeError("Can't retrieve the light curve as none was requested.")

        oldCols = self.deprecate
        oldKeys = self.deprecate

        if returnData is None:
            returnData = self.deprecate
            if self.deprecate and self.showDepWarnings and ("lcReturn" not in _localDepWarned):
                warnings.warn(
                    "DEPRECATION WARNING: In the future this function will not return the light curve, unless "
                    "called with returnData=True. The light curve will still be stored in the self.lcData variable."
                )
                _localDepWarned["lcReturn"] = True

        # Another backwards compatibility this
        if isinstance(nosys, bool):
            if nosys:
                nosys = "yes"
            else:
                nosys = "no"

        if isinstance(incbad, bool):
            if incbad:
                incbad = "yes"
            else:
                incbad = "no"

        jsonDict = {"UserID": self.UserID, "JobID": self.JobID, "nosys": nosys, "incbad": incbad}

        returnedData = self._submitAPICall(jsonDict, "getLightCurve", minKeys=("Datasets",))

        if "ERROR" in returnedData:
            return {"ERROR": True, "Reason": returnedData["ERROR"]}

        # May have to handle renaming of columns.

        if oldCols:
            if ("lcols" not in _localDepWarned) and self._showDepWarnings:
                _localDepWarned["lcols"] = True
                warnings.warn(
                    "DEPRECATION WARNING: The light curve column labels have been renamed, for consistency "
                    "with different products. The server now returns `TimePos`, `TimeNeg` (instead of `T_+ve`, `T_-ve`)"
                    " and `RatePos`, `RateNeg` (instead of `Ratepos`, `Rateneg`)\n"
                    "For backwards compatibility, the columns are, for the time being, rewritten to the old style. "
                    "This will be disabled in the future. You can disable it now my setting the `deprecate` variable "
                    "of this class to `False`."
                )
            self._oldLCCols = True
            # Now we have to fix the columns, which is a pain.
            for key in returnedData["Datasets"]:
                tmpKey = f"{key}Data"
                if tmpKey not in returnedData:
                    raise RuntimeError(f"Expected to find `{key}` data, but it is not present.")
                if "columns" not in returnedData[tmpKey]:
                    raise RuntimeError(f"`{key}` contains no column information.")
                c = returnedData[tmpKey]["columns"]
                c = [
                    "T_+ve"
                    if x == "TimePos"
                    else "T_-ve"
                    if x == "TimeNeg"
                    else "Ratepos"
                    if x == "RatePos"
                    else "Rateneg"
                    if x == "RateNeg"
                    else "Rate"
                    if x == "UpperLimit"
                    else x
                    for x in c
                ]
                returnedData[tmpKey]["columns"] = c

        else:
            self._oldLCCols = False

        self._lcData = dl._handleLightCurve(returnedData, oldCols=oldCols, silent=self.silent, verbose=False)

        if oldKeys:
            if ("lcKeys" not in _localDepWarned) and self.showDepWarnings:
                _localDepWarned["lcKeys"] = True
                warnings.warn(
                    "DEPRECATION WARNING: The light curve dataset keys have been renamed, for greater flexibility and "
                    "compatibility with other products in the API. Names now can include (for example) 'PC_incbad' "
                    "instead of simply 'PC'.\n"
                    "For backwards compatibility, the keys are, for the time being, rewritten to the old style. "
                    "This will be disabled in the future. You can disable it now my setting the `deprecate` variable "
                    "of this class to `False`."
                )
                if (nosys == "both") or (incbad == "both"):
                    warnings.warn(
                        "Cannot revert to the old-style dataset keys if incbad or nosys is 'both'"
                        "(incbad={incbad}, nosys={nosys})."
                    )
                else:
                    tmpDS = []
                    for oldKey in self._lcData["Datasets"]:
                        newKey = oldKey.split("_")[0]
                        if newKey in tmpDS:
                            raise RuntimeError("An error occurred trying to make your products 'old-style.")
                        tmpDS.append(newKey)
                        self._lcData[newKey] = self._lcData.pop(oldKey)

        if returnData:
            return self.lcData

    def retrieveSpectralFits(self, returnData=None):
        """Get the spectral fit results.

        This function queries the server for the spectrum and if there
        is one and it is complete, then it will obtain the standard
        spectrum ``dict`` with the details of the spectra and fits.

        This is saved to the ``specData`` class variable and
        (optionally) returned.

        Parameters
        ----------

        returnData : bool, optional
            Whether this function should return the downloaded data
            (default: ``False``).

        Returns
        -------

        dict
            A dictionary with the spectral fit information as described
            above.

        Raises
        ------

        RuntimeError
            If the job has not been submitted, or didn't contain a
            spectrum.

        """
        if not self.submitted:
            raise RuntimeError("Can't query this request as it hasn't been submitted!")
        if not self.hasProd("spec"):
            raise RuntimeError("Can't retrieve the spectrum as none was requested.")

        oldPars = self.deprecate

        if returnData is None:
            returnData = self.deprecate
            if self.deprecate and self.showDepWarnings and ("specReturn" not in _localDepWarned):
                warnings.warn(
                    "DEPRECATION WARNING: In the future this function will not return the spectrum unless "
                    "called with returnData=True. The source list will still be stored in the self.specData variable."
                )
                _localDepWarned["specReturn"] = True

        jsonDict = {
            "UserID": self.UserID,
            "JobID": self.JobID,
        }

        returnedData = self._submitAPICall(jsonDict, "getSpectrum")

        if oldPars:
            if ("speccols" not in _localDepWarned) and self.showDepWarnings:
                _localDepWarned["speccols"] = True
                warnings.warn(
                    "DEPRECATION WARNING: The spectrum parameters have been renamed, for consistency "
                    "with different products. All fields now have an upper-case first letter, NH is capitalised, and "
                    "the postive/negative error values are labelled a Pos/Neg (not pos/neg)\n"
                    "For backwards compatibility, the columns are, for the time being, rewritten to the old style. "
                    "This will be disabled in the future. You can disable it now my setting the `deprecate` variable "
                    "of this class to `False`."
                )

            # OK, fix the columns. This is going to suck.
            newRet = {}
            newRet["T0"] = returnedData["T0"]
            newRet["GalNH"] = returnedData["GalNH_unfitted"]
            newRet["rnames"] = returnedData["rnames"]

            modes = ("WT", "PC")
            for r in returnedData["rnames"]:
                newRet[r] = {}
                newRet[r]["start"] = str(returnedData[r]["Start"])
                newRet[r]["stop"] = str(returnedData[r]["Stop"])
                newRet[r]["DataFile"] = returnedData[r]["DataFile"]
                newRet[r]["Modes"] = returnedData[r]["Modes"]
                for m in modes:
                    if m in returnedData[r]["Modes"]:
                        newRet[r][f"Have{m}"] = 1
                        newVals = {}
                        if "PowerLaw" in returnedData[r][m]:
                            if "NOFIT" in returnedData[r][m]["PowerLaw"]:
                                newRet[r][f"Have{m}"] = 0
                                newRet[r]["Modes"].remove(m)

                            else:
                                for new in returnedData[r][m]["PowerLaw"].keys():
                                    if new == "Image":
                                        oldKey = new
                                    else:
                                        oldKey = new.replace("NH", "nh")
                                        oldKey = oldKey[0].lower() + oldKey[1:]  # first letter to lower case
                                        oldKey = oldKey.replace("Pos", "pos")
                                        oldKey = oldKey.replace("Neg", "neg")
                                    newVals[oldKey] = returnedData[r][m]["PowerLaw"][new]
                                newVals["meantime"] = returnedData[r][m]["MeanTime"]
                                newVals["exposure"] = returnedData[r][m]["Exposure"]
                                newRet[r][m] = newVals

            returnedData = newRet
            self._oldSpecCols = True
        else:
            self._oldSpecCols = False

        if "ERROR" in returnedData:
            return {"ERROR": True, "Reason": returnedData["ERROR"]}

        self._specData = returnedData

        if returnData:
            return self._specData

    # -------- END OF  FOR GETTING THE PRODUCTS --------

    # -------- REBIN FUNCTIONS ------------------
    # These are really just wrappers around download.py functions.

    def rebinLightCurve(self, **kwargs):
        """Rebin the light curve

        This can be used to rebin the light curve your request built.
        If the only thing you want to change are the binning options,
        this is much faster than building an entirely new light curve.
        The parameter you can pass are all arguments for
        ``ukssdc.download._rebinLightCurve()``.

        Parameters
        ----------

        kwargs : dict
            Parameters defining the binning; please see the online
            documentation for a full description of these.

        """
        if not self.hasLightCurve:
            raise RuntimeError("This request doesn't have a light curve, cannot rebin!")
        if not self.submitted:
            raise RuntimeError("Cannot rebin before building the light curve!")

        if (not self.complete) and (not self._productList["lc"].complete):
            raise RuntimeError("Light curve is not yet compelete, cannot rebin.")

        if ("name" not in kwargs) and ("name" in self.globalPars):
            kwargs["name"] = self.globalPars["name"]
        if "silent" not in kwargs:
            kwargs["silent"] = self.silent
        if "verbose" not in kwargs:
            kwargs["verbose"] = not self.silent

        self._rebinID = dl._rebinLightCurve("UOB_LC", self.JobID, **kwargs)
        if not self.silent:
            print(f"Rebinning with rebinID {self._rebinID}")

    def checkRebinStatus(self):
        """Check the status of a rebin job.

        Just wraps ``ukssdc.data.download._checkRebinStatus()``.

        """
        return dl._checkRebinStatus(self._rebinID, silent=self.silent, verbose=not self.silent)

    def rebinComplete(self):
        """Check whether the rebin job is complete.

        Just wraps ``ukssdc.data.download._rebinComplete()``.

        """
        return dl._rebinComplete(self._rebinID)

    def cancelRebin(self):
        """Cancels the rebin job.

        Just wraps ``ukssdc.data.download._cancelRebin()``."""

        return dl.__cancelRebin(self._rebinID, silent=self.silent, verbose=not self.silent)

    def getRebinnedLightCurve(self, **kwargs):
        """Get the light curves produced by a rebin command.

        This is just a wrapper to a generic function:
        ``ukssdc.data.download._getLightCurve()``.

        """
        if not self.rebinComplete():
            raise RuntimeError("Cannot get light curves; this job is not complete.")

        ret = dl._getLightCurve("REBIN_LC", self._rebinID, **kwargs)

        if ("returnData" in kwargs) and kwargs["returnData"]:
            return ret

    # -------- MISC FUNCTIONS --------
    # Check whether a product already exists

    def hasProd(self, what):
        """Return whether the request contains given product.

        Parameters
        ----------

        what : str
            The product to check.

        Returns
        -------

        bool
            Whether or not the product in question has been added to the
            request.

        Raises
        ------

        ValueError
            The 'what' is not a valid product type.

        """
        if what in longToShort:
            what = longToShort[what]
        if not ProductRequest.validType(what):
            raise ValueError(f"The product type {what} does not exist.")
        return what in self._productList

    # Update globals
    def _updateGlobals(self, parList, fromServer=False):
        """Update the global variables from a dictionary.

        This internal function is used for copying a product, or
        updating the values to those calculated by the server on submit.

        Parameters
        ----------

        parlist : dict
            A dictionary of parameter:value keywords.

        fromServer : bool
            Whether the dictionary is created from the JSON returned by
            the UKSSDC server. If not, then it is assumed to be in the
            format of a request to send TO the server. Default: False

        Raises
        ------

        ValueError
            If the value does not match the type needed by the
            parameter.

        """
        # Go through all of the parameters in the list
        for par in parList:
            val = parList[par]
            # Is it a par I renamed for Python? If so, we get the name of it as a Python global
            if par in self._JSONParsToGlobalPars:
                par = self._JSONParsToGlobalPars[par]

            # Is it a actually a global? parList may contain product-specific pars
            if par in XRTProductRequest._globalTypes:
                # If the parameter was a bool then it has come back as an int
                if (bool in XRTProductRequest._globalTypes[par]) and (type(val) != bool):
                    val = val == 1 or val == "yes" or val == "1"

                # Otherwise, check the type and try to cast it:
                if not isinstance(val, XRTProductRequest._globalTypes[par]):
                    # Get the preferred type
                    myType = XRTProductRequest._globalTypes[par][0]
                    # Cast; will raise an error if it can't
                    try:
                        val = myType(val)
                    except Exception:
                        val = None
                        print(f"Cannot convert parameter {par}={val} to a {myType}, set it to None")

                # If it's a parameter with a specific list of possible values, check the value is OK
                if (par in XRTProductRequest._globalSpecificParValues) and (
                    val not in XRTProductRequest._globalSpecificParValues[par]
                ):
                    raise ValueError(
                        f"'{val}' is not a valid value for {par}. "
                        f"Options are: {','.join(XRTProductRequest._globalSpecificParValues[par])}."
                    )
                # Lastly, if it's one of the 'get' things we want to set
                # it to False if we're from the server, because we want
                # to ensure that the submission will be reproducible,
                # but the targets list etc can change as we re-observe:
                if fromServer and (par in XRTProductRequest._makeWorkPars):
                    val = False

                self._globalPars[par] = val

    # Set all parameters from a JSON string or dict
    def setFromJSON(self, JSONVals, fromServer=False):
        """Update parameters to match those in a supplied dict.

        This sets your request to match the request detailed in the JSON
        object or dictionary supplied.  **This will completely destroy
        all of the current settings in the request**

        Parameters
        ----------

        JSONVals : str or dict (optional)
            If this is set then the request will be created with the
            parameters are defined in the JSON dict or string. This
            should be of the correct format, i.e. either that you can
            get from myRequest.jobPars or myRequest.getJSON() - where
            myRequest as an object of this class.

        fromServer : bool (optional)
            Only allowed if JSON is set. This specifies whether the JSON
            is that which was returned by the UKSSDC server upon
            successful submission of a request (True), or that created
            by this class, ready to submit (False). i.e. if the object
            was obtained via myRequest.jobPars this should be true; if
            from myRequest.getJSON() then it should be false.

        Raises
        ------

        ValueError
            If 'JSONVals' is not a string or dictionary.

        """
        if type(JSONVals) == str:  # It's literally a json string
            JSONVals = json.loads(JSONVals)

        if type(JSONVals) != dict:  # Oh oh
            raise ValueError("JSON should be a JSON string or a dict; it is not.")

        # Reset almost everything
        self._productList = dict()
        # Whether this request has been submitted yet
        self._submitted = False
        # The global vars: will be stored in a dictionary,
        # but accessible by individual par name or the property decorator
        self._globalPars = dict()
        # Will hold the jobID, again, decorator access which also prevents setting by the user.
        self._jobID = None
        self._rebinID = None
        # Status, related to the _statuses static variable
        self._status = 0
        # The data returned by a successful request submission, again will be read only
        self._retData = dict()
        self._complete = False

        # Now work out what products to add:

        # Need to invert classReqPar:
        parProd = dict()
        for prod, par in classReqPar.items():
            parProd[par] = prod

        for par, prod in parProd.items():
            if par in JSONVals:
                val = JSONVals[par]  # Just for ease
                if ((type(val) == bool) and val) or (type(val) == int and (val == 1)):
                    # We do want this product
                    self.addProduct(prod)

        # Now call an internal function to do the work
        self._setFromJSON(JSONVals, fromServer)

    # Internal function, this does the product updating, without first clearing everything
    def _setFromJSON(self, jsonDict, fromServer=False):
        """Update the product paremters from a dict.

        Internal function, does the donkey work for setFromJSON()

        """
        self._updateGlobals(jsonDict, fromServer)
        for prod in self._productList:
            globChange = self._productList[prod].updatePars(jsonDict, fromServer)
            if len(globChange) > 0:
                self._updateGlobals(globChange, fromServer)

    def copyOldJob(self, oldJobID, becomeThis=False):
        """Set your request to match an old job.

        This will completely destroy your request, and replace it with
        the a duplicate of the job matching the ID supplied - provided
        you were the user requesting that job.

        Parameters
        ----------

        oldJob : int
            The ID of the job you want to duplocate.

        becomeThis : bool (optional)
            Whether this XRTProductRequest should 'become' the old
            request. This will mean that you cannot submit the job, but
            you can retrieve the products (if available).

        Raises
        ------

        RuntimeError
            If the job cannot be copied.

        """
        jsonDict = {
            "UserID": self.UserID,
            "oldJob": oldJobID,
        }

        returnedData = self._submitAPICall(jsonDict, "getOldProduct", minKeys=("jobPars", "URL"))

        if "ERROR" in returnedData:
            raise RuntimeError(returnedData["ERROR"])

        self.setFromJSON(returnedData["jobPars"], True)

        if becomeThis:
            self._jobID = oldJobID
            self._retData["URL"] = returnedData["URL"]
            self._submitted = True
            self._status = 1
            self.checkProductStatus()

    def plotLC(self, xlog=False, ylog=False, fileName=None, incbad=False, nosys=False, **kwargs):
        """Create a quick-look plot of the light curve, if retrieved.

        This will create a very simple plot of the light curve, if one
        has been created and retrieved. It requires matplotlib.pyplot
        to be installed and wraps the function
        ``swifttools.ukssdc.plotLightCurve()``.

        Parameters
        ----------

        nosys : bool, optional
            Whether to plot the light curves from which the WT
            systematic error has been removed (default: ``False``).

        incbad : str
            Whether to plot the light curves in which the datapoints
            flagged as potentially unreliable to due centroiding issues
            have been included (default: ``False``).

        **kwargs : dict, optional
            Any extra arguments to pass to
            ``swifttools.ukssdc.plotLightCurve()``.

        Returns
        -------

        fix,ax
            The objects containing the figure, created by
            ``matplolib.pyplot.subplots()``.

        Raises
        ------

        RuntimeError
            If no light curve exists
        ModuleNotFoundError
            If matplotlib.pyplot is not installed.

        """
        if self._lcData is None:
            raise RuntimeError("No light curve has been retrieved")

        whichCurves = []
        suff = ""
        if nosys:
            suff = suff + "_nosys"
        if incbad:
            suff = suff + "_incbad"

        for m in ("WT", "PC"):
            for c in ("", "UL"):
                k = f"{m}{c}{suff}"
                if k in self._lcData:
                    whichCurves.append(k)

        # See if we can make some nice axis labels
        tmp = self.getLightCurvePars()
        tmpG = self.getGlobalPars()
        xlabel = "Time"
        if tmp["timeFormat"] == "m":
            xlabel = "MJD"
        elif ("T0" in tmpG) and (tmpG["T0"] is not None):
            xlabel = f"Time since MET={tmpG['T0']} (s)"
        else:
            xlabel = "Time (s)"

        ylabel = "Count rate"
        if ("minEnergy" in tmp) and ("maxEnergy" in tmp):
            ylabel = f"Count rate ({tmp['minEnergy']} - {tmp['maxEnergy']})"

        return mplot(
            self._lcData,
            whichCurves=whichCurves,
            xlog=xlog,
            ylog=ylog,
            xlabel=xlabel,
            ylabel=ylabel,
            oldAPI=self._oldLCCols,
            silent=self.silent,
        )

    def saveSpectralData(
        self,
        **kwargs
        # destDir="spec",
        # saveImages=True,
        # saveData=True,
        # extract=False,
        # removeTar=False,
        # clobber=False,
        # skipErrors=False,
        # verbose=False,
    ):
        """Save the spectral data to disk.

        This will download and save the spectral files from a previous
        ``retrieveSpectralFits()`` call.

        Parameters
        ----------

        destDir : str, optional
            The directory in which to save (default: "spec").

        saveImages : bool, optional
            Whether to save the gif images (default ``True``).

        saveData : bool, optional
            Whether to save the actual spectral data (default ``True``).

        extract : bool, optional
            Whether to extract the spectral files from the
            tar archive (default ``False``).

        removeTar : bool, optional
            Whether to remove the tar file after extracting. **This
            parameter is ignored unless ``extract`` is ``True``**
            (default: ``False``).

        clobber : bool, optional
            Whether to overwrite files if they exist (default ``False``).

        skipErrors : bool, optional
            If an error occurs saving a file, do not raise a RuntimeError
            but simply continue to the next file (default ``False``).

        verbose : bool, optional
            Product full verbose output (default ``False``).

        """
        if self.specData is None:
            raise RuntimeError("Cannot save spectra until you download them!")

        if self._oldSpecCols:
            raise RuntimeError("Cannot save spectra where the old structure was used.")

        dl._saveSpectrum(self.specData, silent=self.silent, **kwargs)
