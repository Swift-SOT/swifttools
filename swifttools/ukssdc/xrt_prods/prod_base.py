from .productVars import *  # noqa
from .prod_common import *  # noqa
import requests
import os.path


class ProductRequest:
    """Product-specific request class.

    This class manages individual products that are requested, e.g.
    light curve, spectrum etc.  It works with their abbreviated names as
    defined in the main (i.e. not Python-specific) API, i.e.  lc, spec
    etc. This should be invisible to the user who should not be
    accessing this directly.

    MORE DOCS
    """

    @staticmethod
    def validType(what):
        """Return whether the specified product is permittable."""
        return what in prodParTypes

    # Prods will need _ParsToJSONPars
    # _allowedParValues - for things with restrictive values
    # # (e.g. binMeth)
    # _JSONValsToPythonVals - for things which have different internal
    # values to external ones, again e.g. binMeth (too = 1 &c)
    def __init__(self, what, silent=True):
        """
        Create the product that you have requested.

        Parameters
        ----------
        what : str The type of product this request is for (a ValueError
            will be raised if an invalid product is requested)

        silent : bool Whether to suppress all console output
               (default: True).

        """
        # Was this a valid product?
        if what not in prodParTypes:
            raise ValueError(f"{what} is not a valid product to request")

        self._silent = silent
        self._pars = dict()
        self._prodType = what
        self._complete = False
        self._needGlobals = prodNeedGlobals[what]
        self._parTypes = prodParTypes[what]
        self._pythonParsToJSONPars = prodPythonParsToJSONPars[what]
        self._deprecatedPars = deprecatedPars[what]
        self._specificParValues = prodSpecificParValues[what]
        self._parDeps = prodParDeps[what]
        self._needPars = prodNeedPars[what]
        self._downloadStem = prodDownloadStem[what]
        self._parTriggers = prodParTriggers[what]
        self._useGlobals = prodUseGlobals[what]

        self._JSONParsToPythonPars = dict()
        for gpar in self._pythonParsToJSONPars:
            jpar = self._pythonParsToJSONPars[gpar]
            self._JSONParsToPythonPars[jpar] = gpar

        # Set defaults:
        if len(prodDefaults[what]) > 0:
            self.setPars(**(prodDefaults[what]))

        if not self.silent:
            print(f"Successfully created a {longProdName[what]}")

    # -------- SOME ATTRIBUTES --------
    # as properties because I either want checks, or to make them read-only

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

    @property
    def complete(self):
        """Return whether this product been built."""
        return self._complete

    # Setter
    @complete.setter
    def complete(self, isComplete):
        if type(isComplete) != bool:
            raise ValueError(f"complete must be a bool, not {type(isComplete)}")
        self._complete = isComplete

    @property
    def needGlobals(self):
        """Return the globals required by this product."""
        return self._needGlobals

    @property
    def prodType(self):
        """Return what type of product this instance is."""
        return self._prodType

    @property
    def useGlobals(self):
        """Return what globals this product uses."""
        return self._useGlobals

    @property
    def pythonParsToJSONPars(self):
        """Return the conversion from internal to JSON names."""
        return self._pythonParsToJSONPars

    # -------- THE FUNCTIONS --------
    # setPars sets parameters for the product, first checking that all
    # parameters passed are valid parameters for this product

    def setPars(self, **prodPars):
        """Set product parameters.

        Set one more more of the parameters relating to the
        specific product Raises a ValueError if an invalid parameter is
        set, or a parameter is set to an invalid value

        Parameters
        ----------
        **prodPars : (kwargs) Sets of parameter = value keywords.
            Parameter must be a valid parameter needed by this product

        Return
        ------
        dict of any parameters which are actually globals

        """
        #  Go through everything we were sent.
        # Check that it's a valid parameter
        # Check that it has the right type
        # If it has only specific allowable values, check that it's one
        # of these
        # Set it

        retGlob = dict()

        for ppar in prodPars:
            val = prodPars[ppar]

            if ppar in self._deprecatedPars:
                print(f"WARNING: {ppar} is deprecated, replaced with {self._deprecatedPars[ppar]}")
                ppar = self._deprecatedPars[ppar]
            # Check if it's something which is being managed by globals.
            # NB for these, the globals will use the JSON pars, so I do
            # the python to JSON conversion before returning
            if ppar in self._useGlobals:
                # Yes, this needs sending back, but first, does it need
                # changing to a JSON var?
                tmpPar = ppar
                if tmpPar in self._pythonParsToJSONPars:
                    tmpPar = self._pythonParsToJSONPars[tmpPar]
                if not self.silent:
                    print(f"Adding {tmpPar} to change globals")
                retGlob[tmpPar] = val
                continue
            elif ppar in self._JSONParsToPythonPars:
                tmp = self._JSONParsToPythonPars[ppar]
                if tmp in self._useGlobals:
                    retGlob[ppar] = val
                    if not self.silent:
                        print(f"Adding {tmpPar} to change globals (2)")
                    continue

            if ppar not in self._parTypes:
                # They may have used an JSON parameter instead of a python one
                print(f"Looking up {ppar}")
                if ppar in self._JSONParsToPythonPars:
                    print(f"Got {self._JSONParsToPythonPars[ppar]}")
                    ppar = self._JSONParsToPythonPars[ppar]
                else:
                    raise ValueError(f"{ppar} is not a recognised {self.prodType} parameter")

            if not isinstance(val, self._parTypes[ppar]):
                raise TypeError(f"{ppar} should be a {self._parTypes[ppar]} but you supplied a {type(val)}.")

            if ppar in self._specificParValues:
                val = val.lower()
                if val.lower() not in self._specificParValues[ppar]:
                    raise ValueError(
                        f"'{val}' is not a valid value for {ppar}. Options are: {','.join(self._specificParValues[ppar])}."
                    )
            # OK if we got here then we can set it:
            if not self.silent:
                print(f"OK, setting {ppar} = {val}")
            self._pars[ppar] = val
            # Are there any dependencies to set?
            if ppar in self._parTriggers:
                if val in self._parTriggers[ppar]:
                    for depPar, depVal in self._parTriggers[ppar][val].items():
                        if (depVal is None or depVal == "None") and depPar in self._pars:
                            del self._pars[depPar]
                        elif depVal is not None and depVal != "None":
                            self._pars[depPar] = depVal
                        if not self.silent:
                            print(f"Also setting {self._prodType} {depPar} = {depVal}, because {ppar} = {val}")
                if "ANY" in self._parTriggers[ppar]:
                    for depPar, depVal in self._parTriggers[ppar]["ANY"].items():
                        if (depVal is None or depVal == "None") and depPar in self._pars:
                            del self._pars[depPar]
                        elif depVal is not None and depVal != "None":
                            self._pars[depPar] = depVal
                        if not self.silent:
                            print(f"Also setting {self._prodType} {depPar} = {depVal}, because {ppar} = {val} (ANY)")
                if "NONE" in self._parTriggers[ppar] and (val is None or val == "None"):
                    for depar, depVal in self._parTriggers[ppar]["NONE"].items():
                        self._pars[depar] = depVal
                        if not self.silent:
                            print(f"Also setting {depar} = {depVal}, because {ppar} = {val}")

        return retGlob

    # updatePars is like setPars, in that it sets the parameters for
    # this product from those which are passed to it, however it does
    # not throw an error for parameters not in this product, it just
    # skips them I think fromServer is no longer needed, but keave it in
    # in case of future development

    def updatePars(self, parList, fromServer=False):
        """Update parameters for this product.

        This is designed for use when updating parameters to those
        returned by the server on job sumission. It updates the
        parameter values for this product to those supplied, ignoring
        and parameters it does not recognise.

        Parameters
        ----------
        parlist : dict A dictionary of parameter:value keywords.

        fromServer : bool Whether the dictionary is created from the
            JSON returned by the UKSSDC server. If not, then it is
            assumed to be in the format of a request to send TO the
            server. Default: False

        Return
        ------
        dict of any parameters which are actually globals

        """
        retGlob = dict()

        # Go through all of the parameters in the list
        for par in parList:
            val = parList[par]
            # Check if it's something which is being managed by globals.
            # NB for these, the globals will use the JSON pars, so I do
            # the python to JSON conversion before returning
            if par in self._useGlobals:
                # Yes, this needs sending back, but first, does it need
                # changing to a JSON var?
                tmpar = par
                if tmpar in self._pythonParsToJSONPars:
                    tmpar = self._pythonParsToJSONPars[tmpar]
                retGlob[tmpar] = val
                continue

            # Is it a par I renamed for Python? If so, we get the name
            # of it as a Python parameter
            if par in self._JSONParsToPythonPars:
                par = self._JSONParsToPythonPars[par]

            # Is it a actually a parameter in this product?
            if par in self._parTypes:
                # If the parameter was a bool then it has come back as an int
                if (bool in self._parTypes[par]) and (type(val) != bool):
                    val = val == 1 or val == "yes" or val == "1"

                # Otherwise, check the type and try to cast it:
                if not isinstance(val, self._parTypes[par]):
                    # Get the preferred type
                    myType = self._parTypes[par][0]
                    # Cast; will raise an error if it can't
                    val = myType(val)

                if (par in self._specificParValues) and (val not in self._specificParValues[par]):
                    raise ValueError(
                        f"'{val}' is not a valid value for {self.prodType} parmeter {par}. "
                        "Options are: {','.join(self._specificParValues[par])}."
                    )
                self._pars[par] = val
                # Are there any dependencies to set?
                if par in self._parTriggers:
                    if val in self._parTriggers[par]:
                        for depPar, depVal in self._parTriggers[par][val].items():
                            if (depVal is None or depVal == "None") and depPar in self._pars:
                                del self._pars[depPar]
                            elif depVal is not None and depVal != "None":
                                self._pars[depPar] = depVal
                            if not self.silent:
                                print(f"Also setting {self._prodType} {depPar} = {depVal}, because {par} = {val}")
                    if "ANY" in self._parTriggers[par] and val is not None and val != "None":
                        for depPar, depVal in self._parTriggers[par]["ANY"].items():
                            if (depVal is None or depVal == "None") and depPar in self._pars:
                                del self._pars[depPar]
                            elif depVal is not None and depVal != "None":
                                self._pars[depPar] = depVal
                            if not self.silent:
                                print(f"Also setting {self._prodType} {depPar} = {depVal}, because {par} = {val} (ANY)")
                    if "NONE" in self._parTriggers[par] and (val is None or val == "None"):
                        for depar, depVal in self._parTriggers[par]["NONE"].items():
                            self._pars[depar] = depVal
                            if not self.silent:
                                print(f"Also setting {depar} = {depVal}, because {par} = {val}")
        return retGlob

    def removePar(self, par):
        """Remove a specified paramter.

        Raises a ValueError if an invalid parameter is requested

        Parameters
        ----------
        par : str
            The parameter to remove

        Return
        ------
        None

        """
        if par not in self._parTypes:
            # They may have used an JSON parameter instead of a python one
            if par in self._JSONParsToPythonPars:
                par = self._JSONParsToPythonPars[par]
            else:
                raise ValueError(f"{par} is not a recognised {self.prodType} parameter")

        if par not in self._pars:
            # Nothing to do!
            return

        # Are there any dependencies to set?
        if par in self._parTriggers:
            if "NONE" in self._parTriggers[par]:
                for depar, depVal in self._parTriggers[par]["NONE"].items():
                    self._pars[depar] = depVal
                    if not self.silent:
                        print(f"Also setting {depar} = {depVal}")

        del self._pars[par]

    # Checks whether the global par 'par' is something that this product
    # uses/shares
    def usesGlobal(self, par):
        """Return whether this product needs a specified global.

        This checks whether the global parameter 'par' is one which this
        product uses, i.e. it's a shared par.

        Parameters
        ----------
        par : str The parameter to check

        Return
        ------
        bool - whether or not the parameter is a shared global

        """
        if par in self._JSONParsToPythonPars:
            par = self._JSONParsToPythonPars[par]
        return par in self.useGlobals

    # isValid has to check that all of the parameters we need for this
    # product are set This can be a little complex because of the way
    # that some parameters are only needed if other parameters are set,
    # or even set to a specific value.  This is encapsulated in
    # prodParDeps
    def isValid(self):
        """Return whether the product is ready to submit.

        This checks if the product is ready to submit, i.e. all of the
        required parameters are set.

        Parameters
        ----------
        None

        Return
        ------
        A tuple of the form (status, expln)
        status: bool
            True if the request is valid, otherwise False
        expln : string
            A string explaining why the request is invalid

        """
        status = True
        report = ""

        # Check all pars needed by this prod
        for par in self._needPars:
            # If it's not yet set the product isn't valid
            tmp = self._checkParIsSet(par)
            status = status and tmp[0]
            report = report + tmp[1]

        # Now check the dependencies
        for keyPar in self._parDeps:
            # First - is this set?
            if keyPar in self._pars:
                # Yes, so we have to check that any parameters that are
                # required when this is set are set
                # however, this may depend on the value of keypar.
                # Get the value first, makes life easier:
                keyVal = self._pars[keyPar]
                # So, do we have any parameters needed when keyPar is set to keyVal?
                if str(keyVal) in self._parDeps[keyPar]:
                    for par in self._parDeps[keyPar][str(keyVal)]:
                        tmp = self._checkParIsSet(par)
                        status = status and tmp[0]
                        report = report + tmp[1]
                # Also parDeps[keyPar] can have a key ANY which means
                # parameter is needed if keyPar is set, regardless of its value
                if "ANY" in self._parDeps[keyPar]:
                    for par in self._parDeps[keyPar]["ANY"]:
                        tmp = self._checkParIsSet(par)
                        status = status and tmp[0]
                        report = report + tmp[1]

        return (status, report)

    # Internal func to check a needed par is set:
    def _checkParIsSet(self, par):
        """Check if a given parameter is set.

        Internal function.

        Parameters
        ----------
        par : string
            The parameter to check

        Return
        ------
        (status,report)
        status : bool
            Whether the parameter is found or not
        report : string
            Text to report the absence

        """
        status = True
        report = ""
        if par not in self._pars:
            if par not in self._pars:
                status = False
                report = report + f"* The {longProdName[self.prodType]} parameter `{par}` is not set"
                report = report + ".\n"
        return (status, report)

    # getPar returns the parameter in question

    def getPars(self, parName="all", showUnset=False):
        """Return the value of (a) specified parameter/s.

        This returns the current value of the parameter parName,
        or a dictionary of all parameters if 'all' was requested.
        Raises a ValueError if an invalid parameter is sought.

        Parameters
        ----------
        parName : str
            The parameter to get

        showUnset
            When parName='all' this will make parameters not yet set be included.

        Return
        ------
        The value of the parameter, or None if it is not yet set
        """

        if parName == "all":
            if showUnset:
                ret = dict()
                for par in self._parTypes:
                    if par in self._pars:
                        ret[par] = self._pars[par]
                    else:
                        ret[par] = None
                return ret
            else:
                return self._pars

        if parName not in self._parTypes:
            # They may have used an JSON parameter instead of a python one
            if parName in self._JSONParsToPythonPars:
                parName = self._JSONParsToPythonPars[parName]
            else:
                raise ValueError(f"`{parName}` is not a recognised {longProdName[self.prodType]} parameter")
        if parName in self._pars:
            return self._pars[parName]
        else:
            return None

    # Produce the dict, ready for JSON, of pars in this product
    def getJSONDict(self):
        """Return all parameters for this product.

        This returns a dictionary, where keys are the parameters
        JSON (=server) names, not the python names.

        Parameters
        ----------
        None

        Return
        ------
        A dict of parameters

        """
        jsonDict = dict()
        # Go through pars:
        for par in self._pars:
            val = self._pars[par]
            # Bools need converting to 0/1
            if type(val) == bool:
                if val:
                    val = 1
                else:
                    val = 0
            # Do we change the par name for JSON?
            if par in self._pythonParsToJSONPars:
                jsonDict[self._pythonParsToJSONPars[par]] = val
            else:
                jsonDict[par] = val

        return jsonDict

    # Download the products
    def downloadProd(self, url, dir, format, clobber, silent, userStem=None):
        """Download the  data products.

        This will find the actual data product files on the server,
        the product in question was succesfully built, and download it.

        Parameters
        ----------
        url : str
            The URL at which the products are expected.
        dir : str
            The directory in which to save the files.
        format : str
            The required format for the download file
        clobber : bool
            Whether to overwrite the products if they already exist.
        silent : bool
            Whether to print information to the screen or not
        userStem : str
            (Optional) a string to prepend to the filename before
            saving.

        """
        getURL = f"{url}/{self._downloadStem}.{format}"
        outFile = f"{dir}/{self._downloadStem}.{format}"

        if userStem is not None:
            outFile = f"{dir}/{userStem}{self._downloadStem}.{format}"

        if (not clobber) and os.path.exists(outFile):
            raise RuntimeError(f"(Can't save {outFile} as it exists and clobber=False")

        r = requests.get(getURL, allow_redirects=True)
        if r.status_code != 200:  # Check that this is int!
            raise RuntimeError(
                f"Unable to download the product from {getURL}, HTTP return code {r.status_code}: {r.reason}"
            )

        file = open(outFile, "wb")
        file.write(r.content)
        file.close()
        if not self.silent:
            print(f"Downloaded {longProdName[self.prodType]} as `{outFile}`")
        return outFile
