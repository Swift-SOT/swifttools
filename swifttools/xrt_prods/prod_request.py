import requests
import json
from .prod_common import *
from .prod_base import ProductRequest
from .productVars import skipGlobals, globalParTriggers
import os
import re
import warnings
import pandas as pd
import numpy as np
from distutils.version import StrictVersion


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
        raise RuntimeError(
            f"An HTTP error occured - HTTP return code {submitted.status_code}: {submitted.reason}"
        )

    # OK, submitted alright, now, was it successful?
    # Do I want to try/catch just in case?

    returnedData = json.loads(submitted.text)

    # Request was submitted fine, return is OK, but the return reports an error
    checkAPI(returnedData)

    if returnedData["OK"] == 0:
        if "ERROR" not in returnedData:  # Invalid JSON
            return self._submitFail(
                f"The server return does not confirm to the expected JSON structure; do you need do update this module?"
            )

        errString = returnedData["ERROR"] + "\n"
        print(f"ERROR: {errString}")
        return None

    if "jobs" not in returnedData:  # Invalid JSON
        raise RuntimeError(
            f"The server return does not confirm to the expected JSON structure; do you need do update this module?"
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
        raise RuntimeError(
            f"An HTTP error occured - HTTP return code {submitted.status_code}: {submitted.reason}"
        )

    # OK, submitted alright, now, was it successful?
    # Do I want to try/catch just in case?
    returnedData = json.loads(submitted.text)

    # Request was submitted fine, return is OK, but the return reports an error
    checkAPI(returnedData)

    if returnedData["OK"] == 0:
        if "ERROR" not in returnedData:  # Invalid JSON
            return self._submitFail(
                f"The server return does not confirm to the expected JSON structure; do you need do update this module?"
            )

        errString = returnedData["ERROR"] + "\n"
        print(f"ERROR: {errString}")
        return -1

    if "numJobs" not in returnedData:  # Invalid JSON
        raise RuntimeError(
            f"The server return does not confirm to the expected JSON structure; do you need do update this module?"
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
            f"The server return does not confirm to the expected JSON structure; do you need do update this module?"
        )

    # if float(returnedData["APIVersion"]) > float(XRTProductRequest._apiVer):
    if StrictVersion(str(returnedData["APIVersion"])) > StrictVersion(XRTProductRequest._apiVer):
        warnings.warn(
            f"WARNING: you are using version {XRTProductRequest._apiVer} of the API; "
            f"the latest version is {returnedData['APIVersion']}, it would be advisable to update your version."
        )

    if "OK" not in returnedData:  # Invalid JSON
        raise RuntimeError(
            f"The server return does not confirm to the expected JSON structure; do you need do update this module?"
        )


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
    _globalDeps = {"centroid": {"True": ("posErr",)}, "posobs": {"hours": ("posobstime",), "user": ("useposobs")}}

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
    _apiVer = "1.8"

    # Now begin the instantiated stuff.  First what to output when this
    # instance is entered in an ipython shell.
    def __str__(self):
        str = f"XRTProductRequest object for user `{self.UserID}`, with the following products requested:\n"
        for key in self._productList:
            str = str + f"* {longProdName[key]}\n"
        return str

    def __repr__(self):
        str = f"XRTProductRequest object"
        return str

    # Could create a __str__ as well if I want the print(this) to be
    # different from just typing (this) on the cmnd line

    # Constructor - requires the userID
    def __init__(self, user, JSONVals=None, fromServer=False, silent=True):
        """
        Constructs an XRTProductRequest object.

        Parameters
        ----------
        user : str
            Your User ID, as registered via
            https://www.swift.ac.uk/user_objects/register.php

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
        self._specData = None
        self._silent = silent

        # Also create a look up from the par names returned in the JSON
        # to the Python globals shown to the user.  Do this on the flu
        # so I only have one list to maintain, and therefore can't get
        # them out of sync.
        self._JSONParsToGlobalPars = dict()
        for gpar in XRTProductRequest._globalPythonParsToJSONPars:
            jpar = XRTProductRequest._globalPythonParsToJSONPars[gpar]
            self._JSONParsToGlobalPars[jpar] = gpar

        if JSONVals != None:
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
        """Dict containing the light curve, if retreieved."""
        return self._lcData
    
    # specData
    @property
    def specData(self):
        """Dict containing the spectra, if retreieved."""
        return self._specData
    
    
    #####
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
        what : list (optional)
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
        gpar : string
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

    ########### FUNCTIONS RELATED TO ADDING PRODUCTS TO THE REQUEST ################

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
            what : string
                The product to add (lc, spec, psf etc)
            prodArgs : *kwargs* (optional)
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
            what : string
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
        what : string
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
            what : string
                The product to set the parameters for (lc, spec, psf etc)
            **prodArgs
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
        what : string
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
            what : string
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
            what : string
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
            raise ValueError(f"The supplied object to copy from is not a ProductRequest!")
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

    ###################################################################
    ###### START PRODUCT SPECIFICATIONS ##############################
    ###################################################################

    ##### LIGHT CURVE #####

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

    ##### SPECTRUM #####

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

    #####  STANDARD POSITION #####

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

    ##### EHHANCED POSITION #####

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

    ##### ASTROMETRIC POSITION #####

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

    ##### IMAGE #####

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

    ##### SOURCE DETECTION #####

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

    ###################################################################
    ###### END OF PRODUCT SPECIFICATIONS ##############################
    ###################################################################

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

    ########### END OF PRODUCT ADDING SECTION ################

    ########### FUNCTIONS FOR SUBMITTING THE JOB ################

    # First, we need to build the JSON. This will work by going through
    # the global variables first, converting any argument names as
    # necessary, and copying them into a dictionary, then it will merge
    # that with the dictionary that we get from each product.

    def getJSONDict(self):
        """Get the data to upload.

        This returns the dictionary of values to upload to the server,
        built from the current request configuration.

        This does *not* submit the request.

        Parameters
        ----------
        None

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

        Parameters
        ----------
        None

        Returns
        -------
        str
            The JSON object (in string format)

        """
        return json.dumps(self.getJSONDict())

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

        submitted = requests.post("https://www.swift.ac.uk/user_objects/run_userobject.php", json=self.getJSONDict())
        if submitted.status_code != 200:  # Check that this is int!
            return self._submitFail(
                f"An HTTP error occured - HTTP return code {submitted.status_code}: {submitted.reason}"
            )

        # OK, submitted alright, now, was it successful?
        # Do I want to try/catch just in case?
        returnedData = json.loads(submitted.text)

        checkAPI(returnedData)

        # Request was submitted fine, return is OK, but the return reports an error
        if returnedData["OK"] == 0:
            if "ERROR" not in returnedData:  # Invalid JSON
                return self._submitFail(
                    f"The server return does not confirm to the expected JSON structure; do you need do update this module?"
                )

            errString = self._fixErrString(returnedData["ERROR"]) + "\n"
            if "listErr" in returnedData:
                for err in returnedData["listErr"]:
                    errString = errString + self._fixErrString(err["label"]) + "\n"
                    for terr in err["list"]:
                        errString = errString + self._fixErrString(f"* {terr}\n")

            return self._submitFail(errString)

        # If we made it this far, we submitted OK :)
        if "URL" not in returnedData:
            return self._submitFail(
                f"The server return does not confirm to the expected JSON structure; do you need do update this module?"
            )
        if "JobID" not in returnedData:
            return self._submitFail(
                f"The server return does not confirm to the expected JSON structure; do you need do update this module?"
            )
        if "jobPars" not in returnedData:
            return self._submitFail(
                f"The server return does not confirm to the expected JSON structure; do you need do update this module?"
            )

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
            except Exception as e:
                warnings.warn(f"The job was submitted OK, but an error occured updating the parameters.")
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
            m = re.search("([^\w]+)$", word)
            if m:
                extra = m.group(1)
                word = re.sub("[^\w]+$", "", word)
            if word in self._JSONParsToGlobalPars:
                word = self._JSONParsToGlobalPars[word]
            else:
                for what in self._productList.keys():
                    if word in self._productList[what]._JSONParsToPythonPars:
                        word = f"{shortToLong[what]}: {self._productList[what]._JSONParsToPythonPars[word]}"
            retString = retString + word + extra + " "

        return retString

    ########### END OF FUNCTIONS FOR SUBMITTING THE JOB ################

    ########### FUNCTIONS FOR MANIPULATING THE SUBMITTED JOB ################

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
        what : string / list
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
        what : string / list
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
            "api_name": XRTProductRequest._apiName,
            "api_version": XRTProductRequest._apiVer,
            "UserID": self.UserID,
            "JobID": self.JobID,
            "what": ",".join(reqWhat),
        }

        submitted = requests.post("https://www.swift.ac.uk/user_objects/canceljob.php", json=jsonDict)
        if submitted.status_code != 200:  # Check that this is int!
            return (
                -1,
                {"ERROR": f"An HTTP error occured - HTTP return code {submitted.status_code}: {submitted.reason}"},
            )

        returnedData = json.loads(submitted.text)

        checkAPI(returnedData)

        if returnedData["OK"] == 0:
            if "ERROR" not in returnedData:
                return (
                    -1,
                    {
                        "ERROR": "The server return does not confirm to the expected JSON structure; do you need do update this module?"
                    },
                )
            return (-1, {"ERROR": returnedData["ERROR"]})

        if ("status" not in returnedData) or ("statusCodes" not in returnedData):
            return (
                -1,
                {"ERROR": "The server return does not confirm to the expected JSON structure; do you need do update this module?"},
            )

        # OK got here;
        retDict = dict()
        for prod in reqWhat:
            if (prod not in returnedData["statusCodes"]) or (prod not in returnedData["status"]):
                return (
                    -1,
                    {
                        "ERROR": "The server return does not confirm to the expected JSON structure; do you need do update this module?"
                    },
                )
            retDict[shortToLong[prod]] = {
                "code": returnedData["statusCodes"][prod],
                "text": returnedData["status"][prod],
            }

        return (returnedData["OK"], retDict)
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
        what : string / list
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
            raise RuntimeError("Can't query this request as it doesn't correspond to a running job")

        reqWhat = self._getWhatList(what)

        if len(reqWhat) == 0:
            raise ValueError("You have not identified any products to query")

        qprodList = ",".join(reqWhat)
        # Make the request as a dictionary and then convert that to JSON as it removes any typos in the JSON by me, here
        jsonDict = {
            "api_name": XRTProductRequest._apiName,
            "api_version": XRTProductRequest._apiVer,
            "UserID": self.UserID,
            "JobID": self.JobID,
            "what": qprodList,
            "whatProg": qprodList,
        }

        submitted = requests.post("https://www.swift.ac.uk/user_objects/checkProductStatus.php", json=jsonDict)
        if submitted.status_code != 200:  # Check that this is int!
            #print(f"\n\n404: {submitted.text}\n\n")
            return {"ERROR": f"An HTTP error occured - HTTP return code {submitted.status_code}: {submitted.reason}"}

        returnedData = json.loads(submitted.text)

        checkAPI(returnedData)

        if returnedData["OK"] == 0:
            if "ERROR" not in returnedData:
                return {
                    "ERROR": "The server return does not confirm to the expected JSON structure; do you need do update this module?"
                }
            return {"ERROR": returnedData["ERROR"]}

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

    ########### END OF  FOR MANUPULATING THE JOB ################

    ########### FUNCTIONS FOR GETTING THE PRODUCTS ################

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

        what : string / list
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
        if stem != None and type(stem) != str:
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

    def retrieveStandardPos(self):
        """Get the standard position.

        This function queries the server for the standard position and
        returns it in a dictionary, if available. The return dict has
        the following keys:

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
        None

        Return
        ------
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
        if not self.hasProd('psf'):
            raise RuntimeError("Can't retrieve the standard position as none was requested.")

        status = self.checkProductStatus(('psf',))

        jsonDict = {
            "api_name": XRTProductRequest._apiName,
            "api_version": XRTProductRequest._apiVer,
            "UserID": self.UserID,
            "JobID": self.JobID,
        }

        submitted = requests.post("https://www.swift.ac.uk/user_objects/tprods/getPSFPos.php", json=jsonDict)
        if submitted.status_code != 200:
            return {"GotPos": False, "Reason": f"An HTTP error occured - HTTP return code {submitted.status_code}: {submitted.reason}"}

        returnedData = json.loads(submitted.text)

        checkAPI(returnedData)

        if returnedData["OK"] == 0:
            if "ERROR" not in returnedData:
                return {
                    "ERROR": "The server return does not confirm to the expected JSON structure; do you need do update this module?"
                }
            return {"GotPos": False, "Reason": returnedData["ERROR"]}

        # Remove the keys we don't need
        returnedData.pop('APIVersion', None)
        returnedData.pop('OK', None)
        returnedData["GotPos"] = bool(returnedData["GotPos"])
        if returnedData["GotPos"]:  # Position found
            returnedData["FromSXPS"] = bool(returnedData["FromSXPS"])
        else:
            returnedData["Reason"] = "No position could be determined."

        return returnedData

    def retrieveEnhancedPos(self):
        """Get the enhanced position.

        This function queries the server for the enhanced position and
        returns it in a dictionary, if available. The return dict has
        the following keys:

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
        None

        Return
        ------
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
        if not self.hasProd('enh'):
            raise RuntimeError("Can't retrieve the enhanced position as none was requested.")

        jsonDict = {
            "api_name": XRTProductRequest._apiName,
            "api_version": XRTProductRequest._apiVer,
            "UserID": self.UserID,
            "JobID": self.JobID,
        }

        submitted = requests.post("https://www.swift.ac.uk/user_objects/tprods/getEnhPos.php", json=jsonDict)
        if submitted.status_code != 200:
            return {"GotPos": False, "Reason": f"An HTTP error occured - HTTP return code {submitted.status_code}: {submitted.reason}"}

        returnedData = json.loads(submitted.text)

        checkAPI(returnedData)

        if returnedData["OK"] == 0:
            if "ERROR" not in returnedData:
                return {
                    "ERROR": "The server return does not confirm to the expected JSON structure; do you need do update this module?"
                }
            return {"GotPos": False, "Reason": returnedData["ERROR"]}

        # Remove the keys we don't need
        returnedData.pop('APIVersion', None)
        returnedData.pop('OK', None)
        returnedData["GotPos"] = bool(returnedData["GotPos"])
        if not returnedData["GotPos"]:  # No position found
            returnedData["Reason"] = "No position could be determined."

        return returnedData

    def retrieveAstromPos(self):
        """Get the astrometric position.

        This function queries the server for the astrometric position and
        returns it in a dictionary, if available. The return dict has
        the following keys:

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
        None

        Return
        ------
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
        if not self.hasProd('xastrom'):
            raise RuntimeError("Can't retrieve the enhanced position as none was requested.")

        jsonDict = {
            "api_name": XRTProductRequest._apiName,
            "api_version": XRTProductRequest._apiVer,
            "UserID": self.UserID,
            "JobID": self.JobID,
        }

        submitted = requests.post("https://www.swift.ac.uk/user_objects/tprods/getXastromPos.php", json=jsonDict)
        if submitted.status_code != 200:
            return {"GotPos": False, "Reason": f"An HTTP error occured - HTTP return code {submitted.status_code}: {submitted.reason}"}

        returnedData = json.loads(submitted.text)

        checkAPI(returnedData)

        if returnedData["OK"] == 0:
            if "ERROR" not in returnedData:
                return {
                    "ERROR": "The server return does not confirm to the expected JSON structure; do you need do update this module?"
                }
            return {"GotPos": False, "Reason": returnedData["ERROR"]}

        # Remove the keys we don't need
        returnedData.pop('APIVersion', None)
        returnedData.pop('OK', None)
        returnedData["GotPos"] = bool(returnedData["GotPos"])
        if returnedData["GotPos"]:  # Position found
            returnedData["FromSXPS"] = bool(returnedData["FromSXPS"])
        else:
            returnedData["Reason"] = "No position could be determined."

        return returnedData

    def retrieveSourceList(self):
        """Get the sources found by source detection

        This functions queries the source detection run for this job,
        and returns a dict. The dict will have entries:

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

        Parameters
        ----------
        None

        Return
        ------
        dict
            A dictionary with the source information.

        Raises
        ------
        RuntimeError
            If the job has not been submitted, or didn't contain a 
            standard position.

        """
        if not self.submitted:
            raise RuntimeError("Can't query this request as it hasn't been submitted!")
        if not self.hasProd('sourceDet'):
            raise RuntimeError("Can't retrieve the standard position as none was requested.")

        status = self.checkProductStatus(('sourceDet',))

        jsonDict = {
            "api_name": XRTProductRequest._apiName,
            "api_version": XRTProductRequest._apiVer,
            "UserID": self.UserID,
            "JobID": self.JobID,
        }

        submitted = requests.post("https://www.swift.ac.uk/user_objects/tprods/getSourceDetResults.php", json=jsonDict)
        if submitted.status_code != 200:
            return {"ERROR": True, "Reason": f"An HTTP error occured - HTTP return code {submitted.status_code}: {submitted.reason}"}

        returnedData = json.loads(submitted.text)

        checkAPI(returnedData)

        if returnedData["OK"] == 0:
            if "ERROR" not in returnedData:
                return {
                    "ERROR": "The server return does not confirm to the expected JSON structure; do you need do update this module?"
                }
            return {"ERROR": True, "Reason": returnedData["ERROR"]}

        # Remove the keys we don't need
        returnedData.pop('APIVersion', None)
        returnedData.pop('OK', None)

        # Now convert everything I can into numbers:
        for band in returnedData:
            for src in range(len(returnedData[band])):
                for par in returnedData[band][src]:
                    v = returnedData[band][src][par]
                    if re.search("\d", v):
                        if re.search("\.", v):
                            returnedData[band][src][par] = float(returnedData[band][src][par])
                        else:
                            returnedData[band][src][par] = int(returnedData[band][src][par])

        return returnedData

    def retrieveLightCurve(self, nosys=False, incbad=False):
        """Get the light curve data

        This function queries the server for the light curve, and 
        returns a dictionary of Pandas DataFrames.
        If successful, then there will be any or all of the keys:
        WT, WTUL, PC, PCUL - corresponding to WT/PC detected light curve
        bins, or upper limits. A missing key means there were no data
        of that type, e.g. if there is no "PCUL" key then the light
        curve contains no PC mode upper limits. Where the key exists,
        the contents is a DataFrame.

        On failure, the dict will contain: ERROR and Reason.

        Parameters
        ----------
        nosys : bool
            Whether to remove the WT systematic error from the bins.
            Default: False

        incbad : bool
            Whether to include WT data points marked as bad.
            Default: False

        Return
        ------
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
        if not self.hasProd('lc'):
            raise RuntimeError("Can't retrieve the light curve as none was requested.")

        jsonDict = {
            "api_name": XRTProductRequest._apiName,
            "api_version": XRTProductRequest._apiVer,
            "UserID": self.UserID,
            "JobID": self.JobID,
        }

        submitted = requests.post("https://www.swift.ac.uk/user_objects/tprods/getLCData.php", json=jsonDict)
        if submitted.status_code != 200:
            return {"ERROR": True, "Reason": f"An HTTP error occured - HTTP return code {submitted.status_code}: {submitted.reason}"}

        returnedData = json.loads(submitted.text)

        checkAPI(returnedData)

        if returnedData["OK"] == 0:
            if "ERROR" not in returnedData:
                return {
                    "ERROR": True, "Reason": "The server return does not confirm to the expected JSON structure; do you need do update this module?"
                }
            return {"ERROR": True, "Reason": returnedData["ERROR"]}

        # Remove the keys we don't need
        returnedData.pop('APIVersion', None)
        returnedData.pop('OK', None)
        possKeys = ('WT', 'WTUL', 'PC', 'PCUL')
        ret = dict()

        for key in possKeys:
            tmpKey = f"has{key}"
            if (tmpKey in returnedData) and (returnedData[tmpKey]==1):
                tmpKey = f"{key}Data"
                if tmpKey not in returnedData:
                    return {"ERROR": True, "Reason": f"Can't find {tmpKey} in data, is your module up to date?"}
                if 'columns' not in returnedData[tmpKey]:
                    return {"ERROR": True, "Reason": f"Can't find {tmpKey}.columns in data, is your module up to date?"}
                if 'columns' not in returnedData[tmpKey]:
                    return {"ERROR": True, "Reason": f"Can't find {tmpKey}.data in data, is your module up to date?"}
                cols = returnedData[tmpKey]['columns']
                ret[key] = pd.DataFrame(returnedData[tmpKey]['data'], columns=cols, dtype=float)

        self._lcData = ret
        return self._lcData

    def retrieveSpectralFits(self):
        """Get the spectral fit results.

        This function queries the server for the spectrum and if there
        is one and it's complete, then it will return the automated
        power-law fit values for each spectrum requested. These will
        be stored in a dictionary, with one entry per spectrum (given 
        the interval names requested). Each such entry has keys:

        * T0: The reference T0 time for the spectra
        * GalNH: The Galactic NH (from Willingale et al., 2013) along the
            line of sight. This is NOT included in the fit
        
        Then there is an entry for each spectrum you created. The key is
        the spectrum name, and the entry is a dict with the following
        keys:

        * start: Time in sec after T0 of the first data in this spectrum
        * stop: Time in sec after T0 of the last data in this spectrum
        * HaveWT: Whether there is a valid WT-mode fit
        * WT: a dict of the WT mode fit (if HaveWT=True)
        * HavePC: Whether there is a valid PC-mode fit
        * PC: a dict of the WT mode fit (if HavePC=True)

        The WT/PC dicts contain:

        * meantime: Mean photon arrival time (in sec since T0) in this 
                    spectrum
        * nh: Best-fitting column density in cm^-2
        * nhpos: 90% CL positive error on NH
        * nhneg: 90% CL negative error on NH
        * gamma: Best-fitting photon index
        * gammapos: 90% CL positive error on gamma
        * gammaneg: 90% CL negative error on gamma
        * obsFlux: Best-fitting observed flux in erg cm^-2 s^-1
        * obsFluxpos: 90% CL positive error on the observed flux
        * obsFluxneg: 90% CL negative error on the observed flux
        * unabsFlux: Best-fitting unabsorbed flux in erg cm^-2 s^-1
        * unabsFluxpos: 90% CL positive error on the unabsorbed flux
        * unabsFluxneg: 90% CL negative error on the unabsorbed flux
        * cstat: The C-stat of the best fit (technically Wstat, see the
                 xspec manual for details)
        * dof: The degrees of freedom in the fit
        * fitChi: The Churazov-weighed chi^2 test statistic. This is not
                  used in the minimisation, just to asses fir quality.
        * exposure: The exposure time in the spectrum

        On failure, the dict will have a key ERROR, and a key Reason
        giving the description of the error.

        Parameters
        ----------
        None

        Return
        ------
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
        if not self.hasProd('spec'):
            raise RuntimeError("Can't retrieve the spectrum as none was requested.")

        jsonDict = {
            "api_name": XRTProductRequest._apiName,
            "api_version": XRTProductRequest._apiVer,
            "UserID": self.UserID,
            "JobID": self.JobID,
        }

        submitted = requests.post("https://www.swift.ac.uk/user_objects/tprods/getSpecData.php", json=jsonDict)
        if submitted.status_code != 200:
            return {"ERROR": True, "Reason": f"An HTTP error occured - HTTP return code {submitted.status_code}: {submitted.reason}"}

        returnedData = json.loads(submitted.text)

        checkAPI(returnedData)

        if returnedData["OK"] == 0:
            if "ERROR" not in returnedData:
                return {
                    "ERROR": "The server return does not confirm to the expected JSON structure; do you need do update this module?"
                }
            return {"ERROR": True, "Reason": returnedData["ERROR"]}

        # Remove the keys we don't need
        returnedData.pop('APIVersion', None)
        returnedData.pop('OK', None)

        self._specData = returnedData
        return self._specData
        
    ########### END OF  FOR GETTING THE PRODUCTS ################

    ########### MISC FUNCTIONS ################
    #####
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
                    val = (val == 1 or val == 'yes' or val == '1')

                # Otherwise, check the type and try to cast it:
                if not isinstance(val, XRTProductRequest._globalTypes[par]):
                    # Get the preferred type
                    myType = XRTProductRequest._globalTypes[par][0]
                    # Cast; will raise an error if it can't
                    try:
                        val = myType(val)
                    except Exception as e:
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
        # The global vars: will be stored in a dictionary, but accessible by individual par name or the property decorator
        self._globalPars = dict()
        # Will hold the jobID, again, decorator access which also prevents setting by the user.
        self._jobID = None
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
            "api_name": XRTProductRequest._apiName,
            "api_version": XRTProductRequest._apiVer,
            "UserID": self.UserID,
            "oldJob": oldJobID,
        }

        submitted = requests.post("https://www.swift.ac.uk/user_objects/getOldProduct.php", json=jsonDict)
        if submitted.status_code != 200:  # Check that this is int!
            # print(f"\n\n404: {submitted.text}\n\n")
            return {"ERROR": f"An HTTP error occured - HTTP return code {submitted.status_code}: {submitted.reason}"}

        returnedData = json.loads(submitted.text)

        checkAPI(returnedData)

        if returnedData["OK"] == 0:
            if "ERROR" not in returnedData:
                raise RuntimeError(
                    "The server return does not confirm to the expected JSON structure; do you need do update this module?"
                )
            raise RuntimeError(returnedData["ERROR"])

        if "jobPars" not in returnedData:
            raise RuntimeError("No data returned by the server!")

        if "URL" not in returnedData:
            raise RuntimeError("Invalid data returned by the server!")

        self.setFromJSON(returnedData["jobPars"], True)

        if becomeThis:
            self._jobID = oldJobID
            self._retData["URL"] = returnedData["URL"]
            self._submitted = True
            self._status = 1
            self.checkProductStatus()

    def plotLC(self, xlog=False, ylog=False, fileName=None):
        """Create a quick-look plot of the light curve, if retreived.

        This will create a very simple plot of the light curve, if one
        has been created and retrieved. It requires matplotlib.pyplot
        to be installed.

        Parameters
        ----------

        xlog : bool (optional)
            Whether to plot with the x axis logarithmic (default: False)
        ylog : bool (optional)
            Whether to plot with the y axis logarithmic (default: False)
        fileName : str (optional)
            If supplied, the light curve will be saved to the specified
            file

        Raises
        ------
        RuntimeError
            If no light curve exists
        ModuleNotFoundError
            If matplotlib.pyplot is not installed.
        
        """
        if self._lcData is None:
            raise RuntimeError("No light curve has been retrieved")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots()

        if 'WT' in self._lcData:
            ax.errorbar(self._lcData['WT']['Time'],
                        self._lcData['WT']['Rate'],
                        xerr=[-self._lcData['WT']['T_-ve'], self._lcData['WT']['T_+ve']],
                        yerr=[-self._lcData['WT']['Rateneg'],self._lcData['WT']['Ratepos']],
                        fmt=".",elinewidth=1.0,color="blue",label="WT",zorder=5)

        if 'WTUL' in self._lcData:
            empty = np.zeros(len(self._lcData['WTUL']['Time']))
            ulSize = np.zeros(len(self._lcData['WTUL']['Time']))+0.002
            ax.errorbar(self._lcData['WTUL']['Time'],
                        self._lcData['WTUL']['Rate'],
                        xerr=[-self._lcData['WTUL']['T_-ve'], self._lcData['WTUL']['T_+ve']],
                        yerr=[ulSize,empty],
                        uplims=True,elinewidth=1.0,color="blue",label="WT",zorder=5)

        if 'PC' in self._lcData:
            ax.errorbar(self._lcData['PC']['Time'],
                        self._lcData['PC']['Rate'],
                        xerr=[-self._lcData['PC']['T_-ve'], self._lcData['PC']['T_+ve']],
                        yerr=[-self._lcData['PC']['Rateneg'],self._lcData['PC']['Ratepos']],
                        fmt=".",elinewidth=1.0,color="red",label="PC",zorder=5)

        if 'PCUL' in self._lcData:
            empty = np.zeros(len(self._lcData['PCUL']['Time']))
            ulSize = np.zeros(len(self._lcData['PCUL']['Time']))+0.002
            ax.errorbar(self._lcData['PCUL']['Time'],
                        self._lcData['PCUL']['Rate'],
                        xerr=[-self._lcData['PCUL']['T_-ve'], self._lcData['PCUL']['T_+ve']],
                        yerr=[ulSize,empty],
                        uplims=True,elinewidth=1.0,color="red",label="PC",zorder=5)

        if xlog:
            ax.set_xscale("log")
        if ylog:
            ax.set_yscale("log")

        # See if we can make some nice axis labels
        tmp = self.getLightCurvePars()
        tmpG = self.getGlobalPars()
        xlabel = "Time"
        if tmp['timeType'] == "m":
            xlabel = "MJD"
        elif ('T0' in tmpG) and (tmpG['T0'] is not None):
            xlabel = f"Time since MET={tmpG['T0']} (s)"
        else:
            xlabel = "Time (s)"

        ylabel = "Count rate"
        if ('minEnergy' in tmp) and ('maxEnergy' in tmp):
            ylabel = f"Count rate ({tmp['minEnergy']} - {tmp['maxEnergy']})"

        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)

        if fileName is None:
            plt.show()
        else:
            plt.savefig(fileName)

