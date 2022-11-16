"""GRB data access functions.

This module provides GRB-specific functions for downloading data,
products or more information. It allows direct access, rather than
having to carry out a query first.

This documentation will be updated when I've written the code

"""
__docformat__ = "restructedtext en"


import pandas as pd
from .. import main as base
from . import download as dl


def GRBNameToTargetID(GRBName, silent=True, verbose=False):
    """Convert a GRB name into a targetID

    Parameters
    ----------

    GRBName : str
        The name of the GRB (e.g. "GRB 060729")

    silent : bool, optional
        Whether to suppress all output (default: ``True``).

    verbose : bool, optional
        Whether to write verbose output (default: ``False``).

    Returns
    -------

    int or None
        On success, the integer targetID; if the GRB is not found,
        ``None``

    """
    if verbose:
        silent = False

    sendData = {"name": GRBName}
    tmp = base.submitAPICall("GRBNameToTargetID", sendData, verbose=verbose)
    if "NOTFOUND" in tmp:
        if not silent:
            print(f"No confirmed GRB with name `{GRBName}` found in the XRT catalogue.")
        return None
    if "targetID" in tmp:
        if not silent:
            print(f"Resolved `{GRBName}` as `{tmp['targetID']}`.")
        return tmp["targetID"]
    else:
        raise RuntimeError("Unknown error; unexpected return; is your swifttools version up to date?")


def _handleGRBListArgument(targetID, GRBName, silent=True, verbose=False):
    """Internal function to handle targetID/GRBName arguments.

    This function receives the targetID and GRBName passed in
    a call, ensures that only one is set, and then converts the value
    into a list if necessary. It also returns a look up of the targetID
    against the input key, which may of course just be the targetID!

    Parameters
    ----------

    targetID : int or None
        The targetID specified by the user

    GRBName : str or None
        The source name specified by the user

    silent : bool, optional
        Whether to suppress all output (default: ``True``).

    verbose : bool, optional
        Whether to write verbose output (default: ``False``).


    Returns
    -------

    list
        A list of the targetIDs supplied

    dict
        A lookup of targetID against key for saving.

    single: bool
        Whether a single value, instead of a list, was supplied.

    """
    if verbose:
        silent = False

    if (targetID is None) == (GRBName is None):
        raise ValueError("Exactly one of `targetID` or `GRBName` must be set.")

    varVal = None
    lookup = {}
    single = False

    if GRBName is not None:
        # Have to convert to targetID
        if isinstance(GRBName, (list, tuple)):
            varVal = []
            for n in GRBName:
                tmp = GRBNameToTargetID(n, silent=silent, verbose=verbose)
                varVal.append(tmp)
                lookup[tmp] = n
        else:
            tmp = GRBNameToTargetID(GRBName, silent=silent, verbose=verbose)
            varVal = [tmp]
            single = True
            lookup[tmp] = GRBName

    else:
        if isinstance(targetID, (list, tuple)):
            varVal = targetID
            lookup = dict(zip(targetID, targetID))
        else:
            varVal = [targetID]
            single = True
            lookup[targetID] = targetID

    return (varVal, lookup, single)


# --------------------------------------------------------------------
# Light curve access


def getLightCurves(
    targetID=None,
    GRBName=None,
    returnData=False,
    saveData=True,
    destDir="lc",
    subDirs=True,
    silent=True,
    verbose=False,
    **kwargs,
):
    """Download a GRB light curve / set of light curves.

    This function can either return the requested light curve data, as
    a dict of pandas DataFrames, or it can save the light curve files to
    disk (or both). It wraps ``ukssdc.data.download._getLightCurve()``
    so most of the arguments are kwargs passed to that.

    You must specify either GRB name(s) or targetID(s), but not both.
    If you supply a list then the keys supplied will be used to
    save/index the data. That is, if you supply a list of targetIDs,
    then the returned dict will use the targetIDs as keys, and if you
    save the light curves then the subdirectory or file prefixes will
    be the targetIDs. If GRBName is set instead, then these will be
    used.

    Parameters
    ----------

    targetID : int or list or tuple, optional
        The name of the GRB to retrieve, or a list of names.

    GRBName : str or list or tuple, optional
        The name of the GRB to retrieve, or a list of names.

    returnData : bool, optional
        Whether to return the organised light curve data from this
        function (default: ``False``).

    saveData : bool, optional
        Whether to save the light curve data to disk (default:
        ``True``).

    subDirs : bool, optional
        Whether to save each object's data to its own subdirectory. Only
        used if ``saveData`` is ``True`` and a list of objects is
        supplied.

    destDir : str, optional
        The directory in which to save the light curves (default: "lc").

    silent : bool, optional
        Whether to suppress all output (default: ``True``).

    verbose : bool, optional
        Whether to write verbose output (default: ``False``).

    **kwargs: dict
        Arguments passed to ``download._getLightCurve``.

    Returns
    -------
    dict
        A dictionary with the light curve information as described
        above.

    """
    if verbose:
        silent = False

    # Handle the arguments into a list, and whether we are getting a
    # single thing.
    targetIDs, lookup, single = _handleGRBListArgument(targetID, GRBName, silent=silent, verbose=verbose)

    # I don't want the prefix argument to be passable in here; it is set
    # by this function, so check for it:
    if "prefix" in kwargs:
        raise ValueError("You cannot set `prefix` for getLightCurves()")

    if saveData:
        base._createDir(destDir, silent=silent, verbose=verbose)

    ret = {}

    for t in targetIDs:
        # We are not necessarily using the targetID as the index; what
        # do we want.
        outDir = destDir
        prefix = ""
        key = lookup[t]
        if verbose:
            print(f"Getting {key}")
        if saveData and subDirs and not single:
            outDir = f"{destDir}/{key}"
            base._createDir(outDir, silent=silent, verbose=verbose)
        elif not single:
            prefix = f"{key}_"

        tmp = dl._getLightCurve(
            type="GRB",
            objectID=t,
            prefix=prefix,
            returnData=returnData,
            saveData=saveData,
            destDir=outDir,
            silent=silent,
            verbose=verbose,
            **kwargs,
        )

        if returnData:
            ret[key] = tmp

    if returnData:
        if single:
            return ret[lookup[targetIDs[0]]]
        else:
            return ret


def saveLightCurves(data, destDir="lc", whichGRBs="all", subDirs=True, **kwargs):
    """Save light curves to text files.

    This will save the light curve data supplied via the `data`
    parameter to disk. By default, this will save all of the data in the
    supplied object but you can request to save only specific subsets.

    Parameters
    ----------

    data : dict
        The light curve data, either a light curve `dict` or a `dict` of
        light curve `dict`s.

    destDir : str, optional
        The directory in which to save the files (default: 'lc').

    whichGRBs : list or str, optional
        A list of the GRBs to save. Should be keys of the data
        object, or 'all' (default: 'all').

    subDirs : bool, optional
        This argument is ignored if ``data`` is a light curve ``dict``,
        rather than a ``dict`` of light curve ``dict``s.

        Whether to save the light curves for the separate GRBs in
        subdirectories of ``destDir``, with directories named by the
        keys in ``data``. If ``False``, the keys will be
        prepended to the file names, since the files for different GRBs
        otherwise all have the same names (default: ``True``).

    **kwargs : dict, optional
        Other arguments to pass to _saveLightCurveFromDict()

    """
    if "silent" in kwargs:
        silent = kwargs["silent"]
    else:
        silent = True
    if "verbose" in kwargs:
        verbose = kwargs["verbose"]
    else:
        verbose = False

    if verbose:
        silent = False

    usePrefix = True
    # Need to check if we have a light curve dict, or a set of dicts.
    if "Datasets" in data:  # LC dict
        usePrefix = False  # Do not prepend this fake sourceID to the file name.
        tmp = {"mySource": data}
        data = tmp
        # If we had an lc dict, then we don't use subDirs (NB a list with one entry does use them)
        subDirs = False

    # Create the output dir, if needed.

    base._createDir(destDir, silent=silent, verbose=verbose)

    # Which sources am I saving?
    if (whichGRBs is None) or (whichGRBs == "all"):
        whichGRBs = data.keys()

    # For GRBs we don't add the time or binning to the extension unless requested
    if "timeFormatInFname" not in kwargs:
        kwargs["timeFormatInFname"] = False
    if "binningInFname" not in kwargs:
        kwargs["binningInFname"] = False

    # prefix should not be in this dict, so remove if it is.
    kwargs.pop("prefix", None)

    # Now start saving light curves, one source at a time
    for source in whichGRBs:
        if source not in data:
            raise ValueError(f"{source} is not in the light curve list.")

        path = destDir
        prefix = ""
        if subDirs:
            path = f"{destDir}/{source}"
        elif usePrefix:
            prefix = f"{source}_"

        dl._saveLightCurveFromDict(data[source], destDir=path, prefix=prefix, **kwargs)


# --------------------------------------------------------------------
# REBIN functions


def rebinLightCurve(GRBName=None, targetID=None, silent=True, verbose=False, **kwargs):
    """Rebin a GRB light curve.

    This will request a GRB light curve be rebinned. It requires either
    a GRB name, or a targetID. It will return a JobID which you must
    save, as this can then be used to check the job status and retrieve
    the light curve.

    Parameters
    ----------

    GRBName : str, optional
        The GRB name.

    targetID : int, optional
        The GRB targetID

    silent : bool, optional
        Whether to suppress all output (default: ``True``).

    verbose : bool, optional
        Whether to write verbose output (default: ``False``).

    kwargs : dict
        Parameters defining the binning; please see the online
        documentation for a full description of these.

    Returns
    -------

    int
        The job identifier, which is needed to retrieve your data.

    """
    if verbose:
        silent = False

    if (targetID is None) == (GRBName is None):
        raise ValueError("Exactly one of `GRBName` or `targetID` must be set.")

    # Do I need to find the targetID?
    if GRBName is not None:
        if not silent:
            print(f"Need to convert `{GRBName}` into a targetID")
        targetID = GRBNameToTargetID(GRBName)
        if targetID is None:
            raise ValueError(f"No such GRB `{GRBName}` found.")
        if not silent:
            print(f"Got targetID: `{targetID}`")
        if "name" not in kwargs:
            kwargs["name"] = GRBName

    return dl._rebinLightCurve("GRB", targetID, silent=silent, verbose=verbose, **kwargs)


def checkRebinStatus(JobID, silent=True, verbose=False):
    """Check the status of a rebin job."""
    if verbose:
        silent = False

    if not isinstance(JobID, int):
        raise ValueError("JobID must be an int")

    return dl._checkRebinStatus(JobID, silent=silent, verbose=verbose)


def rebinComplete(JobID):
    """Check whether a rebin job is complete

    Parameters
    ----------

    JobID : int
        The Job ID.

    Returns
    -------

    bool
        Whether the job is complete or not.

    """
    if not isinstance(JobID, int):
        raise ValueError("JobID must be an int")

    return dl._rebinComplete(JobID)


def cancelRebin(JobID, silent=True, verbose=False):
    """Cancels a rebin job.

    Parameters
    ----------

    JobID : int
        The Job ID.

    silent : bool, optional
        Whether to suppress all output (default: ``True``).

    verbose : bool, optional
        Whether to write verbose output (default: ``False``).

    Returns
    -------

    dict
        A dictionary with keys:

        statusCode : int
            :A code indicating the status of the job.

        statusText : str
            :A textual description of the job status.

    """
    if verbose:
        silent = False

    return dl._cancelRebin(JobID, silent=silent, verbose=verbose)


def getRebinnedLightCurve(JobID, **kwargs):
    """Get the light curves produced by a rebin command.

    This is just a wrapper to a generic function:
    download._getLightCurve()

    For details of the kwargs, see the online documentation, or the help
    for the above function.
    """
    if not rebinComplete(JobID):
        raise RuntimeError("Cannot get light curves; this job is not complete.")

    ret = dl._getLightCurve("REBIN_LC", JobID, **kwargs)

    if ("returnData" in kwargs) and kwargs["returnData"]:
        return ret


# --------------------------------------------------------------------
# Spectrum access


def getSpectra(
    targetID=None,
    GRBName=None,
    JobID=None,
    returnData=False,
    saveData=True,
    saveImages=True,
    destDir="spec",
    subDirs=True,
    silent=True,
    verbose=False,
    **kwargs,
):
    """Download a GRB spectrum / set of spectra.

    This function can either return the fit results for the specified
    GRBs, as a dict of pandas DataFrames, or it can save the spectral
    files to disk (or both).

    You must specify either GRB name(s) or targetID(s), but not both.
    If you supply a list then the keys supplied will be used to
    save/index the data. That is, if you supply a list of targetIDs,
    then the returned dict will use the targetIDs as keys, and if you
    save the spectra  then the subdirectory or file prefixes will
    be the targetIDs. If GRBName is set instead, then these will be
    used.

    Parameters
    ----------

    targetID : int or list or tuple, optional
        The name of the GRB to retrieve, or a list of names.

    GRBName : str or list or tuple, optional
        The name of the GRB to retrieve, or a list of names.

    JobID : int, optional
        The identifier of a time-sliced spectrum to download.

    returnData : bool, optional
        Whether to return the organised light curve data from this
        function (default: ``False``).

    saveData : bool, optional
        Whether to save the light curve data to disk (default:
        ``True``).

    subDirs : bool, optional
        Whether to save each object's data to its own subdirectory. Only
        used if ``saveData`` is ``True`` and a list of objects is
        supplied.

    destDir : str, optional
        The directory in which to save the light curves (default: "lc").

    silent : bool, optional
        Whether to suppress all output (default: ``True``).

    verbose : bool, optional
        Whether to write verbose output (default: ``False``).

    **kwargs: dict
        Arguments passed to ``download._getLightCurve``.

    Returns
    -------
    dict
        A dictionary with the light curve information as described
        above.

    """
    if verbose:
        silent = False

    if saveData and not subDirs and ("extract" in kwargs) and kwargs["extract"]:
        raise RuntimeError("You cannot have subDirs as False if you are extracting data.")

    # Handle the arguments into a list, and whether we are getting a
    # single thing.
    isTimeSlice = False
    if JobID is not None:
        if not isinstance(JobID, int):
            raise ValueError("`JobID` should be an int")
        targetIDs = (JobID,)
        lookup = {JobID: JobID}
        single = True
        isTimeSlice = True
    else:
        targetIDs, lookup, single = _handleGRBListArgument(targetID, GRBName, silent=silent, verbose=verbose)
        isTimeSlice = False

    # I don't want the prefix argument to be passable in here; it is set
    # by this function, so check for it:

    if saveData or saveImages:
        base._createDir(destDir, silent=silent, verbose=verbose)

    ret = {}
    sendData = {"type": "GRB"}
    if isTimeSlice:
        sendData["type"] = "timeslice"

    for t in targetIDs:
        # We are not necessarily using the targetID as the index; what
        # do we want.
        prefix = ""
        outDir = destDir
        key = lookup[t]
        if verbose:
            print(f"Getting {key}")
        if saveData and subDirs and not single:
            outDir = f"{destDir}/{key}"
            base._createDir(outDir, silent=silent, verbose=verbose)
        elif not single:
            prefix = f"{key}_"

        # Now, first get the data:
        sendData["objectID"] = t

        tmp = base.submitAPICall("downloadSpectrum", sendData, verbose=verbose)

        if (saveData or saveImages) and "NoSpectrum" not in tmp:
            dl._saveSpectrum(
                tmp,
                saveData=saveData,
                saveImages=saveImages,
                prefix=prefix,
                destDir=outDir,
                silent=silent,
                verbose=verbose,
                **kwargs,
            )

        if returnData:
            ret[key] = tmp

    if returnData:
        if single:
            return ret[lookup[targetIDs[0]]]
        else:
            return ret


def saveSpectra(data, destDir="spec", whichGRBs="all", silent=True, verbose=False, **kwargs):
    """Save the spectral data to disk.

    This will download and save the spectral files from a previous
    ``getSpectra()`` call.

    Parameters
    ----------

    data : dict
        The object returned by ``getSXPSSpectra()``

    destDir : str, optional
        The directory in which to save the spectra (default: "spec").

    whichGRBs : list
        A list of the GRBs to save. Should be keys of the data
        object.

    silent : bool, optional
        Whether to suppress all output (default: ``True``).

    verbose : bool, optional
        Whether to write verbose output (default: ``False``).

    **kwargs : dict, optional
        Arguments to pass to ``download.dl._saveSpectrum()``

    """
    if verbose:
        silent = False

    # Little hack needed here to handle the case that we have only a single spectrum, not a dict of LCs
    # We will know this because it will have the 'Datasets' key
    single = False
    if "rnames" in data:
        tmp = {"mySource": data}
        data = tmp
        single = True

    # Create the output dir, if needed.
    base._createDir(destDir, silent=silent, verbose=verbose)

    # Which sources am I saving?
    if (whichGRBs is None) or (whichGRBs == "all"):
        whichGRBs = data.keys()

    # Now start saving light curves, one source at a time
    for source in whichGRBs:
        if source not in data:
            raise ValueError(f"{source} is not in the spectra available.")
        if "NoSpectrum" in data[source]:
            if not silent:
                print(f"Source `{source}` has no spectra.")
            continue

        path = destDir
        if not single:
            path = f"{destDir}/{source}"
            base._createDir(path, silent=silent, verbose=verbose)

        dl._saveSpectrum(data[source], destDir=path, silent=silent, verbose=verbose, **kwargs)


# --------------------------------------------------------------------
# TIMESLICE functions


def timesliceSpectrum(
    GRBName=None, targetID=None, slices=None, mode="BOTH", redshift=None, grades="all", silent=True, verbose=False
):
    """Rebin time-slicing of a GRB spectrum.

    This will request the creation of spectra of the selected GRB with
    specific time regions. The job will be submitted to a queue, so this
    function only returns the jobID, which can then be used to query the
    status or download the spectrum.

    The information about the time intervals you want to create are
    contained within the ``slices`` and (optionally) ``mode`` arguments.
    ``slices`` is a ``dict`` with one entry for each spectrum that you
    want to create. The key should be a string label that will be used
    to identify the spectrum; the value should be either a string,
    giving the time interval(s), or a two-element list giving the string
    and XRT mode desired. In the former case, the mode will be set to
    the value supplied as the ``mode`` argument.

    Time intervals should be supplied as 'start-stop' times, with commas
    used to separate multiple intervals if appropriate. Time intervals
    can be either seconds since the GRB T0, Swift MET, or an obsid
    (preceded with OBS). Note that in the latter case, this does not
    mean that only the specified observation will be included, but all
    times covered by that observation will be included. Usually these
    are the same thing, but sometimes there can be observations which
    overlap in time.

    The following example ``slices`` dict demonstrates valid slices:

    slices = {
        'slice1': '100-400',
        'slice2': ['200-500', 'WT'],
        'slice3': ['100-300,1000-1500', 'BOTH']
        'slice4': ['OBS00282445001-OBS0082445001', 'PC']
    }

    The first instance requests a spectrum called 'slice1' covering
    times 100-400 s since T0, for whichever mode was specified by the
    ``mode`` parameter.

    The second instance requests a spectrum called 'slice2' which covers
    times 200-500 s since T0, using only WT mode.

    The third instance requests a spectrum ('slice3') which covers times
    100-300 and 1000-1500 since T0 and uses both modes.

    The final instance requests the times covered by a single obsid:
    00282445001. Note that even though only one obsID is given, it is
    given as the start and end as a time range is needed.

    If the time values were >10^8 then they would be interpreted as MET
    values.

    Parameters
    ----------

    GRBName : str, optional
        The GRB name.

    targetID : int, optional
        The GRB targetID

    slices : dict
        The time-slices you want to create. This is described in detail
        above.

    mode : str, optional
        The XRT mode to use if not specified in the slices dict. Must be
        'WT', 'PC' or 'BOTH' (default: 'BOTH').

    redshift: float or str, optional
        The redshift to use when fitting the intrinsic aborption. If
        ``None`` then the value current known to the GRB system will be
        used, or no redshift if none is known. If the string 'NONE' then
        no redshift will be used in the fit (default: ``None``).

    grades: int or str, optional
        Which event grades to include in the spectrum, can be 'all', 0
        or 4. 'all' will use grades 0-12, 0 will use grade 0, and 4 will
        use grades 0-4 for PC mode and grade 0 for WT mode.

    silent : bool, optional
        Whether to suppress all output (default: ``True``).

    verbose : bool, optional
        Whether to write verbose output (default: ``False``).

    Returns
    -------

    int
        The job identifier, which is needed to retrieve your data.

    """
    if verbose:
        silent = False

    if (targetID is None) == (GRBName is None):
        raise ValueError("Exactly one of `GRBName` or `targetID` must be set.")

    # Do I need to find the targetID?
    if GRBName is not None:
        if not silent:
            print(f"Need to convert `{GRBName}` into a targetID")
        targetID = GRBNameToTargetID(GRBName)
        if targetID is None:
            raise ValueError(f"No such GRB `{GRBName}` found.")
        if not silent:
            print(f"Got targetID: `{targetID}`")

    # Check default mode
    mode = mode.upper()
    if mode not in ("PC", "WT", "BOTH"):
        raise ValueError(f"`mode` should be `PC`, `WT` or `BOTH`, not `{mode}`")

    # Need to parse the slices dict
    if not isinstance(slices, dict):
        raise ValueError("`slices` must be a dict")
    times = []
    rnames = []
    modes = []

    for name, slice in slices.items():
        if isinstance(slice, str):
            rnames.append(name)
            times.append(slice)
            modes.append(mode)
        elif isinstance(slice, (list, tuple)):
            rnames.append(name)
            times.append(slice[0])
            if len(slice) > 1:
                modes.append(slice[1])
            else:
                modes.append(mode)
        else:
            raise ValueError(f"Slice entry `{name}` is invalid.")

    # print(f"Going to call with:\nrnames: {rnames}\ntimes:{times}\nmodes:{modes}")

    # NOTE: The rebin function does this via a generic function in downloads.py, because I want to be able to rebin
    # other things (e.g. user objects); for spectra this is not necessary as spectra are built from scratch, time
    # slicing is really a bespoke way to call user objects but for a GRB-like spectral fit.  So, do the submission here.
    # If I ever change my mind I can just move the stuff below into a function in download.py

    sendData = {"targetID": targetID, "rnames": rnames, "times": times, "modes": modes}
    if GRBName is not None:
        sendData["name"] = GRBName

    if grades is not None:
        sendData["grades"] = grades

    # Handle redshift
    if redshift is not None:
        if redshift == "NONE" or isinstance(redshift, float):
            sendData["redshift"] = redshift
        else:
            raise ValueError("Redshift should be a float or 'NONE'")

    tmp = base.submitAPICall("timesliceSpectrum", sendData, verbose=verbose, minKeys=("JobID",))
    t = int(tmp["JobID"])
    if verbose:
        print(f"Success: JobID={t}")
    return t

    # return dl._rebinLightCurve("GRB", targetID, binMeth=binMeth, silent=silent, verbose=verbose, **kwargs)


def checkTimesliceStatus(JobID, silent=True, verbose=False):
    """Check the status of a timeslice spectrum job.

    Parameters
    ----------

    JobID : int
        The Job ID.

    silent : bool, optional
        Whether to suppress all output (default: ``True``).

    verbose : bool, optional
        Whether to write verbose output (default: ``False``).

    Returns
    -------

    dict
        A dictionary with keys:

        statusCode : int
            :A code indicating the status of the job.

        statusText : str
            :A textual description of the job status.

    """
    if verbose:
        silent = False

    if not isinstance(JobID, int):
        raise ValueError("JobID must be an int")

    if not isinstance(JobID, int):
        raise ValueError("JobID must be an int")

    sendData = {"JobID": JobID}
    tmp = base.submitAPICall("checkSliceStatus", sendData, verbose=verbose, minKeys=("status", "text"))
    ret = {"statusCode": tmp["status"], "statusText": tmp["text"]}

    return ret


def timesliceComplete(JobID):
    """Check whether a timeslice spectrum job is complete

    Parameters
    ----------

    JobID : int
        The Job ID.

    Returns
    -------

    bool
        Whether the job is complete or not.

    """
    if not isinstance(JobID, int):
        raise ValueError("JobID must be an int")

    tmp = checkTimesliceStatus(JobID, silent=True, verbose=False)

    if tmp["statusCode"] == 4:
        return True
    else:
        return False


def cancelTimeslice(JobID, silent=True, verbose=False):
    """Cancels a timeslice job.

    Parameters
    ----------

    JobID : int
        The Job ID.

    silent : bool, optional
        Whether to suppress all output (default: ``True``).

    verbose : bool, optional
        Whether to write verbose output (default: ``False``).

    Returns
    -------

    dict
        A dictionary with keys:

        statusCode : int
            :A code indicating the status of the job.

        statusText : str
            :A textual description of the job status.

    """
    if verbose:
        silent = False

    if not isinstance(JobID, int):
        raise ValueError("JobID must be an int")

    if not isinstance(JobID, int):
        raise ValueError("JobID must be an int")

    sendData = {"JobID": JobID}
    tmp = base.submitAPICall("cancelSlice", sendData, verbose=verbose, skipErrors=True)

    if "OK" in tmp:
        return True
    else:
        if verbose or not silent:
            print("Cannot cancel job - it may have already completed.")
        return False


# --------------------------------------------------------------------
# Burst Analyser access


def getBurstAnalyser(
    targetID=None,
    GRBName=None,
    returnData=False,
    instruments="all",
    BATBinning="all",
    bands="all",
    nosys="no",
    incbad="yes",
    saveData=True,
    downloadTar=False,
    subDirs=True,
    destDir="BurstAn",
    clobber=False,
    skipErrors=False,
    silent=True,
    verbose=False,
    **kwargs,
):
    """Download and/or save burst analyser data.

    This function downloads and/or saves the burst analyser data for
    a GRB or set of GRBs. There are three ways in which the data can be
    obtained, depending on which parameters you specify. The options
    are:

    returnData
        The function returns a ``dict`` which contains the requested
        data.

    saveData
        The data downloaded are saved to files.

    downloadTar
        The tar file from the website is downloaded.

    A full discussion of these points is beyond the scope of a docstring
    and so you should read the online API documentation. In very-short
    summary:

    * returnData creates a ``dict``, indexed by instrument (BAT, XRT,
      UVOT), and within that indexed again by energy band (BAT is also
      also indexed by binning). Within this are light curves, which are
      formatted like all light curves in this module; that is: the
      ``dict`` has a 'Datasets' key listing the datasets, also also a
      key corresponding to each entry in 'Datasets' - those contain the
      actual light curve data in the form of pandas DataFrames.

      For the burst analyser, these differ from the products available
      on the web site, in that the photon index and energy conversion
      factor have been merged into the same data frame as the flux,
      and the flux errors appear twice: once as on the website, and once
      with the ECF error propagated in.

    * saveData Basically saves every DataFrame in returnData to its own
      file.

    * downloadTar Literally downloads the tar file of all the files
      which are used to power the website. For historical reasons, there
      are separate files for flux, photon index and conversion factor,
      which means that there are a lot more files.

    Parameters
    ----------

    targetID : int or list or tuple, optional
        The name of the GRB to retrieve, or a list of names.

    GRBName : str or list or tuple, optional
        The name of the GRB to retrieve, or a list of names.

    returnData : cool, optional
        Whether to return a dict containing all of the downloaded data
        (default: ``True``).

    instruments : str or list, optional
        Which instrument data to retrieve. Must be 'all' or a list of
        instruments (from: BAT, XRT, UVOT) (default: 'all').

    BATBinning : str or list, optional
        Which BAT binning methods' data to retrieve. Must be 'all' or a
        case-insensitive list of binning methods (e.g. ['snr4',
        'timedel0.064']); (default: 'all').

    bands : str or list, optional
        Which energy band data to retrieve. Must be 'all' or a list of
        case-insensitive bands (from 'ObservedFlux', 'Density',
        'BATBand', 'XRTBand'); (default: 'all').

    nosys : str
        Whether to return the light curves from which the WT
        systematic error has been removed. Can be 'yes', 'no',
        'both' -- the latter returning datasets with and without the
        systematic error. Only used if ``returnData=True`` or
        ``saveData=True`` (default: 'no').

    incbad : str
        Whether to return the light curves in which the datapoints
        flagged as potentially unreliable to due centroiding issues
        have been included. Can be 'yes', 'no', 'both' -- the latter
        returning datasets with and without the unreliable
        datapoints. Only used if ``returnData=True`` or
        ``saveData=True`` (default: 'yes').

    saveData : bool, optional
        Whether to save the data downloaded as files (default: ``True``)

    downloadTar : bool, optional
        Whether to download the tar file on the burst analyser website,
        with all the files created for that site.

    subDirs : bool, optional
        Whether to save each object's data to its own subdirectory. Only
        used if ``saveData`` or ``downloadTar`` is ``True`` and a list
        of objects is supplied.

    destDir : str, optional
        The directory in which to save the data (default: "BurstAn").

    clobber : bool, optional
        Whether to overwrite files if they exist (default: ``False``).

    skipErrors : bool, optional
        Whether to continue if a problem occurs with one file
        (default: ``False``).

    silent : bool, optional
        Whether to suppress all output (default: ``True``).

    verbose : bool, optional
        Whether to write verbose output (default: ``False``).

    **kwargs : dict, optional
        If ``saveData=True``, any arguments to pass to
        ``saveSingleBurstAn()``.

    Returns
    -------
    dict
        A dictionary with the light curve information in a huge bloody
        complex mess (EDIT ME).

    """
    if verbose:
        silent = False

    # Handle the arguments into a list, and whether we are getting a
    # single thing.
    targetIDs, lookup, single = _handleGRBListArgument(targetID, GRBName, silent=silent, verbose=verbose)

    if saveData or downloadTar:
        base._createDir(destDir, silent=silent, verbose=verbose)

    ret = {}
    for t in targetIDs:
        key = lookup[t]
        if verbose:
            print(f"Getting {key} ({t})")

        path = destDir
        if subDirs and (saveData or downloadTar) and (not single):
            path = f"{destDir}/{key}"
            base._createDir(path, silent=silent, verbose=verbose)

        # Tar file first - relatively easy:
        if downloadTar:
            tarPath = path
            if saveData:
                tarPath = f"{path}/fromTar"
                # targPath above may not be unique, needs to be
                if (not single) and (not subDirs):
                    tarPath = f"{path}/{key}_fromTar"

            # OK, now get the URL
            sendData = {"targetID": t}
            tmp = base.submitAPICall("getBurstAnalyserTarURL", sendData, verbose=verbose, minKeys=("URL",))

            # Create the path
            base._createDir(tarPath, silent=silent, verbose=verbose)

            # And get the tar data:
            ok = dl._saveTar(tmp["URL"], tarPath, strip=True, clobber=clobber, silent=silent, verbose=verbose, **kwargs)
            if not (ok or skipErrors):
                raise RuntimeError(f"Failed getting tar for {key}")

        if saveData or returnData:

            sendData = {
                "targetID": t,
                "instruments": instruments,
                "bands": bands,
                "BATBinning": BATBinning,
                "incbad": incbad,
                "nosys": nosys,
            }
            tmp = base.submitAPICall("downloadBurstAnalyser", sendData, verbose=verbose, minKeys=("Instruments",))

            # If we are getting multiple light curves, and no subdirs, then the file names will need prefixes.
            prefix = ""
            if (not subDirs) and (not single):
                prefix = key

            # Trying to do the handle Light Curve thing is a pain, because
            # that function returns something new, it does not edit in place.
            # I'm not sure how I can make it edit in place, so I'm going to have to do this
            # a crap way, for now at least.

            if "BAT" in tmp["Instruments"]:
                # handle HR data direct
                if "HRData" in tmp["BAT"]:
                    tmp["BAT"]["HRData"] = pd.DataFrame(
                        tmp["BAT"]["HRData"]["data"], columns=tmp["BAT"]["HRData"]["columns"], dtype=float
                    )

                for b in tmp["BAT"]["Binning"]:
                    tmp["BAT"][b] = dl._handleLightCurve(tmp["BAT"][b], silent=silent, verbose=verbose)
                    for d in tmp["BAT"][b]["Datasets"]:
                        tmp["BAT"][b][d]["BadBin"] = tmp["BAT"][b][d]["BadBin"].astype(bool)

            if "BAT_NoEvolution" in tmp["Instruments"]:
                for b in tmp["BAT_NoEvolution"]["Binning"]:
                    tmp["BAT_NoEvolution"][b] = dl._handleLightCurve(
                        tmp["BAT_NoEvolution"][b], silent=silent, verbose=verbose
                    )
                    for d in tmp["BAT_NoEvolution"][b]["Datasets"]:
                        tmp["BAT_NoEvolution"][b][d]["BadBin"] = tmp["BAT_NoEvolution"][b][d]["BadBin"].astype(bool)

            if "XRT" in tmp["Instruments"]:
                # handle HR data direct
                keepMe = {}
                for m in ("WT", "PC"):
                    if f"HRData_{m}" in tmp["XRT"]:
                        # print(f"Handling `HRData_{m}`")

                        keepMe[m] = pd.DataFrame(
                            tmp["XRT"][f"HRData_{m}"]["data"], columns=tmp["XRT"][f"HRData_{m}"]["columns"], dtype=float
                        )
                    # else:
                    #     print(f"Cannot find `HRData_{m}` in XRT")
                tmp["XRT"] = dl._handleLightCurve(tmp["XRT"], silent=silent, verbose=verbose)
                for m in ("WT", "PC"):
                    if m in keepMe:
                        tmp["XRT"][f"HRData_{m}"] = keepMe[m]

            if "UVOT" in tmp["Instruments"]:
                tmp["UVOT"] = dl._handleLightCurve(tmp["UVOT"], silent=silent, verbose=verbose)

            if saveData:
                saveSingleBurstAn(
                    tmp,
                    destDir=path,
                    prefix=prefix,
                    clobber=clobber,
                    skipErrors=skipErrors,
                    silent=silent,
                    verbose=verbose,
                    **kwargs,
                )

            if returnData:
                ret[key] = tmp
    if returnData:
        if single:
            ret = ret[lookup[targetIDs[0]]]
        return ret


def saveBurstAnalyser(data, destDir="spec", whichGRBs="all", subDirs=True, silent=True, verbose=False, **kwargs):
    """Save the burst analyser data to disk.

    This will download and save the spectral files from a previous
    ``getBurstAnalyser()`` call.

    Parameters
    ----------

    data : dict
        The object returned by ``getSXPSSpectra()``

    destDir : str, optional
        The directory in which to save the spectra (default: "spec").

    whichGRBs : list
        A list of the GRBs to save. Should be keys of the data
        object.

    subDirs : bool, optional
        Whether to save each object's data to its own subdirectory. Only
        used if ``saveData`` is ``True`` and a list of objects is
        supplied.

    silent : bool, optional
        Whether to suppress all output (default: ``True``).

    verbose : bool, optional
        Whether to write verbose output (default: ``False``).

    **kwargs : dict, optional
        Arguments to pass to ``download.dl._saveSpectrum()``

    """
    if verbose:
        silent = False

    # Little hack needed here to handle the case that we have only a single spectrum, not a dict of LCs
    # We will know this because it will have the 'Datasets' key
    usePrefix = True
    if "Instruments" in data:
        usePrefix = False  # Do not prepend this fake sourceID to the file name.
        tmp = {"mySource": data}
        data = tmp
        if subDirs and not verbose:
            print("Ignoring subDirs as only a single source was provided.")
        subDirs = False

    # Create the output dir, if needed.
    base._createDir(destDir, silent=silent, verbose=verbose)

    # Which sources am I saving?
    if (whichGRBs is None) or (whichGRBs == "all"):
        whichGRBs = data.keys()

    # Now start saving light curves, one source at a time
    for source in whichGRBs:
        if source not in data:
            raise ValueError(f"{source} is not in the light curve list.")
        path = destDir
        prefix = ""
        if subDirs:
            path = f"{destDir}/{source}"
            base._createDir(path, silent=silent, verbose=verbose)

        elif usePrefix:
            prefix = f"{source}_"

        saveSingleBurstAn(
            data[source],
            destDir=path,
            silent=silent,
            verbose=verbose,
            prefix=prefix,
            **kwargs,
        )


def saveSingleBurstAn(
    data,
    destDir="burstAn",
    prefix="",
    instruments="all",
    asQDP=False,
    header=False,
    sep=",",
    suff=None,
    usePropagatedErrors=False,
    badBATBins=False,
    clobber=False,
    skipErrors=False,
    silent=True,
    verbose=False,
    **kwargs,
):
    """Save downloaded burst analyser data to disk.

    This takes a data structure for a previously-downloaded burst
    analyser dataset, and saves it to disk.

    NOTE: This is for a **single** object, not a set of objects, i.e if
    you downloaded a set of objects, then you received a dict, with one
    entry per object; a single entry should be passed here as the data
    argument.

    Parameters
    ----------

    data : dict
        A dictionary of burst analyser data, previously downloaded.

    destDir : str
        The directory in which to save the data.

    prefix : str, optional
        A string to prepend to the filenames when saving them.

    instruments : str or list, optional
        Which instrument data to save. Must be 'all' or a list of
        instruments (from: BAT, XRT, UVOT) (default: 'all').

    asQDP : bool, optional
        Whether to save in qdp format. Overrides ``sep``
        (default: ``False``).

    header : bool, optional
        Whether to print a header row (default: ``False``).

    sep : str, optional
        Separator to use for columns in the file (default: ',').

    suff : str
        If specified, the file suffix to use (default: ``.dat``, or
        ``.qdp`` if ``asQDP=True``).

    usePropagatedErrors=False : bool, optional
        Whether the flux errors to write to the files are those which
        have had the uncertainty on the ECF propagated (default:
        ``False``) **only effective if ``asQDP=True``**

    badBATBins : bool, optional
        Whether to write out BAT bins flagged as 'bad' (default:
        ``False``).

    clobber : bool, optional
        Whether to overwrite files if they exist (default: ``False``).

    skipErrors : bool, optional
        Whether to continue if a problem occurs with one file
        (default: ``False``).

    silent : bool, optional
        Whether to suppress all output (default: ``True``).

    verbose : bool, optional
        Whether to write verbose output (default: ``False``).

    **kwargs : dict, optional
        Not needed, but stops errors due to the way this can be called.

    """
    if verbose:
        silent = False

    if asQDP:
        if (not silent) and (sep != "\t"):
            print("Setting separator to tab, for 'qdp-style; saving")
        sep = "\t"

    if suff is None:
        suff = ".dat"
        if asQDP:
            suff = ".qdp"

    if instruments == "all":
        instruments = data["Instruments"]

    base._createDir(destDir, silent=silent, verbose=verbose)

    # This has to be per instrument as there are small differences between
    if ("BAT" in data) and ("BAT" in instruments):
        if "HRData" in data["BAT"]:
            qdpH = None
            if asQDP:
                qdpH = "READ TERR 1 2 3 4 5 6 7"

            cols = data["BAT"]["HRData"].columns.tolist()
            fname = f"{destDir}/{prefix}BAT_HR{suff}"
            ok = dl._saveDFToDisk(
                data["BAT"]["HRData"],
                fname,
                cols,
                header,
                sep,
                qdpH,
                asQDP,
                clobber=clobber,
                silent=silent,
                verbose=verbose,
            )
            if not (ok or skipErrors):
                raise RuntimeError("Failed saving BAT HR data to disk")

        for b in data["BAT"]["Binning"]:
            for d in data["BAT"][b]["Datasets"]:
                tmp = data["BAT"][b][d]
                cols = tmp.columns.tolist()
                cols = [x for x in cols if x != "BadBin"]
                fname = f"{destDir}/{prefix}BAT_{b}_{d}{suff}"
                qdpH = None

                # If we don't want the bad data, filter them:
                if not badBATBins:
                    # flake is wrong, is False crashes!
                    tmp = data["BAT"][b][d][data["BAT"][b][d]["BadBin"] == False]  # noqa;

                # For QDP, this gets more complicated, we need to filter the columns to get rid of the unwanted errors
                if asQDP:
                    qdpH = "READ TERR 1 2 3 4"
                    removeStem = "WithECFErr"
                    if usePropagatedErrors:
                        removeStem = ""
                    cols = [x for x in cols if (x != f"FluxPos{removeStem}") and (x != f"FluxNeg{removeStem}")]

                ok = dl._saveDFToDisk(
                    data["BAT"][b][d],
                    fname,
                    cols,
                    header,
                    sep,
                    qdpH,
                    asQDP,
                    clobber=clobber,
                    silent=silent,
                    verbose=verbose,
                )
                if not (ok or skipErrors):
                    raise RuntimeError("Failed saving BAT data to disk")

    if ("BAT_NoEvolution" in data) and ("BAT" in instruments):
        for b in data["BAT_NoEvolution"]["Binning"]:
            for d in data["BAT_NoEvolution"][b]["Datasets"]:
                tmp = data["BAT_NoEvolution"][b][d]
                cols = tmp.columns.tolist()
                cols = [x for x in cols if x != "BadBin"]
                fname = f"{destDir}/{prefix}BAT_NoEvolution_{b}_{d}{suff}"
                qdpH = None

                # If we don't want the bad data, filter them:
                if not badBATBins:
                    tmp = data["BAT_NoEvolution"][b][d][data["BAT_NoEvolution"][b][d]["BadBin"] == False]  # noqa

                if asQDP:
                    qdpH = "READ TERR 1 2"

                ok = dl._saveDFToDisk(
                    data["BAT_NoEvolution"][b][d],
                    fname,
                    cols,
                    header,
                    sep,
                    qdpH,
                    asQDP,
                    clobber=clobber,
                    silent=silent,
                    verbose=verbose,
                )
                if not (ok or skipErrors):
                    raise RuntimeError("Failed saving BAT_NoEvolution data to disk")

    if ("XRT" in data) and ("XRT" in instruments):
        for m in ("WT", "PC"):
            for s in ("", "_incbad"):
                k = f"HRData_{m}{s}"
                if k in data["XRT"]:
                    qdpH = None
                    if asQDP:
                        qdpH = "READ TERR 1 2 3 4 5 6 7"

                    cols = data["XRT"][k].columns.tolist()
                    fname = f"{destDir}/{prefix}XRT_HR_{m}{s}{suff}"
                    ok = dl._saveDFToDisk(
                        data["XRT"][k],
                        fname,
                        cols,
                        header,
                        sep,
                        qdpH,
                        asQDP,
                        clobber=clobber,
                        silent=silent,
                        verbose=verbose,
                    )
                    if not (ok or skipErrors):
                        raise RuntimeError(f"Failed saving XRT {m}{s}-mode HR data to disk")

        for d in data["XRT"]["Datasets"]:
            fname = f"{destDir}/{prefix}XRT_{d}{suff}"
            qdpH = None
            cols = data["XRT"][d].columns.tolist()
            # For QDP, this gets more complicated, we need to filter the columns to get rid of the unwanted errors
            if asQDP:
                qdpH = "READ TERR 1 2 3 4"
                removeStem = "WithECFErr"
                if usePropagatedErrors:
                    removeStem = ""
                cols = [x for x in cols if (x != f"FluxPos{removeStem}") and (x != f"FluxNeg{removeStem}")]

            ok = dl._saveDFToDisk(
                data["XRT"][d], fname, cols, header, sep, qdpH, asQDP, clobber=clobber, silent=silent, verbose=verbose
            )
            if not (ok or skipErrors):
                raise RuntimeError("Failed saving XRT data to disk")

    if ("UVOT" in data) and ("UVOT" in instruments):
        for d in data["UVOT"]["Datasets"]:
            fname = f"{destDir}/{prefix}UVOT_{d}{suff}"
            qdpH = None
            cols = data["UVOT"][d].columns.tolist()
            if asQDP:
                qdpH = "READ TERR 1 2"

            ok = dl._saveDFToDisk(
                data["UVOT"][d], fname, cols, header, sep, qdpH, asQDP, clobber=clobber, silent=silent, verbose=verbose
            )
            if not (ok or skipErrors):
                raise RuntimeError("Failed saving UVOTdata to disk")


# --------------------------------------------------------------------
# Data access


def _getTargetsForGRB(targetID):
    """Internal function to get all targets for a GRB.

    Parameters
    ----------

    targetID : str or int
        The GRB targetID

    Returns
    -------

    list
        The targetIDs for this GRB.

    """

    sendData = {"targetID": targetID}
    tmp = base.submitAPICall("getGRBTargetList", sendData, minKeys=("targetList",))
    return tmp["targetList"]


def getObsData(
    targetID=None,
    GRBName=None,
    silent=True,
    verbose=False,
    **kwargs,
):
    """Download the obsData associated with the GRB(s).

    This function takes a GRB targetID or name (or a list of them) and
    downloads the obs data associated with these GRB. It uses
    ``ukssdc.data.downloadObsData()`` and passes most arguments to that.

    Parameters
    ----------

    targetID : int or list or tuple, optional
        The name of the GRB to retrieve, or a list of names.

    GRBName : str or list or tuple, optional
        The name of the GRB to retrieve, or a list of names.

    silent : bool, optional
        Whether to suppress all output (default: ``True``).

    verbose : bool, optional
        Whether to write verbose output (default: ``False``).

    **kwargs: dict
        Arguments passed to ``ukssdc.data.downloadObsData()``.

    """
    if verbose:
        silent = False

    # Handle the arguments into a list, and whether we are getting a
    # single thing.
    targetIDs, lookup, single = _handleGRBListArgument(targetID, GRBName, silent=silent, verbose=verbose)

    for t in targetIDs:
        if verbose:
            print(f"Getting {lookup[t]}")
        targList = _getTargetsForGRB(t)
        if not silent:
            print(f"Have to get targetIDs: {targList}")
        dl.downloadObsDataByTarget(targList, silent=silent, verbose=verbose, **kwargs)


def getPositions(targetID=None, GRBName=None, positions="all", silent=True, verbose=False):
    """Get the GRB position(s).

    This function returns the position(s) for a specified GRB or set
    of GRBs.

    Parameters
    ----------

    targetID : int or list or tuple, optional
        The name of the GRB to retrieve, or a list of names.

    GRBName : str or list or tuple, optional
        The name of the GRB to retrieve, or a list of names.

    positions: str ot list or tuple, optional:
        Which positions to retrieve, either 'all' or a list of the
        desired position types (default 'all').

    silent : bool, optional
        Whether to suppress all output (default: ``True``).

    verbose : bool, optional
        Whether to write verbose output (default: ``False``).

    Returns
    -------
    dict
        A dictionary with the light curve information as described
        above.

    """
    if verbose:
        silent = False

    targetIDs, lookup, single = _handleGRBListArgument(targetID, GRBName, silent=silent, verbose=verbose)

    ret = {}

    if isinstance(positions, str):
        if positions.lower() != "all":
            raise ValueError("Positions must be list/tuple or 'all'")
    elif not isinstance(positions, (list, tuple)):
        raise ValueError("Positions must be list/tuple or 'all'")

    sendData = {"posToGet": positions}

    for t in targetIDs:
        # We are not necessarily using the targetID as the index; what
        # do we want.
        key = lookup[t]
        if verbose:
            print(f"Getting {key}")

        # Now, first get the data:
        sendData["targetID"] = t

        tmp = base.submitAPICall("getGRBPositions", sendData, verbose=verbose)
        ret[key] = tmp

    if single:
        return ret[lookup[targetIDs[0]]]
    else:
        return ret
