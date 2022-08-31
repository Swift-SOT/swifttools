"""SXPS data access functions.

This module provides SXPS-specific functions for downloading data,
products or more information. It allows direct access, rather than
having to carry out a query first.

Provided functions:

* getSourceDetails()
* getLightCurves()
* saveLightCurves()
* getSpectra()
* saveSpectra()
* saveSourceImages()
* getUpperLimits()
* getFailedUpperLimit()
* getDatasetDetails()
* saveDatasetImages()

"""

__docformat__ = "restructedtext en"


import os
import pandas as pd
import tempfile
import subprocess
from .. import main as base
from . import download as dl


if base.HAS_ASTROPY:
    import astropy.coordinates  # noqa

LC_BINNING = {
    "observation": "Observation",
    "obs": "Observation",
    "obsid": "Observation",
    "snapshot": "Snapshot",
    "ss": "Snapshot",
    "counts": "Counts",
}

LC_TIMEFORMAT = {
    "met": "Swift MET",
    "swift met": "Swift MET",
    "mjd": "MJD",
    "tdb": "TDB",
}

UL_BOOLCOLS = (
    "IsDetected",
    "IsRetrospectiveDetection",
    "DataFromCatalogue",
    "PileupWarning",
)

UL_FLOATCOLS = ("UpperLimit", "Rate", "RatePos", "RateNeg", "Counts", "BGCounts", "CorrectionFactor")

BAND_NAMES = base.SXPS_BAND_NAMES

tableLookup = {
    "extcatmatches": "xcorr",
}

# ----------------------------------------------------------------------
# Source functions


def _handleSourceArgs(sourceID, sourceName):
    """Internal function to handle sourceID/name arguments.

    This function receives the sourceID and sourceName passed in
    a call, ensures that only one is set, and then converts the value
    into a list if necessary.

    Parameters
    ----------

    sourceID : int or None
        The sourceID specified by the user
    sourceName : str or None
        The source name specified by the user

    Returns
    -------

    varName : str
        Either 'sourceID' or 'sourceName', the name of the argument to
            send to the API call.
    varVal : list
        A list of the sourceIDs/names supplied
    single: bool
        Whether a single value, instead of a list, was supplied.

    """
    # Exactly one of sourceID and sourceName must be set, i.e. not None.
    # I don't see an exclusive-or operator in Python, but we can fake one
    # as below. a xor b; where a and b are bools, can be done as a!=b,
    # but we want to raise when this is not the case, i.e. not xor,
    # so if a==b then we have an error. a is "sourceID is None", and b is
    # "sourceName is None".
    # So the following line basically raises an error if both or neither
    # are set.
    if (sourceID is None) == (sourceName is None):
        raise ValueError("Exactly one of `sourceID` or `sourceName` must be set.")

    varName = None
    varVal = None
    single = False

    if sourceName is not None:
        varName = "sourceName"
        if isinstance(sourceName, (list, tuple)):
            varVal = sourceName
        else:
            varVal = [sourceName]
            single = True

    else:
        varName = "sourceID"
        if isinstance(sourceID, (list, tuple)):
            varVal = sourceID
        else:
            varVal = [sourceID]
            single = True

    return (varName, varVal, single)


def _transientToSource(cat, varName, varVal, skipErrors=False, silent=False, verbose=True):
    """Convert transients to sources.

    This internal function receives the parameters created by
    _handleSourceArgs and converts the identifiers/names from transient
    handles into source handles.

    Parameters
    ----------

    cat : str
        The catalogue we are working with.

    varName : str
        Either 'sourceID' or 'sourceName', the name of the argument to
            send to the API call.

    varVal : list
        A list of the sourceIDs/names supplied

    skipErrors : bool, optional
        Whether to continue if a transAsSource results in an error as
        above (default: ``False``).

    silent : bool, optional
        Whether to suppress all output (default: ``True``).

    verbose : bool, optional
        Whether to write verbose output (default: ``False``).

    Returns
    -------

    list
        The corrected ``varVal`` list.

    """
    if verbose:
        silent = False
    tmpSend = {"whichCat": cat, varName: varVal}
    tmp = base.submitAPICall("getSXPSTransAsSources", tmpSend, verbose=verbose, minKeys=("lookup",))
    tmp2 = varVal
    varVal = []
    for k in tmp2:
        k = str(k)
        if (k not in tmp["lookup"]) or (tmp["lookup"][k] == "MISSING"):
            if not silent:
                print(f"Transient `{k}` is not yet in LSXPS.")
            if not skipErrors:
                raise RuntimeError(f"Transient `{k}` is not yet in LSXPS.")
        varVal.append(tmp["lookup"][k])
    return varVal


def getSourceDetails(sourceID=None, sourceName=None, cat="LSXPS", silent=True, verbose=False, forceSingle=False):
    """Get the full set of information for an SXPS source.

    This obtains all of the information for a given SXPS source as
    displayed on the webpages. This duplicates some of the information
    in the Public_Sources table, but includes other information such
    as details of detections/non-detections, external catalogue macthes
    and so forth.

    sourceID or sourceName can be set - an error will be raised if both
    (or neither) is set - and can either be a single value, or a list.
    If a single value, then this function returns a single dict
    containing the details of the requested source. If a list, then
    the return value will be a list of dicts.

    Because LSXPS is a dynamic catalogue, source definitions can change
    and a given source can be superseded; indeed, a source can be split
    and so superseded by multiple sources (see the LSXPS documentation
    for more details). If a requested source has been superseded by a
    single newer source then the details of that newer source will be
    returned; you will be able to tell that this has happened because
    the source ID or name will not match your request. In your requested
    source has been split into multiple sources, the return dict will
    have the single key 'newerSources' which is a list of the
    superseding sources; each list entry is a dict giving basic
    information about the superseding source.

    Parameters
    ----------

    sourceID : int or list or tuple, optional
        The SXPS source ID.

    sourceName : str or list or tuple, optional
        The SXPS source IAUName.

    cat : str
        Which SXPS catalogue the source is in.

    silent : bool, optional
        Whether to suppress all output (default: ``True``).

    verbose : bool, optional
        Whether to write verbose output (default: ``False``).

    forceSingle : bool
        For internal usage. Top secret.

    Returns
    -------

    list or dict
        The source info dict, or a list of dicts if a list of sources
        was supplied.

    """
    if verbose:
        silent = False
    varName, varVal, single = _handleSourceArgs(sourceID, sourceName)

    if forceSingle:
        single = True
        if len(varVal) != 1:
            raise RuntimeError("Internal error via transAsSource. Please report this as a bug.")

    pdl1 = ("Detections", "NonDetections")
    pdl2 = ("Observations", "Stacks")
    # The argument has now been made into a list, so we can go through
    # that list and submit the request to the API.
    # We will store the results in ret
    ret = {}

    sendData = {"whichCat": cat}
    for i in varVal:
        if verbose:
            print(f"Getting data for {varName} = `{i}`")
        sendData[varName] = i
        # We can just accept this result, as the only key we have to have is "OK", and
        # if that wasn't set we will already have hit an error.
        tmp = base.submitAPICall("getSXPSSourceInfo", sendData, verbose=verbose)

        if "data" in tmp:
            ret[i] = tmp["data"]
        else:
            ret[i] = tmp

        for x in pdl1:
            if x in ret[i]:
                for y in pdl2:
                    if y in ret[i][x]:
                        ret[i][x][y] = pd.DataFrame(ret[i][x][y])
        if "CrossMatch" in ret[i]:
            ret[i]["CrossMatch"] = pd.DataFrame(ret[i]["CrossMatch"])

    if single:
        return ret[varVal[0]]
    else:
        return ret


def getLightCurves(
    sourceID=None,
    sourceName=None,
    cat="LSXPS",
    bands="all",
    binning=None,
    timeFormat=None,
    returnData=False,
    saveData=True,
    silent=True,
    verbose=False,
    transient=False,
    transAsSource=False,
    skipErrors=False,
    **kwargs,
):
    """Download a light curve, or set of light curves from SXPS.

    This will retrieve a light curve, or set of light curves, for
    object(s) in an SXPS catalogue, converting them into a
    set of pandas DataFrames.

    Some notes about what is returned, when I've worked it out.

    sourceID or sourceName can be set - an error will be raised if both
    (or neither) is set - and can either be a single value, or a list.
    If a single value, then this function returns a single dict
    containing the details of the requested source. If a list, then the
    return value will be a dict of dicts, indexed by the sourceID or
    name, whichever you supplied.

    This function can also be used to get light curves for transients,
    by setting the ``transient`` parameter to ``True``. In this case the
    ID or name supplied should be the transient identifier. Transient
    light curves are only available in the total band, with the time
    axis in MJD, and with the definitions of bins and upper limits fixed
    but with an extra binning option ('counts'). Supplied arguments that
    are not supported for transients will be ignored, and warnings will
    only appear if ``silent`` is ``False``.

    Transient sources will appear in LSXPS, with some delay, and so you
    can access the normal LSXPS light curve for a source via its
    transient identifier, by specifiying ``transAsSource=True``, however
    if the transient is not yet in LSXPS, this will return an error.

    Because LSXPS is a dynamic catalogue, source definitions can change
    and a given source can be superseded; indeed, a source can be split
    and so superseded by multiple sources (see the LSXPS documentation
    for more details). If a requested source has been superseded by a
    single newer source then the details of that newer source will be
    returned; you will be able to tell that this has happened because
    the source ID or name will not match your request. If your requested
    source has been split into multiple sources, the return dict will
    have the single key 'newerSources' which is a list of the
    superseding sources; each list entry is a dict giving basic
    information about the superseding source.

    Parameters
    ----------

    sourceID : int or list or tuple, optional
        The SXPS source ID.

    sourceName : str or list or tuple, optional
        The SXPS source IAUName.

    cat : str, optional
        Which SXPS catalogue the source is in (default: 'LSXPS').

    bands : str or list, optional
        Either 'all', or a list of labels of the energy bands to
        retrieve ('total', 'soft', 'medium', 'hard', 'HR1', 'HR2');
        (default: 'all')

    binning : str
        Which of the two binning methods you want: either
        'observation' or 'snapshot'

    timeFormat : str
        Which units to use for the time axis. Must be 'met' or 'tdb'
        or 'mjd'.

    returnData : bool, optional
        Whether to return the organised light curve data from this
        function (default: ``False``).

    saveData : bool, optional
        Whether to save the light curve data to disk (default:
        ``True``).

    transient : bool, optional
        Whether the object requested is from the LSXPS transient list,
        rather than source list (i.e. the name/ID is a transient name/
        ID) (default: ``False``).

    transAsSource : bool, optional
        Only relevant if ``transient=True``, this means that the object
        identifier supplied is a transient, but the desired light curve
        should be taken from the LSXPS data corresponding to this
        transient. If the transient is not (yet) in LSXPS then this will
        result in an error (default: ``False``).

    skipErrors : bool, optional
        Whether to continue if a transAsSource results in an error as
        above (default: ``False``).

    silent : bool, optional
        Whether to suppress all output (default: ``True``).

    verbose : bool, optional
        Whether to write verbose output (default: ``False``).

    **kwargs : dict, optional
        Any options to pass to ``saveLightCurve()`` and also extra
        options controlling your light curves, to pass to the API. These
        are:

        * showObs : bool, optional
            Whether the obsID should be included as a column.

        * hideBadPup : bool, optional
            Whether bins with the "pupWarn" flag set should be
            rejected.

        * mergeAliases : bool
            Whether to include points from sources identified as
            aliases.

        * getAllTypes : bool
            Whether to get all possible data types, and store
            as separate entities. This overrides all of the following
            arguments.

        * groupRates : bool
            Whether all detections (blind and retrospective)
            should be grouped into the same light curve entity.

        * groupULs : bool
            Whether all upper limits (non-detection, and
            retrospective only) should be grouped into the same light
            curve entity.

        * groupHRss : bool
            Whether all HRs (blind and retrospective dets)
            should be grouped into the same light curve entity.

        * retroAsUL  : bool
            Whether to return upper limits, instead of
            count-rate bins, for retrospective detections

        * nondetAsUL : bool
            Whether to return upper limits, instead of
            count-rate bins, for non detections

        * getRetroHR : bool
            Whether to include HRs from retrospective detections.


    Returns
    ------

    dict :

        If a list of sources was supplied, then the dictionary will have
        keys corresponding to the sourceID or sourceName, depending on
        which this function was called with. Each of the entries in this
        dict is itself a dict corresponding to the results for a single
        source.

        If a sourceID/name was supplied not as a list, then the dict
        returned is that containing the results for that source.

        The contents of this dict range significantly, depending on the
        details of your request. The following keys will always exist:

        * TimeFormat: Confirming which time system the time axis uses.

        * Binning: Whether observation or snapshot binning was selected.

        * Datasets: A list of the keys corresponding to the datasets
          (that is, individual light curves) returned.

        Then there is an entry per light curve *returned*. NB this may
        not match the light curves requested, as empty light curves are
        not returned.

        The names of these datasets depends upon the arguments supplied
        above, and differs for light curves and hardness ratios.

        For light curves, the general form is:

        ${band}_${what}

        ${band} is one of "total", "soft", "medium", "hard".

        ${what} is more complex, as it depends upon the "group" options
        supplied in the arguments. BY default, groupRates and groupULs
        are True, in which case ${what} will be:

        * rates -- for the count rates with 1-sigma errors *  UL    --
          for the 3-sigma upper limits.

        However if groupRates is False then instead there will be up to
        three "rates" entries for ${what}:

        * "blind_rates" - for cases where a blind detection of the
          source exists.

        * "retro_rates" - for cases where retrospective detections of
          the source exists.

        * "nondet_rates" - for cases where the source was not detected,
          blindly or retrospecitvely.

        Similarly, if groupULs is False then there will up to two "UL"
        entries for ${what}:

        * "retro_UL" - for cases where only a retrospective detection
          exists.

        * "nondet_UL" - for cases where the source was not detected,
          blindly or retrospecitvely.

        Normally, not all of these will exist, as you can specify
        whether retrospective and non-detections are reported as upper
        limits or as count-rate bins, using the retroAsUL and nondetAsUL
        arguments; by default the former is False and the latter True;
        that is, all detections (blind or retrospective) are reported as
        count-rate bins and non-detections as upper limits.

        If the parameters "getAllTypes" is set to True then both upper
        limits AND count-rate bins will be produced for the
        retrospective and non-detections, and all no grouping is
        applied.

        Note that blind detections are always reported with count-rate
        bins.

    """
    if verbose:
        silent = False

    varName, varVal, single = _handleSourceArgs(sourceID, sourceName)

    # Now handle the other arguments.
    if transient and not transAsSource:
        if not silent:
            if len(kwargs) > 0:
                print("WARNING: kwargs are ignored for transient light curves")
            if (bands is not None) and (bands.lower() != "all"):
                print("WARNING: 'bands' is ignored for transient light curves")
            if (timeFormat is not None) and (timeFormat.lower() != "mjd"):
                print("WARNING: 'timeFormat' is ignored for transient light curves")

    sendData = {
        "whichCat": cat,
        "bands": bands,
        "binning": binning,
        "timeFormat": timeFormat,
    }

    if transient and not transAsSource:
        sendData["transient"] = True

    # May need to convert transientIDs into sourceIDs
    if transient and transAsSource:
        varVal = _transientToSource(cat, varName, varVal, skipErrors=skipErrors, silent=silent, verbose=verbose)

    # And there are other things that may have been set in kwargs.
    # These are all bools. Start with the universal ones, and getAllTypes
    if transAsSource or not transient:
        tmp = ("showObs", "hideBadPup", "mergeAliases", "getAllTypes")
        for t in tmp:
            if t in kwargs.keys():
                if not isinstance(kwargs[t], bool):
                    raise RuntimeError(f"`{t}` should be boolean")
                sendData[t] = kwargs[t]

        # Now the grouping and retrieval things.
        getAll = False
        if "getAllTypes" in sendData:
            getAll = sendData["getAllTypes"]

        # Now handle all the grouping things
        tmp = (
            "groupRates",
            "groupULs",
            "groupHRss",
            "retroAsUL",
            "nondetAsUL",
            "getRetroHR",
        )
        for t in tmp:
            if t in kwargs:
                if getAll:
                    if not silent:
                        print(f"WARNING: Ignoring parameter {t} as getAllTypes = True")
                    continue
                if not isinstance(kwargs[t], bool):
                    raise RuntimeError(f"`{t}` should be boolean")
                sendData[t] = kwargs[t]

    # If we had a list, then we will return a dict, where each API result
    # is an entry, and the supplied keys (IDs or names) are the dict keys.
    # If only a single value was supplied, we will return only the first
    # entry from this.
    # NOTE: A list with a single entry is returned as a dict with a single
    # entry.

    binLookup = {"obslc": "Observation", "sslc": "Snapshot", "counts": "Counts"}
    ret = {}

    for i in varVal:
        if verbose:
            print(f"Getting data for {varName} = `{i}`")
        sendData[varName] = i

        # We can just accept this result, as the only key we have to have is "OK", and
        # if that wasn't set we will already have hit an error.
        tmp = base.submitAPICall("getSXPSLC", sendData, verbose=verbose)

        if tmp["Binning"] in binLookup:
            tmp["Binning"] = binLookup[tmp["Binning"]]

        if "Datasets" in tmp:
            ret[i] = dl._handleLightCurve(tmp, silent, verbose)
        else:
            ret[i] = tmp

    if saveData:
        d = ret
        if single:
            d = ret[varVal[0]]
        saveLightCurves(d, silent=silent, verbose=verbose, **kwargs)

    if returnData:
        if single:
            return ret[varVal[0]]
        else:
            return ret


def saveLightCurves(
    data,
    destDir="lc",
    whichSources="all",
    subDirs=True,
    **kwargs,
):
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

    whichSources : list or str, optional
        A list of the sources to save. Should be keys of the data
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
    if (whichSources is None) or (whichSources == "all"):
        whichSources = data.keys()

    # For SXPS objects we add the time or binning to the extension unless the user says no
    if "timeFormatInFname" not in kwargs:
        kwargs["timeFormatInFname"] = True
    if "binningInFname" not in kwargs:
        kwargs["binningInFname"] = True

    # prefix should not be in this dict, so remove if it is.
    kwargs.pop("prefix", None)

    # Now start saving light curves, one source at a time
    for source in whichSources:
        if source not in data:
            raise ValueError(f"{source} is not in the light curve list.")

        if "newerSources" in data[source]:
            if not silent:
                print(f"Skipping source {source} as is has been superseded by multiple sources.")
            continue

        path = destDir
        prefix = ""
        if subDirs:
            path = f"{destDir}/{source}"
        elif usePrefix:
            prefix = f"{source}_"

        dl._saveLightCurveFromDict(data[source], destDir=path, prefix=prefix, **kwargs)


def getSpectra(
    sourceID=None,
    sourceName=None,
    cat="LSXPS",
    returnData=False,
    saveData=True,
    transient=False,
    transAsSource=False,
    specType=None,
    skipErrors=False,
    silent=True,
    verbose=False,
    **kwargs,
):
    """Download a spectrum, or set of spectra from SXPS.

    This will retrieve the information about a spectral fit for
    object(s) in an SXPS catalogue, returning a dictionary of the
    details, which also includes the URL of a tar file containing the
    actual spectrum data, and URLs of gif images of the fitted spectra.

    sourceID or sourceName can be set - an error will be raised if both
    (or neither) is set - and can either be a single value, or a list.
    If a single value, then this function returns a single dict
    containing the details of the requested source. If a list, then the
    return value will be a list of dicts.

    This function can also be used to get spectra for transients,
    by setting the ``transient`` parameter to ``True``. In this case the
    ID or name supplied should be the transient identifier. In this case
    you must also suppled the ``specType`` parameter to specify which
    of the two transient spectra you want to retrieve.

    Transient sources will appear in LSXPS, with some delay, and so you
    can access the normal LSXPS light curve for a source via its
    transient identifier, by specifiying ``transAsSource=True``, however
    if the transient is not yet in LSXPS, this will return an error.

    Because LSXPS is a dynamic catalogue, source definitions can change
    and a given source can be superseded; indeed, a source can be split
    and so superseded by multiple sources (see the LSXPS documentation
    for more details). If a requested source has been superseded by a
    single newer source then the details of that newer source will be
    returned; you will be able to tell that this has happened because
    the source ID or name will not match your request. If your requested
    source has been split into multiple sources, the return dict will
    have the single key 'newerSources' which is a list of the
    superseding sources; each list entry is a dict giving basic
    information about the superseding source.

    Parameters
    ----------

    sourceID : int or list or tuple
        The SXPS source ID.

    sourceName : str or list or tuple
        The SXPS source IAUName.

    cat : str
        Which SXPS catalogue the source is in.

    returnData : bool, optional
        Whether to return the organised light curve data from this
        function (default: ``False``).

    saveData : bool, optional
        Whether to save the light curve data to disk (default:
        ``True``).

    transient : str, optional
        Whether the object requested is from the LSXPS transient list,
        rather than source list (i.e. the name/ID is a transient name/
        ID) (default: ``False``).

    transAsSource : bool, optional
        Only relevant if ``transient=True``, this means that the object
        identifier supplied is a transient, but the desired light curve
        should be taken from the LSXPS data corresponding to this
        transient. If the transient is not (yet) in LSXPS then this will
        result in an error (default: ``False``).

    specType : str, optional
        Required if ``transient`` is ``True``, and ``transAsSource`` is
        ``False``, this specifies whether to get the spectrum created
        only from the discovery dataset (set to 'discovery') or that
        made from all data since discovery ('full'). If it is 'both'
        then the returned ``dict`` has keys 'Discovery' and 'Full'
        containing the respective spectra.

    skipErrors : bool, optional
        Whether to continue if a transAsSource results in an error as
        above (default: ``False``).

    silent : bool, optional
        Whether to suppress all output (default: ``True``).

    verbose : bool, optional
        Whether to write verbose output (default: ``False``).

    **kwargs : dict, optional
        Any arguments to pass to ``saveSpectra()``

    Returns
    ------

    dict

        An API-standard spectrum dict.

    """
    if verbose:
        silent = False

    varName, varVal, single = _handleSourceArgs(sourceID, sourceName)

    # Now handle the other arguments.

    # Now handle the other arguments.

    sendData = {"whichCat": cat}
    if transient and not transAsSource:
        sendData["transient"] = True

    # May need to convert transientIDs into sourceIDs
    if transient:
        if transAsSource:
            varVal = _transientToSource(cat, varName, varVal, skipErrors=skipErrors, silent=silent, verbose=verbose)
        else:
            if specType is None:
                raise RuntimeError("`specType` must be set when getting a transient spectrum.")
            else:
                sendData["specType"] = specType

    ret = {}
    for i in varVal:
        if verbose:
            print(f"Getting data for {varName} = `{i}`")
        sendData[varName] = i

        # We can just accept this result, as the only key we have to have is "OK", and
        # if that wasn't set we will already have hit an error.
        ret[i] = base.submitAPICall("getSXPSSpectrumData", sendData, verbose=verbose)

    if saveData:
        saveAsTrans = transient and not transAsSource and specType.lower() == "both"
        d = ret
        if single:
            d = ret[varVal[0]]
        saveSpectra(d, silent=silent, verbose=verbose, transient=saveAsTrans, **kwargs)

    if returnData:
        if single:
            return ret[varVal[0]]
        else:
            return ret


def saveSpectra(data, destDir="spec", whichSources=None, transient=False, silent=True, verbose=False, **kwargs):
    """Save the spectral data to disk.

    This will download and save the spectral files from a previous
    ``getSpectra()`` call.

    Parameters
    ----------

    data : dict
        The object returned by ``getSXPSSpectra()``

    destDir : str, optional
        The directory in which to save the spectra (default: "spec").

    whichSources : list
        A list of the sources to save. Should be keys of the data
        object.

    transient : bool, optional
        Whether the spectra are transient spectra (default: ``True``).

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
    if (whichSources is None) or (whichSources == "all"):
        whichSources = data.keys()

    # Now start saving spectra, one source at a time
    for source in whichSources:
        if source not in data:
            raise ValueError(f"{source} is not in the spectra available.")
        if "NoSpectrum" in data[source]:
            if not silent:
                print(f"Source `{source}` has no spectra.")
            continue

        if "newerSources" in data[source]:
            if not silent:
                print(f"Skipping source {source} as is has been superseded by multiple sources.")
            continue

        path = destDir
        if not single:
            path = f"{destDir}/{source}"
            base._createDir(path, silent=silent, verbose=verbose)

        print(f"Transient {transient}")
        if transient:
            for i in ("Full", "Discovery"):
                if i in data[source]:
                    if "NoSpectrum" in data[source][i]:
                        if not silent:
                            print(f"Source `{source}` has no `{i}` spectrum.")
                        continue
                    else:
                        fpath = f"{path}/{i}"
                        base._createDir(fpath, silent=silent, verbose=verbose)
                        dl._saveSpectrum(data[source][i], destDir=fpath, silent=silent, verbose=verbose, **kwargs)
        else:
            dl._saveSpectrum(data[source], destDir=path, silent=silent, verbose=verbose, **kwargs)


def saveSourceImages(
    sourceID=None,
    sourceName=None,
    cat="LSXPS",
    bands="all",
    destDir="images",
    subDirs=True,
    clobber=False,
    skipErrors=False,
    transient=False,
    transAsSource=False,
    silent=True,
    verbose=False,
):
    """Download the thumbnail images of the sources.

    This will retrieve and save thumbnail images of the specified
    object(s) in an SXPS catalogue.

    sourceID or sourceName can be set - an error will be raised if both
    (or neither) is set - and can either be a single value, or a list.

    Because LSXPS is a dynamic catalogue, source definitions can change
    and a given source can be superseded; indeed, a source can be split
    and so superseded by multiple sources (see the LSXPS documentation
    for more details). If a requested source has been superseded by a
    single newer source then the details of that newer source will be
    returned; you will be able to tell that this has happened because
    the source ID or name will not match your request. If your requested
    source has been split into multiple sources, the return dict will
    have the single key 'newerSources' which is a list of the
    superseding sources; each list entry is a dict giving basic
    information about the superseding source.

    Parameters
    ----------

    BLAH

    cat : str
        Which SXPS cat the source is in.

    bands : str or list, optional
        Which bands' images to retrieve. As well as the normal SXPS
        bands, this can include 'Expmap' to get the exposure map image
        (default: 'all').

    subDirs : bool, optional
        Whether to save each dataset's data into its own subdirectory
        (default: ``True``).

    clobber : bool
        Whether to overwrite files if they exist.

    skipErrors : bool, optional
        If an error occurs saving a file, do not raise a RuntimeError
        but simply continue to the next file (default ``False``).

    transient : str, optional
        Whether the object requested is from the LSXPS transient list,
        rather than source list (i.e. the name/ID is a transient name/
        ID) (default: ``False``).

    transAsSource : bool, optional
        Only relevant if ``transient=True``, this means that the object
        identifier supplied is a transient, but the desired light curve
        should be taken from the LSXPS data corresponding to this
        transient. If the transient is not (yet) in LSXPS then this will
        result in an error (default: ``False``).

    silent : bool, optional
        Whether to suppress all output (default: ``True``).

    verbose : bool, optional
        Whether to write verbose output (default: ``False``).

    """
    if verbose:
        silent = False

    varName, varVal, single = _handleSourceArgs(sourceID, sourceName)

    sendData = {"whichCat": cat, "bands": bands}

    if transient and not transAsSource:
        sendData["transient"] = True

    # May need to convert transientIDs into sourceIDs
    if transient and transAsSource:
        varVal = _transientToSource(cat, varName, varVal, skipErrors=skipErrors, silent=silent, verbose=verbose)

    # Create the output dir, if needed.
    base._createDir(destDir, silent=silent, verbose=verbose)
    for i in varVal:
        if verbose:
            print(f"Getting images for {varName} = `{i}`")
        sendData[varName] = i

        # We can just accept this result, as the only key we have to have is "OK", and
        # if that wasn't set we will already have hit an error.
        tmp = base.submitAPICall("getSXPSSourceImages", sendData, verbose=verbose)

        path = destDir
        prefix = None
        if subDirs:
            path = f"{path}/{i}"
            base._createDir(path, silent=silent, verbose=verbose)
        else:
            prefix = f"{i}_"
        for b in BAND_NAMES:
            if b in tmp:
                url = tmp[b]
                if (url == "NOTFOUND") and (not silent):
                    print(f"No image exists for the {b} band for `{i}`.")
                else:
                    ok = dl._saveURLToFile(
                        url,
                        path,
                        name=f"{b}.png",
                        prefix=prefix,
                        clobber=clobber,
                        silent=silent,
                        verbose=verbose,
                    )
                    if not ok:
                        if skipErrors:
                            continue
                        raise RuntimeError(f"Failed to save {url} to {path}/")
        if "Expmap" in tmp:
            url = tmp["Expmap"]
            if (url == "NOTFOUND") and (not silent):
                print(f"No exposure map image exists for `{i}`.")
            else:
                ok = dl._saveURLToFile(
                    url,
                    path,
                    name="Expmap.png",
                    prefix=prefix,
                    clobber=clobber,
                    silent=silent,
                    verbose=verbose,
                )
                if not ok:
                    if skipErrors:
                        continue
                    raise RuntimeError(f"Failed to save {url} to {path}/")


# ----------------------------------------------------------------------
# Transient functions


def getTransientDetails(
    sourceID=None, sourceName=None, cat="LSXPS", transAsSource=False, skipErrors=False, silent=True, verbose=False
):
    """Get the full set of information for an SXPS transient.

    This obtains all of the information for a given SXPS transient as
    displayed on the webpages. This duplicates some of the information
    in the Public_Transients table, but includes other information.

    sourceID or sourceName can be set - an error will be raised if both
    (or neither) is set - and can either be a single value, or a list.
    If a single value, then this function returns a single dict
    containing the details of the requested source. If a list, then
    the return value will be a list of dicts.

    Parameters
    ----------

    sourceID : int or list or tuple, optional
        The SXPS source ID.

    sourceName : str or list or tuple, optional
        The SXPS source IAUName.

    cat : str
        Which SXPS catalogue the source is in.

    transAsSource : bool, optional
        If set, then this will convert the transientID to a sourceID
        (if possible) and then call getSourceDetails instead.

    skipErrors : bool, optional
        Whether to continue if converting to sourceID results in an
        error (default: ``False``).

    silent : bool, optional
        Whether to suppress all output (default: ``True``).

    verbose : bool, optional
        Whether to write verbose output (default: ``False``).

    Returns
    -------

    list or dict
        The source info dict, or a list of dicts if a list of sources
        was supplied.

    """
    if verbose:
        silent = False

    varName, varVal, single = _handleSourceArgs(sourceID, sourceName)
    if transAsSource:
        varVal = _transientToSource(cat, varName, varVal, skipErrors=skipErrors, silent=silent, verbose=verbose)
        args = {varName: varVal, "cat": cat, "silent": silent, "verbose": verbose, "forceSingle": single}
        return getSourceDetails(**args)

    ret = {}

    sendData = {"whichCat": cat}
    for i in varVal:
        if verbose:
            print(f"Getting data for {varName} = `{i}`")
        sendData[varName] = i
        # We can just accept this result, as the only key we have to have is "OK", and
        # if that wasn't set we will already have hit an error.
        tmp = base.submitAPICall("getSXPSTransInfo", sendData, verbose=verbose)
        ret[i] = tmp

    if single:
        return ret[varVal[0]]
    else:
        return ret


# ----------------------------------------------------------------------
# Upper limit functions


def getUpperLimits(
    position=None,
    name=None,
    RA=None,
    Dec=None,
    cat="LSXPS",
    bands=("total",),
    whichData="deepest",
    timeFormat="cal",
    sigma=3.0,
    detectionsAsRates=False,
    detThresh=None,
    skipDetections=False,
    useCatValues=False,
    pandas=True,
    silent=True,
    verbose=False,
):
    """Find upper limit(s) for a specified object/position.

    This function returns flux information for a specific location on
    the sky. Its default use is to provide a single, 0.3-10 keV upper
    limit corresponding to the deepest observation available, however
    there is significant flexibility in what you can request, as
    demonstrated by the arguments below.

    You must supply 'position', 'name' or both 'RA' & 'Dec', but only
    one of these (e.g. you cannot give a 'position' and RA/Dec).

    Parameters
    ----------

    position : str, optional
        A string to be parsed as a free-form RA/Dec position.

    name : str, optional
        A name to be resolved into coordinates

    RA : float or astropy.coordinates.Angle, optional
        The RA at which to calculate the upper limit(s).

    Dec : float or astropy.coordinates.Angle, optional
        The declination at which to calculate the upper limit(s).

    cat : str
        Which SXPS catalogue the source is in.

    bands : str or list, optional
        Either 'all', or a list of labels of the energy bands to
        retrieve ('total', 'soft', 'medium', 'hard')
        (default: ['total']).

    whichData : str, optional
        Which datasets to use for the flux measurement, either:
        'deepest' or 'all' (default: 'deepest').

    timeFormat : str, optional
       What format/system to use for the timestamps, either: 'cal',
       'met', 'mjd', 'tdb' (default: 'cal').

    sigma : float, optional
        The confidence level for upper limits, in Gaussian sigmas
        (default: 3).

    detectionsAsRates : bool, optional
        Supply count-rate (and 1-sigma errors) in cases that the source
        is deemed 'detected' (that is, the n-sigma lower-limit is >0;
        where n is set by the detThresh parameter) (default: ``False``).

    detThresh : float, optional
        The significance level to be used for deciding if a flux
        measurement corresponds to a detection or not. If ``None``, this
        will default to sigma (default: ``None``).

    skipDetections : bool, optional
        Skip datasets in which a source is detected at / close to the
        position specified (default: ``False``).

    useCatValues : bool, optional
        If, in a given dataset, the source is in the catalogue in any
        band, then return the values from the catalogue instead of
        recalculating them (default, ``False``).

    pandas : bool, optional
        Whether to convert the result to a pandas DataFrame
        (default: ``True``).

    silent : bool, optional
        Whether to suppress all output (default ``True``).

    verbose : bool, optional
        Whether to write verbose output (default ``False``).

    Return
    ------

    dict
        This returns a dict, with the following keys (note, not all
        keys will always be present).

        * ``ULData`` - the upper limit data
        * ``DetData`` - Details of SXPS sources near the input position.
        * ``Columns`` - The list of columns returned in ULData (not
            present if ``pandas`` is ``True``).

        If you supplied the ``position`` or ``name`` argument then the
        following (standard) keys will also be present:

        * ``ResolvedRA`` The RA (decimal degrees) actually used.
        * ``ResolvedDec`` The dec (decimal degrees) actually used.
        * ``ResolvedInfo`` Text information about the coordinates.

        If the job timed out, the key ``TIMEOUT`` will be present, with
        a unique identifier that can be used to call
        ``getFailedUpperLimit()``.

        ``DetData`` will only be present if the position you requested
        is close to a source in the catalogue searched, and thus may
        serve as a warning. This will be a list, one entry per matching
        source, with keys ``Distance`` and ``SourceName``. The latter is
        self-explanatory, the former is the distance (arcsec) between
        your input position, and the source.

        ``ULData`` is the main data returned, giving the flux
        measurements your query returned. The exact contents of this
        depend both on what arguments you provided, and the values
        found when calculating the upper limits. By default, this object
        is a pandas ``DataFrame``, with one row per dataset for which
        results were obtained. If you set ``pandas=False`` then it will
        be a list (one entry per dataset) with each entry being a
        ``dict``.

        The possible keys/columns that will be in this ``ULData`` object
        are below. **Note** For brevity, only the total band entries
        are given, but for everything starting ``Total_`` there may also
        be ``Soft_``, ``Medium_`` and ``Hard_`` if you requested those
        bands.

        * ``StartTime`` - The start time of the dataset, in your
            requested format.
        * ``StopTime`` - The end time of the dataset, in your
            requested format.
        * ``ObsID`` - The observation identifier.
        * ``SourceExposure`` - The exposure (in s) at the source
            position.
        * ``ImageExposure`` - The on-axis exposure (in s) of the
            dataset.
        * ``Total_UpperLimit`` - The upper limit in the total band.
        * ``Total_Rate`` - The count rate in the total band.
        * ``Total_RatePos`` - The 1-sigma positive error on the count
            rate in the total band.
        * ``Total_RateNeg``- The 1-sigma negative error on the count
            rate in the total band.
        * ``Total_Counts`` - The measured counts in the extraction
            region in the total band.
        * ``Total_BGCounts`` - The predicted background counts in the
            extraction region in the total band.
        * ``Total_CorrectionFactor`` - The count-rate correction factor
            (correcting for vignetting, bad columns, etc) in the total
            band.
        * ``Total_IsDetected`` - Whether there was a blind detection of
            a source at your requested position in this dataset in the
            total band.
        * ``Total_IsRetrospectiveDetection`` - Whether your input
            position corresponds to an SXPS source for which there is
            a retrospective detection in this dataset in the total band.
        * ``Total_DataFromCatalogue`` - Whether these total-band data
            were taken from the catalogue, rather than being calculated
            afresh.
        * ``Total_PileupWarning`` - Whether the total-band data have
            a warning flag indicating that the pile up correction (and
            hence count-rate values) may be wrong.

    """
    if verbose:
        silent = False

    # Handle the arguments. Do not need to sanity check all arguments,
    # as this can be done by the back end and it makes sense to do it
    # just once, but we do need to handle a few things. First, put most
    # of the options into the dict to send:
    sendData = {
        "catalogue": cat,
        "bands": bands,
        "whichData": whichData,
        "timeFormat": timeFormat,
        "sigma": sigma,
        "detectionsAsRates": detectionsAsRates,
        "skipDetections": skipDetections,
        "useCatValues": useCatValues,
    }

    # 1) Do we have name, coordinates, or position?
    gotPosData = False
    if position is not None:
        sendData["searchName"] = position
        gotPosData = True
    if name is not None:
        if gotPosData:
            raise RuntimeError("You can supply position OR name, not both.")
        sendData["searchName"] = name
        gotPosData = True
    if (RA is not None) and (Dec is not None):
        if gotPosData:
            raise RuntimeError("You can supply position/name, or RA & Dec not both.")
        if isinstance(RA, astropy.coordinates.Angle):
            RA = float(RA.deg)
        elif isinstance(RA, str):
            tmp = astropy.coordinates.Angle(RA)
            RA = float(tmp.deg)
        if isinstance(Dec, astropy.coordinates.Angle):
            Dec = float(Dec.deg)
        elif isinstance(Dec, str):
            tmp = astropy.coordinates.Angle(Dec)
            Dec = float(tmp.deg)
        sendData["RA"] = RA
        sendData["Dec"] = Dec

    # 2) detThresh:
    if detThresh is None:
        detThresh = sigma

    if not silent:
        print("Submitting upper limit request; this may take a few moments.")
    tmp = base.submitAPICall("getSXPSUL", sendData, verbose=verbose)

    if verbose:
        print("Upper limit retrieved.")

    if pandas:
        _handleUL(tmp)
        tmp.pop("Columns", None)
    tmp.pop("OK", None)

    if ("TIMEOUT" in tmp) and (not silent):
        print("The upper limit calculation timed out.")
    return tmp


def getFailedUpperLimit(id, pandas=True, silent=True, verbose=False):
    """Try to get an upper limit that timed out.

    Upper limit requests called by ``getUpperLimits()`` can time out,
    in which case the dict returned by that function will contain the
    key ``TIMEOUT`` with a unique identifier as the value. It may be
    that the upper limit job still completed, but after the back-end
    timeout was hit. This function allows to to retrieve an upper limit
    in that event.

    **NOTES**

    1. Upper limit jobs are only allocated a short maximum runtime on
        the server, thus some jobs may timeout and never complete. This
        timeout is a server setting and subject to change, so cannot be
        documented here, but as a general rule, if it has been more than
        20 minutes and you still get timeout warnings, your job has
        probably been killed.

    2. When upper limit data are retrieved, by this function or by
        ``getUpperLimits()``, the files are deleted off the server, i.e.
        they can only be downloaded successfully once.

    If ``getUpperLimits()`` returned a timeout, then you can wait a
    short time and then call this function, passing as its argument the
    id string returned in the ``TIMEOUT`` key of the original request.
    This will either return another TIMEOUT warning, or the requested
    upper limit.

    Parameters
    ----------

    id : str
        The identification string for your timed out upper limit.

    pandas : bool, optional
        Whether to convert the result to a pandas DataFrame
        (default: ``True``).

    silent : bool, optional
        Whether to suppress all output (default ``True``).

    verbose : bool, optional
        Whether to write verbose output (default ``False``)..

    """
    if verbose:
        silent = False

    if not isinstance(id, str):
        raise ValueError("`id` must be a string.")

    sendData = {
        "ULID": id,
    }

    tmp = base.submitAPICall("getSXPSUL", sendData, verbose=verbose)
    if pandas:
        _handleUL(tmp)

    tmp.pop("OK", None)

    if ("TIMEOUT" in tmp) and (not silent):
        print("The upper limit calculation timed out.")
    return tmp


def _handleUL(data):
    """Internal function to convert UL data to pandas"""

    if "ULData" in data:
        data["ULData"] = pd.DataFrame(data["ULData"], columns=data["Columns"])
        for c in ("SourceExposure", "ImageExposure"):
            if c in data["Columns"]:
                data["ULData"][c] = data["ULData"][c].apply(lambda x: float(x))
        for b in BAND_NAMES:
            for col in UL_BOOLCOLS:
                c = f"{b}_{col}"
                if c in data["Columns"]:
                    data["ULData"][c] = data["ULData"][c].apply(lambda x: bool(x))
            for col in UL_FLOATCOLS:
                c = f"{b}_{col}"
                if c in data["Columns"]:
                    data["ULData"][c] = data["ULData"][c].apply(lambda x: float(x))

    if "DetData" in data:
        data["DetData"] = pd.DataFrame(data["DetData"])


# ----------------------------------------------------------------------
# Dataset functions


def _handleDSArgs(DatasetID, ObsID):
    """Internal function to handle DatasetID/ObsID arguments.

    This function receives the DatasetID and ObsID passed in
    a call, ensures that only one is set, and then converts the value
    into a list if necessary.

    Parameters
    ----------

    DatasetID : int or None
        The DatasetID specified by the user
    ObsID : int or None
        The ObsID specified by the user

    Returns
    -------

    varName : str
        Either 'DatasetID' or 'ObsID', the name of the argument to
            send to the API call.
    varVal : list
        A list of the Dataset/Obs IDs supplied
    single: bool
        Whether a single value, instead of a list, was supplied.

    """
    if (DatasetID is None) == (ObsID is None):
        raise ValueError("Exactly one of `DatasetID` or `ObsID` must be set.")

    varName = None
    varVal = None
    single = False

    if ObsID is not None:
        varName = "ObsID"
        if isinstance(ObsID, (list, tuple)):
            varVal = ObsID
        else:
            varVal = [ObsID]
            single = True

    else:
        varName = "DatasetID"
        if isinstance(DatasetID, (list, tuple)):
            varVal = DatasetID
        else:
            varVal = [DatasetID]
            single = True

    return (varName, varVal, single)


def getDatasetDetails(DatasetID=None, ObsID=None, cat="LSXPS", silent=True, verbose=False):
    """Get the full set of information for an SXPS dataset.

    This obtains all of the information for a given SXPS dataset as
    displayed on the webpages. This duplicates some of the information
    in the Public_Datasets table, but includes other information such
    as details of the objects detected in that dataset etc.

    DatasetID or ObsID can be set - an error will be raised if both
    (or neither) is set - and can either be a single value, or a list.
    If a single value, then this function returns a single dict
    containing the details of the requested dataset. If a list, then
    the return value will be a list of dicts.

    Will add some notes here about superseded stacks later, when stacks
    are done.

    NOTE: May end up with DatasetID being for LSXPS only.

    Parameters
    ----------

    DatasetID : int or list or tuple, optional
        The SXPS dataset ID.

    ObsID : str or int or list or tuple, optional
        The Swift ObsID

    cat : str
        Which SXPS catalogue the source is in.

    silent : bool, optional
        Whether to suppress all output (default: ``True``).

    verbose : bool, optional
        Whether to write verbose output (default: ``False``).

    Returns
    -------

    list or dict
        The source info dict, or a list of dicts if a list of sources
        was supplied.

    """
    if verbose:
        silent = False

    varName, varVal, single = _handleDSArgs(DatasetID, ObsID)

    # The argument has now been made into a list, so we can go through
    # that list and submit the request to the API.
    # We will store the results in ret
    ret = {}

    sendData = {"whichCat": cat}
    for i in varVal:
        if verbose:
            print(f"Getting data for {varName} = `{i}`")
        sendData[varName] = i
        # We can just accept this result, as the only key we have to have is "OK", and
        # if that wasn't set we will already have hit an error.
        tmp = base.submitAPICall("getSXPSDatasetInfo", sendData, verbose=verbose)
        j = i
        if varName == "ObsID":
            if not single and isinstance(i, int):
                j = f"{i:011d}"
        if "data" in tmp:
            ret[j] = tmp["data"]
            # panda-ise the sources tables?
        else:
            ret[j] = tmp

        if "Sources" in ret[j]:
            ret[j]["Sources"] = pd.DataFrame(ret[j]["Sources"])

        # for b in BAND_NAMES:
        #     k = f"{b}_sources"
        #     if k in ret[j]:
        #         ret[j][k] = pd.DataFrame(ret[j][k])

    if single:
        return ret[varVal[0]]
    else:
        return ret


def saveDatasetImages(
    DatasetID=None,
    ObsID=None,
    cat="LSXPS",
    bands="all",
    types="all",
    getRegions=False,
    destDir="images",
    subDirs=True,
    clobber=False,
    skipErrors=False,
    silent=True,
    verbose=False,
):
    """Get the full set of information for an SXPS dataset.

    This obtains all of the information for a given SXPS dataset as
    displayed on the webpages. This duplicates some of the information
    in the Public_Datasets table, but includes other information such
    as details of the objects detected in that dataset etc.

    DatasetID or ObsID can be set - an error will be raised if both
    (or neither) is set - and can either be a single value, or a list.
    If a single value, then this function returns a single dict
    containing the details of the requested dataset. If a list, then
    the return value will be a list of dicts.

    Will add some notes here about superseded stacks later, when stacks
    are done.

    NOTE: May end up with DatasetID being for LSXPS only.

    Parameters
    ----------

    DatasetID : int or list or tuple, optional
        The SXPS dataset ID.

    ObsID : str or int or list or tuple, optional
        The Swift ObsID

    cat : str
        Which SXPS catalogue the source is in.

    bands : str or list, optional
        Bands (default: 'all').

    types : str or list, optional
        Types (default: 'all').

    getRegions : bool, optional
        Whether to get ds9 region files for the sources in the image
        as well (default: ``False``).

    subDirs : bool, optional
        Whether to save each dataset's data into its own subdirectory
        (default: ``True``).

    clobber : bool
        Whether to overwrite files if they exist.

    skipErrors : bool, optional
        If an error occurs saving a file, do not raise a RuntimeError
        but simply continue to the next file (default ``False``).

    silent : bool, optional
        Whether to suppress all output (default: ``True``).

    verbose : bool, optional
        Whether to write verbose output (default: ``False``).

    Returns
    -------

    list or dict
        The source info dict, or a list of dicts if a list of sources
        was supplied.

    """
    if verbose:
        silent = False

    varName, varVal, single = _handleDSArgs(DatasetID, ObsID)

    # The argument has now been made into a list, so we can go through
    # that list and submit the request to the API.
    # We will store the results in ret

    base._createDir(destDir, silent=silent, verbose=verbose)

    sendData = {"whichCat": cat, "bands": bands, "types": types, "getRegions": getRegions}

    for i in varVal:
        if verbose:
            print(f"Getting data for {varName} = `{i}`")
        sendData[varName] = i
        # We can just accept this result, as the only key we have to have is "OK", and
        # if that wasn't set we will already have hit an error.
        tmp = base.submitAPICall("getSXPSDatasetImages", sendData, verbose=verbose)
        if 'SupersededBy' in tmp:
            print("\n ** WARNING: This dataset is an obsolete stack ** \n")
        path = destDir
        if subDirs:
            j = i
            if varName == "ObsID" and isinstance(i, int):
                j = f"{i:011d}"
            path = f"{path}/{j}"
            base._createDir(path, silent=silent, verbose=verbose)

        for b in BAND_NAMES:
            if b in tmp:
                for t in tmp[b]:
                    url = tmp[b][t]
                    if (url == "NOTFOUND") and (not silent):
                        print(f"No {t} image exists for the {b} band for `{i}`.")
                    else:
                        ok = dl._saveURLToFile(url, path, clobber=clobber, silent=silent, verbose=verbose)
                        if not ok:
                            if skipErrors:
                                continue
                            raise RuntimeError(f"Failed to save {url} to {path}/")
        if "Expmap" in tmp:
            url = tmp["Expmap"]
            if (url == "NOTFOUND") and (not silent):
                print(f"No exposure map image exists for `{i}`.")
            else:
                ok = dl._saveURLToFile(url, path, clobber=clobber, silent=silent, verbose=verbose)
                if not ok:
                    if skipErrors:
                        continue
                    raise RuntimeError(f"Failed to save {url} to {path}/")


# ----------------------------------------------------------------------
# Catalogue table functions


def listOldTables(silent=True, verbose=False):
    """Get the list of old tables.

    This returns details of old snapshot versions of the database tables
    that exist.

    Paramters
    ---------

    silent : bool, optional
        Whether to suppress all output (default: ``True``).

    verbose : bool, optional
        Whether to write verbose output (default: ``False``).

    Returns
    -------

    dict
        A ``dict`` with keys 'hourly' and 'daily'. These are themselves
        ``dicts``s with keys of epochs for which snapshots exists,
        and those then contain the tables that exist for those
        snapshots.

    """
    if verbose:
        silent = False
    sendData = {}
    tmp = base.submitAPICall("getOldSXPSTables", sendData, verbose=verbose, minKeys=("hourly", "daily"))
    return tmp


def getFullTable(
    cat="LSXPS",
    table=None,
    subset=None,
    epoch=None,
    format="csv",
    destDir=None,
    saveData=True,
    returnData=False,
    clobber=False,
    silent=True,
    verbose=False,
):
    """Get the full catalogue data for a given table.

    This allows you to access the entire catalogue in one go. This
    will download the .csv file for the table you requested and read it
    into a pandas ``DataFrame`` which will be returned, and then the
    file will be deleted. You can change this behaviour to keep the file
    and/or to not return a ``DataFrame``.

    Parameters
    ----------

    cat : str, optional
        Which SXPS catalogue to download (default: 'LSXPS').

    table : str
        The database table to download.

    subset : str, optional
        Some tables have subsets you can select, e.g. the 'clean' set of
        Public_Sources. You can specify that subset using this parameter
        or, if this is not supplied, the default subset will be obtained.

    epoch : str, optional
        If supplied, gets an older version of the table from the
        specified epoch (default: ``None``).

    format : str
        The format to download the file. Can be 'csv' or 'fits'.
        NOTE: if ``returnData`` is ``True`` this must be csv (default:
        'csv').

    destDir : str, optional
        The directory to save the file in. If not specified, a temporary
        file will be used.

    saveData : bool, optional
        Whether to keep the csv file (default ``True``).

    returnData : bool, optional
        Whether to return a ``DataFrame`` (default ``False``).

    clobber : bool, optional
        Whether to overwrite the file if it exists. Only matters if
        ``destDir`` is set (default: ``False``).

    silent : bool, optional
        Whether to suppress all output (default: ``True``).

    verbose : bool, optional
        Whether to write verbose output (default: ``False``).

    Returns
    -------

    pandas.DataFrame, optional
        If ``returnData`` was ``True`` then this contains the downloaded
        data.

    """
    if verbose:
        silent = False

    if (table is None) or not isinstance(table, str):
        raise RuntimeError("`table` is a required parameter and must be a string")

    if table.lower() in tableLookup:
        table = tableLookup[table.lower()]

    sendData = {"whichCat": cat, "table": table}

    if subset is not None:
        if not isinstance(subset, str):
            raise RuntimeError("`subset` must be a string")
        sendData["subset"] = subset

    if epoch is not None:
        if not isinstance(epoch, str):
            raise RuntimeError("`epoch` must be a string")
        sendData["epoch"] = epoch

    if not isinstance(format, str):
        raise RuntimeError("`format` must be a string")
    sendData["format"] = format

    if returnData and (format.lower() != "csv"):
        raise RuntimeError("With returnData set, format must be 'csv'")

    tmp = base.submitAPICall("getSXPSTable", sendData, verbose=verbose, minKeys=("URL", "FILE"))
    tmpDir = None
    if destDir is not None:
        base._createDir(destDir, silent=silent, verbose=verbose)
    elif saveData:
        destDir = "."
    else:
        tmpDir = tempfile.TemporaryDirectory()
        destDir = tmpDir.name

    dl._saveURLToFile(
        tmp["URL"],
        destDir,
        prefix=None,
        name=None,
        clobber=clobber,
        silent=silent,
        verbose=verbose,
    )

    ff = os.path.basename(tmp["FILE"])
    fname = f"{destDir}/{ff}"

    # Do we need to unzip it?
    if fname[-3:] == ".gz":
        comm = ["gunzip", fname]
        if verbose:
            print(f"gunzipping {fname}")
        status = subprocess.run(comm, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if status.returncode != 0:
            raise RuntimeError(f"Could not gunzip the downloaded file {fname}")
        fname = fname[:-3]

    ret = None
    if returnData:
        ret = pd.read_csv(fname, sep=",", low_memory=False)

    if not saveData:
        if verbose:
            print(f"Removing downloaded file {fname}")
        os.unlink(fname)
        if tmpDir is not None:
            os.rmdir(tmpDir.name)

    if returnData:
        return ret


# ----------------------------------------------------------------------
# xrt_prods functions


def makeProductRequest(
    email,
    sourceID=None,
    sourceName=None,
    sourceDetails=None,
    getMissingInfo=True,
    cat="LSXPS",
    T0=None,
    useObs="all",
    addProds=None,
    skipErrors=False,
    transient=False,
    transAsSource=False,
    silent=True,
    verbose=False,
):
    """Build XRTProductRequest object(s) for the specified source(s).

    This function will create XRTProductRequest objects for the sources
    supplied in the arguments, either a single XRTProductRequest or a
    list thereof, depending on the supplied arguments. Please read the
    argument definitions with care, since the nature of the returned
    XRTProductRequest is heavily affected by these. Note that the
    XRTProductRequest objects built are NOT submitted, thus you can
    inspect and edit them.

    sourceID or sourceName can be set - an error will be raised if both
    (or neither) is set - and can either be a single value, or a list.
    If it is a single value, then a single XRTProductRequest will be
    returned. If a list, then the return value will be a dict of
    XRTProductRequests, indexed by the sourceID or name, whichever you
    supplied.

    **Note** The parameter ``useObs`` only has any effect if either
    products are specified (via ``addProds``). This is because in an
    ``XRTProductRequest``, the choice of which observations to use is
    set per product, thus this can only be set here if products are
    added at this point; if not, you will have to set the observations
    yourself. The `getObsList()` function may help here.

    **If you create many XRTProductRequest objects, please read the
    documentation about how to throttle submissions, rather than sending
    all job requests en masse.**

    Parameters
    ----------

    email : str
        The email address with which you registered to submit
        XRTProductRequest objects to the servers.

    sourceID :int or list or tuple, optional
        The SXPS source ID.

    sourceName : str or list or tuple, optional
        The SXPS source IAUName.

    sourceDetails : dict, optional
        The data returned by the `getSourceDetails()` function for the
        source(s) requested.

    getMissingInfo : bool, optional
        Whether this function should call `getSourceDetails()` to for any
        sources requested but not present in the `sourceDetails` dict.

    cat : str, optional
        Which SXPS catalogue the source is in. This is only needed if
        you do not supply the ``sourceDetails`` for all requested sources,
        as it will be used to look up the details. (default: 'LSXPS').

    T0 : str or None, optional
        Which value to supply as the T0 parameter of the request
        (default ``None``). Valid values are:

        * ``None``: T0 is not set, but the ``getT0`` global
            parameter will be set to ``True``.

        * 'firstObs': T0 will be set to the start time of the
            first observation of this object in the selected catalogue.

        * 'firstBlindDet': T0 will be set to the start time of
            the first observation in which this object was blindy detected
            in the selected catalogue.

        * 'firstDet': T0 will be set to the start time of the
            first observation in which this object was detected, blindly or
            via a retrospective detection, in the selected catalogue.

    useObs: str, optional
        Which observations should be used to build your requested
        observations (default: 'all').

        Valid values are:

        * 'all': Use all observations in the Swift archive (NB, this may
            include observations not used in the selected catalogue).

        * 'allCat': Use all observations in the selected catalogue
            covering this source region.

        * 'blind': Use only the observations in which this object was
            blindy detected in the selected catalogue.

        * 'allDet': Use only the observations in which this object was
            detected, blindly or via a retrospective detection, in the
            selected catalogue.

    addProds: list, optional
        Whether to add any products to the XRTProductRequest objects
        being created. If this is not ``None`` then it should be a list
        of product types (e.g. 'LightCurve', 'Spectrum' etc.). Any
        product for which the function ``XRTProductRequest.add$prod()``
        exists (where ``$prod`` is the string to include in this list).

    skipErrors : bool, optional
        If an error occurs saving a file, do not raise a RuntimeError
        but simply continue to the next file (default ``False``).

    transient : str, optional
        Whether the object requested is from the LSXPS transient list,
        rather than source list (i.e. the name/ID is a transient name/
        ID) (default: ``False``).

    transAsSource : bool, optional
        Only relevant if ``transient=True``, this means that the object
        identifier supplied is a transient, but the desired light curve
        should be taken from the LSXPS data corresponding to this
        transient. If the transient is not (yet) in LSXPS then this will
        result in an error (default: ``False``).

    silent : bool, optional
        Whether to suppress all output (default: ``True``).

    verbose : bool, optional
        Whether to write verbose output (default: ``False``).

    """
    if verbose:
        silent = False

    # First, handle sourceName or sourceID.
    varName, varVal, single = _handleSourceArgs(sourceID, sourceName)

    # May need to convert transientIDs into sourceIDs
    if transient and transAsSource:
        varVal = _transientToSource(cat, varName, varVal, skipErrors=skipErrors, silent=silent, verbose=verbose)

    # so varName is now either `sourceName` or `sourceID`, and varVal
    # is a list of sourceNames or IDs.
    # single will determine whether are returning a dict or a single thing
    ret = {}
    # Go over the input list:
    for i in varVal:
        if verbose:
            print(f"Building XRTProductRequest for {varName} = `{i}`.")

        # if the sourceDetails is missing, don't want to add it to the sourceDetails
        # dict that the user supplied, as that will pollute that dict.
        si = None
        # check if sourceDetails exists
        if (sourceDetails is None) or (i not in sourceDetails):
            # It may be that the user supplied a sourceDetails string with
            # only one entry, corresponding to this source.
            # So check a random key that is in sourceDetails:
            if single and (sourceDetails is not None) and ("IAUName" in sourceDetails):
                si = sourceDetails
                # Warn??
            else:
                if getMissingInfo:
                    data = {
                        varName: i,
                        "cat": cat,
                        "silent": silent,
                        "verbose": verbose,
                    }
                    if not silent:
                        print(f"Have to get sourceDetails for {varName}={i}")
                    si = None
                    if transient and not transAsSource:
                        si = getTransientDetails(**data)
                    else:
                        si = getSourceDetails(**data)
                elif skipErrors:
                    if not silent:
                        print(f"No entry for {varName}={i} in sourceDetails, SKIPPING.")
                        continue
                else:
                    raise ValueError(f"No entry for {varName}={i} in sourceDetails.")
        else:
            si = sourceDetails[i]
        # Now pass everything to a sub function to actually make the
        # request - that func will either return an XRTProductRequest,
        # or a dict of keys [useObs, request].
        asTrans = transient and not transAsSource
        tmp = _makeSingleProductRequest(
            email,
            si,
            T0=T0,
            useObs=useObs,
            addProds=addProds,
            silent=silent,
            verbose=verbose,
            transient=asTrans,
        )

        if isinstance(tmp, dict) and ("ERROR" in tmp):
            if skipErrors:
                if not silent:
                    print(f"Error: {tmp['ERROR']} for {varName}={i}, SKIPPING.")
                    continue
            else:
                raise RuntimeError(f"Error: {tmp['ERROR']} for {varName}={i}.")

        ret[i] = tmp

    if single:
        return ret[varVal[0]]
    else:
        return ret


def _makeSingleProductRequest(
    email,
    sourceDetails,
    T0=None,
    useObs=None,
    addProds=None,
    transient=False,
    silent=True,
    verbose=False,
):
    """Internal function to actually build an XRTProductRequest."""
    if verbose:
        silent = False

    from ...xrt_prods import XRTProductRequest

    req = XRTProductRequest(email, silent=silent)
    # Now get some global parameters
    gp = {"posErr": 1, "centroid": False, "useSXPS": True}
    # Lookups from sourceDetails pars to XRTProductRequest global pars
    lookUps = {"IAUName": "name", "RA": "RA", "Decl": "Dec"}
    for ipar, rpar in lookUps.items():
        if ipar not in sourceDetails:
            return {"ERROR": f"Cannot find {ipar} in sourceDetails"}

        gp[rpar] = sourceDetails[ipar]
        if ipar in ("RA", "Decl"):
            gp[rpar] = float(gp[rpar])

    T0LookUp = {
        "firstobs": "FirstObsMET",
        "firstblinddet": "FirstBlindDetMET",
        "firstdet": "FirstDetMET",
    }
    if transient:
        T0LookUp = {
            "discovery": "DetectionMET",
        }

    # What to do with T0?
    if T0 is None:
        # T0 is not set, to tell user objects to do a look up.
        gp["getT0"] = True
    elif T0.lower() in T0LookUp:
        # T0 is set to one of the allowed values, so find the corresponding
        # key in sourceDetails, and set it.
        p = T0LookUp[T0.lower()]
        if p not in sourceDetails:
            return {"ERROR": f"Cannot find T0 parameter `{p}` in sourceDetails"}
        else:
            if verbose:
                print(f"Trying to get {p}")
            gp["T0"] = float(sourceDetails[p])
    else:
        return {"ERROR": f"`{T0}` is not a valid T0 value."}

    # Now handle useObs.
    # Do this in two pieces.
    # First, we always have to decided about targetIDs, so do that

    # If useObs is 'all', we need to set getTargs, and if not, then we need
    # to work out the targets ourselves, from the catalogue.
    uoString = None  # The default.
    prodPars = {}
    if useObs == "all":
        gp["getTargs"] = True
        prodPars["whichData"] = "all"
    elif useObs is not None:
        # OK, work out all observations and targetIDs.
        if transient:
            # discovery is handled slighlty differently to the others as it has no target and is a string, not list
            if useObs.lower() == "discovery":
                uoString = sourceDetails["DiscoveryObs"]
                gp["targ"] = uoString[0:8]
            elif useObs.lower() == "new":
                uoString = ",".join(sourceDetails["AllNewObs"])
                gp["targ"] = ",".join(map(str, sourceDetails["AllNewTargs"]))
            else:
                raise RuntimeError("UseObs must be 'all', 'new' or 'discovery'")

        else:
            # Don't use stacks, of course, as these are not obsIDs
            # Use dicts, just to make sure I'm not getting duplicates
            # targList = {}
            # obsList = {}
            # # We always want blind detections
            # z = _getObsList(sourceDetails, "Detections", targList, obsList, False)
            # if z is not None:
            #     return z

            # # Now if callCat/allDet we need to add to this.

            # if useObs == "allCat":
            #     z = _getObsList(sourceDetails, "NonDetections", targList, obsList, False)
            #     if z is not None:
            #         return z
            # elif useObs == "allDet":
            #     z = _getObsList(sourceDetails, "NonDetections", targList, obsList, True)
            #     if z is not None:
            #         return z
            # elif useObs != "blind":
            #     raise ValueError(f"`{useObs}` is not a valid useObs value.")
            tmp = getObsList(sourceDetails, useObs=useObs)

            # Now we have all the observations and targets, so update things
            gp["targ"] = ",".join(tmp["targList"])
            uoString = ",".join(tmp["obsList"])

        prodPars["whichData"] = "user"
        prodPars["useObs"] = uoString

    # Now we can set the global parameters
    req.setGlobalPars(**gp)

    # Finally, set the products, if any.
    # Note: I do not here check if the products are valid; that would mean
    # keeping a separate list of products here, and having to edit this
    # every time we add a new product. If user requests a non-existant
    # product, this will raise an error.

    if addProds is not None:
        for p in addProds:
            req.addProduct(p, clobber=True, **prodPars)

    return req


def getObsList(
    sourceDetails=None, sourceID=None, sourceName=None, cat="LSXPS", useObs=None, silent=True, verbose=False
):
    """Get the list of catalogue observations covering the source"""

    if verbose:
        silent = False

    if sourceDetails is None:
        sourceDetails = getSourceDetails(
            sourceID=sourceID, sourceName=sourceName, cat=cat, silent=silent, verbose=verbose
        )
    else:
        pass

    single = False
    varVal = None
    if "IAUName" in sourceDetails:
        single = True
        varVal = ("dummy",)
        tmp = {"dummy": sourceDetails}
        sourceDetails = tmp
    else:
        single = False
        varVal = sourceDetails.keys()

    ret = {}
    for i in varVal:
        targList = {}
        obsList = {}

        if useObs.lower() not in ("allcat", "alldet", "blind", "allnondet", "retro"):
            raise ValueError(f"{useObs} is not a valid value for `useObs`.")

        # If we want blind detections
        if useObs.lower() in ("allcat", "alldet", "blind"):
            if verbose:
                print("Getting blind detections")
            tmp = _getObsList(sourceDetails[i], "Detections", False)
            targList.update(tmp["targList"])
            obsList.update(tmp["obsList"])

        # If wanted, get all non-detections as well
        if useObs.lower() in ("allcat", "allnondet"):
            if verbose:
                print("Getting non-detections")
            tmp = _getObsList(sourceDetails[i], "NonDetections", False)
            targList.update(tmp["targList"])
            obsList.update(tmp["obsList"])

        # Or if we wanted retrospective detections
        elif useObs.lower() in ("alldet", "retro"):
            if verbose:
                print("Getting retrospective detections")
            tmp = _getObsList(sourceDetails[i], "NonDetections", True)
            targList.update(tmp["targList"])
            obsList.update(tmp["obsList"])

        ret[i] = {"targList": list(targList.keys()), "obsList": list(obsList.keys())}

    if single:
        return ret[varVal[0]]
    else:
        return ret


def _getObsList(sourceDetails, key, detOnly):
    targList = {}
    obsList = {}
    if key not in sourceDetails:
        raise RuntimeError(f"Cannot find {key} in sourceDetails")
    if "Observations" in sourceDetails[key]:
        if "ObsID" not in sourceDetails[key]["Observations"].columns:
            raise RuntimeError("sourceDetails has the wrong format. Is your module out of date?")

        # Fork here on detOnly to do it the quick way if we are getting everything
        if detOnly:
            for i, r in sourceDetails[key]["Observations"].iterrows():
                o = r["ObsID"]
                if isinstance(o, int):
                    o = f"{o:011d}"
                if len(o) != 11:
                    return {"ERROR": "sourceDetails has the wrong ObsID format. Is your module out of date?"}
                isDet = False
                for b in BAND_NAMES:
                    k = f"{b}_Info"
                    if ("isDet" in r[k]) and (int(r[k]["isDet"]) == 1):
                        isDet = True
                        break
                if isDet:
                    obsList[o] = 1
                    targ = o[0:8]
                    targList[targ] = 1

        else:
            for o in sourceDetails[key]["Observations"]["ObsID"]:
                if isinstance(o, int):
                    o = f"{o:011d}"
                if len(o) != 11:
                    return {"ERROR": "sourceDetails has the wrong ObsID format. Is your module out of date?"}
                obsList[o] = 1
                targ = o[0:8]
                targList[targ] = 1
    ret = {"targList": targList, "obsList": obsList}
    return ret
