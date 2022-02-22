"""SXPS data access functions.

This module provides SXPS-specific functions for downloading data,
products or more information.

Provided functions:

    getSourceInfo()
    getSourceLightCurve()

"""


import os
import io
import pandas as pd
from .. import main as base
from .download import handleLightCurve

if base.HAS_ASTROPY:
    import astropy.coordinates  # noqa

SXPS_LC_BINNING = {
    "observation": "Observation",
    "obs": "Observation",
    "obsid": "Observation",
    "snapshot": "Snapshot",
    "ss": "Snapshot",
}

SXPS_LC_TIMEFORMAT = {"met": "MET", "swift met": "MET", "mjd": "MJD", "tdb": "TDB"}


def handleSourceArgs(sourceID, sourceName):
    """Internal function to handle sourceID/name arguments.

    This function receives the sourceID and sourceName passed in
    a call, ensures that only one is set, and then converts the value
    into a list if necessary.

    It returns three things, in order:

    varName = 'sourceID' or 'sourceName' = the name of the argument to
            send to the API call.

    varVal  = a list of the supplied values.

    single  = True/False: whether a single value, instead of a list,
            was supplied.

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


def getSourceInfo(sourceID=None, sourceName=None, catalogue="LSXPS", silent=True, verbose=False):
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

    sourceID : Union(int,list,tuple) The SXPS source ID.

    sourceName : Union(str,list,tuple) The SXPS source IAUName.

    catalogue : str Which SXPS catalogue the source is in.

    silent : bool Whether to suppress all output.

    verbose : bool Whether to write verbose output.

    Return:
    -------

    list or dict.

    """
    varName, varVal, single = handleSourceArgs(sourceID, sourceName)

    # The argument has now been made into a list, so we can go through
    # that list and submit the request to the API.
    # We will store the results in ret
    ret = {}

    sendData = {"whichCat": catalogue}
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

    if single:
        return ret[varVal[0]]
    else:
        return ret


def getSourceLightCurve(
    sourceID=None,
    sourceName=None,
    catalogue="LSXPS",
    bands="all",
    binning=None,
    timeFormat=None,
    silent=True,
    verbose=False,
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
    return value will be a list of dicts.

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

    sourceID : Union(int,list,tuple) The SXPS source ID.

    sourceName : Union(str,list,tuple) The SXPS source IAUName.

    catalogue : str Which SXPS catalogue the source is in.

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

    silent : bool Whether to suppress all output.

    verbose : bool Whether to write verbose output.

    **kwargs : dict Other options that can be passed to the API. These
        are:

    showObs : bool Whether the obsID should be included as a column.

    hideBadPup  : bool Whether bins with the "pupWarn" flag set should
        be rejected.

    mergeAliases : bool Whether to include points from sources
        identified as aliases.

    getAllTypes : bool Whether to get all possible data types, and store
        as separate entities. This overrides all of the following
        arguments.

    groupDets : bool Whether all detections (blind and retrospective)
        should be grouped into the same light curve entity.

    groupULs : bool Whether all upper limits (non-detection, and
        retrospective only) should be grouped into the same light
        curve entity.

    groupHRss : bool Whether all HRs (blind and retrospective dets)
        should be grouped into the same light curve entity.

    retroAsUL  : bool Whether to return upper limits, instead of
        count-rate bins, for retrospective detections

    nonDetAsUL : bool Whether to return upper limits, instead of
        count-rate bins, for non detections

    getRetroHR  : bool Whether to include HRs from retrospective
        detections.

    Return
    ------

    dict

    If a list of sources was supplied, then the dictionary will have
    keys corresponding to the sourceID or sourceName, depending on which
    this function was called with. Each of the entries in this dict
    is itself a dict corresponding to the results for a single source.

    If a sourceID/name was supplied not as a list, then the dict
    returned is that containing the results for that source.

    The contents of this dict range significantly, depending on the
    details of your request. The following keys will always exist:

    * TimeFormat : Confirming which time system the time axis uses.

    * Binning : Whether observation or snapshot binning was selected

    * datasets: A list of the keys corresponding to the datasets
        (that is, individual light curves) returned.

    Then there is an entry per light curve *returned*. NB this may not
    match the light curves requested, as empty light curves are not
    returned.

    The names of these datasets depends upon the arguments supplied
    above, and differs for light curves and hardness ratios.

    For light curves, the general form is:

    ${band}_${what}

    ${band} is one of "total", "soft", "medium", "hard".

    ${what} is more complex, as it depends upon the "group" options
    supplied in the arguments. BY default, groupDets and groupULs are
    True, in which case ${what} will be:

    * rates -- for the count rates with 1-sigma errors
    *  UL    -- for the 3-sigma upper limits.

    However if groupDets is False then instead there will be up to
    three "rates" entries for ${what}:

    * "blind_rates" - for cases where a blind detection of the
        source exists.

    * "retro_rates" - for cases where retrospective detections of
        the source exists.

    * "nondet_rates" - for cases where the source was not
        detected, blindly or retrospecitvely.

    Similarly, if groupULs is False then there will up to two "UL"
    entries for ${what}:

    * "retro_UL" - for cases where only a retrospective detection exists

    * "nondet_UL" - for cases where the source was not detected, blindly
         or retrospecitvely.

    Normally, not all of these will exist, as you can specify whether
    retrospective and non-detections are reported as upper limits or as
    count-rate bins, using the retroAsUL and nonDetAsUL arguments; by
    default the former is False and the latter True; that is, all
    detections (blind or retrospective) are reported as count-rate bins
    and non-detections as upper limits.

    If the parameters "getAllTypes" is set to True then both upper
    limits AND count-rate bins will be produced for the retrospective
    and non-detections, and all no grouping is applied.

    Note that blind detections are always reported with count-rate bins.
    """
    varName, varVal, single = handleSourceArgs(sourceID, sourceName)

    # Now handle the other arguments.

    sendData = {"whichCat": catalogue, "bands": bands, "binning": binning, "timeFormat": timeFormat}

    # And there are other things that may have been set in kwargs.
    # These are all bools. Start with the universal ones, and getAllTypes
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
    tmp = ("groupDets", "groupULs", "groupHRss", "retroAsUL", "nonDetAsUL", "getRetroHR")
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

    binLookup = {"obslc": "Observation", "sslc": "Snapshot"}
    ret = {}

    for i in varVal:
        if verbose:
            print(f"Getting data for {varName} = `{i}`")
        sendData[varName] = i

        # We can just accept this result, as the only key we have to have is "OK", and
        # if that wasn't set we will already have hit an error.
        tmp = base.submitAPICall("getSXPSLC", sendData, verbose=verbose)
        # So, parse it if we can.

        #        ret[i] = tmp

        if tmp["Binning"] in binLookup:
            tmp["Binning"] = binLookup[tmp["Binning"]]

        if "datasets" in tmp:
            ret[i] = handleLightCurve(tmp, silent, verbose)
        else:
            ret[i] = tmp

    if single:
        return ret[varVal[0]]
    else:
        return ret


def getQDPHeader(data, curve, sep):
    """Get the qdp-style header lines for a given light curve.

    This is an internal function, not designed for user calls.

    This examines the DataFrame corresponding to a specific light
    curve, and works out what the READ commands for qdp should be.
    It then returns a string containing this line/s and also a
    qdp comment line giving the headers.

    Parameters
    ----------

    data : dict A light curve dict.

    source : str The source being saved; must be an index in
        data
    curve : str The label defining the light curve; must be an index
        in data

    sep : str The column separator

    Return
    ------

    str The header that needs printing before the data.

    """
    # I want this function to be fairly generic in theory, so that
    # we can support things with symmetric errors as well as asymmetric,
    # but there is no point wasting time working this out now, because
    # at present, the back end ONLY returns asymmetric time errors
    # and either asymmetric errors or no errors.
    # I don't see this changing in the foreseeable future, because
    # we can always handle symmetric errors simply by returning
    # them as if asymmetric. However, leave this function here so that
    # it can be easily changed if we want.
    header = "READ TERR 1"
    if "UpperLimit" not in data[curve].columns:
        header = header + " 2"
    header = header + "\n"
    cols = data[curve].columns.tolist()
    cols = [x for x in cols if x != "ObsID"]
    header = header + "!" + sep.join(cols)
    return header


def saveLightCurves(
    data,
    destDir="lc",
    asQDP=False,
    subDirs=True,
    whichCurves=None,
    whichSources=None,
    clobber=False,
    header=False,
    sep=",",
    suff=None,
    silent=True,
    verbose=False,
):
    """Save the light curves to text files.

    This will save the data as comma-separated data. Other
    functionality will be added soon.

    Parameters
    ----------

    destDir : str The directory in which to save.

    subDirs : bool Save each source's curves in a subdirectory,
        named by the key light curves are indexed under.

    asQDP : bool Whether to save in qdp format

    whichCurves : list A list of the keys identifying the datasets
        to save. By default, all are saved.

    whichSources : list A list of the sources to save. Should be
        keys of the data object.

    header : bool Whether to print a header row

    sep : str Separator for columns in the file

    suff : str If specified, the file suffix to use. Defaults to
        .dat (or .qdp if asQDP is True) if not specified

    clobber : bool Whether to overwrite files if they exist.

    """

    # Little hack needed here to handle the case that we have only a single LC, not a dict of LCs
    # We will know this because it will have the 'datasets' key
    usePrefix = True
    if "datasets" in data:
        usePrefix = False  # Do not prepend this fake sourceID to the file name.
        tmp = {"mySource": data}
        data = tmp
        if subDirs and not verbose:
            print("Ignoring subDits as only a single source was provided.")
        subDirs = False

    # Create the output dir, if needed.
    if not os.path.isdir(destDir):
        if not silent:
            print(f"Making directory {destDir}")
        os.mkdir(destDir)
        if not os.path.isdir(destDir):
            raise RuntimeError(f"Cannot make directory {destDir}")

    # Which sources am I saving?
    if (whichSources is None) or (whichSources == "all"):
        whichSources = data.keys()

    # If we asked for qdp then we need to set the separater to a tab
    if asQDP:
        if (not silent) and (sep != "\t"):
            print("Setting separator to tab, for 'qdp-style; saving")
        sep = "\t"
        header = False

    if suff is None:
        suff = "dat"
        if asQDP:
            suff = "qdp"
        if not silent:
            print(f"Setting suffix to `{suff}`")

    # Now start saving light curves, one source at a time
    for source in whichSources:
        if source not in data:
            raise ValueError(f"{source} is not in the light curve list.")

        path = destDir
        prefix = ""
        if subDirs:
            path = f"{destDir}/{source}"
            if not os.path.isdir(path):
                os.mkdir(path)
                if not os.path.isdir(path):
                    raise RuntimeError(f"Cannot make directory {path}")
        elif usePrefix:
            prefix = f"{source}_"

        _saveSingleLightCurve(
            data[source],
            destDir=path,
            asQDP=asQDP,
            whichCurves=whichCurves,
            clobber=clobber,
            header=header,
            sep=sep,
            suff=suff,
            prefix=prefix,
            silent=silent,
            verbose=verbose,
        )


def _saveSingleLightCurve(
    data,
    destDir="lc",
    asQDP=False,
    whichCurves=None,
    clobber=False,
    header=False,
    sep=",",
    prefix="",
    suff=None,
    silent=False,
    verbose=False,
):
    """Internal function to actually save a light curve.

    This is the work-horse for each separate light curve, called via a
    loop from saveLightCurves(). Its arguments are a subset of that
    function, and are documented there, as that is the user-facing
    function.

    """

    theseCurves = []
    if whichCurves is not None:
        theseCurves = whichCurves
    else:
        theseCurves = data["datasets"]

    # Grab some helper vars
    b = data["Binning"]
    t = data["TimeFormat"]
    if t == "Swift MET":
        t = "MET"

    for c in theseCurves:
        fname = f"{destDir}/{prefix}{c}_{t}_{b}.{suff}"
        if c not in data["datasets"]:
            if verbose:
                print(f"Not saving {prefix}{c} as this curve does not exist.")
            continue

        if os.path.exists(fname) and not clobber:
            raise RuntimeError(f"Cannot write `{fname}`, already exists and clobber=False")

        # In normal mode, we will pass the filename to pandas; in qdp mode we will pass
        # a string buffer
        outvar = fname
        cols = data[c].columns.tolist()

        if asQDP:
            outvar = io.StringIO()
            cols = [x for x in cols if x != "ObsID"]

        # Now we call the pandas function to actually write the data:
        data[c].to_csv(outvar, index=False, sep=sep, header=header, columns=cols)

        # Unless asQDP was set, the light curve has now been saved to the file, so that's that.
        # But if asQDP was set, then we have the data in the outvar buffer.
        # We need to get the QDP header, and then write it all to a file.
        if asQDP:
            qdpheader = getQDPHeader(data, c, sep)
            with open(fname, "w") as outfile:
                outfile.write(f"{qdpheader}\n")
                outfile.write(outvar.getvalue())

        if not silent:
            print(f"Saving file `{fname}`")


def getUpperLimit(
    position=None,
    name=None,
    RA=None,
    Dec=None,
    catalogue="LSXPS",
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

    position : str A string to be parsed as a free-form RA/Dec position.

    name : str A name to be resolved into coordinates

    RA : Union (float,astropy.coordinates.Angle) : The RA.

    Dec : Union (float,astropy.coordinates.Angle) : The declination.

    catalogue : str Which SXPS catalogue the source is in.

    bands : Union(str,list): Either 'all', or a list of labels of
           the energy bands to retrieve ('total', 'soft', 'medium',
           'hard') (default: ['total']).

    whichData : str Which datasets to use for the flux measurement,
       either: 'deepest' or 'all' (default: 'deepest').

    timeFormat : str What format/system to use for the timestamps,
       either: 'cal', 'met', 'mjd', 'tdb' (default: 'cal').

    sigma : float The confidence level for upper limits, in Gaussian
        sigmas (default: 3).

    detectionsAsRates : bool Supply count-rate (and 1-sigma errors) in
        cases that the source is deemed 'detected' (that is, the
        n-sigma lower-limit is >0; where n is set by the detThresh
        parameter) (default: False).

    detThresh : float The significance level to be used for deciding
        if a flux measurement corresponds to a detection or not. If
        None, this will default to sigma.

    skipDetections : bool Skip datasets in which a source is
        detected at / close to the position specified (default: False).

    useCatValues : bool If, in a given dataset, the source is in the
        catalogue in any band, then return the values from the catalogue
        instead of recalculating them.

    pandas : Bool Whether to convert the result to a pandas DataFrame
        (default: True).

    silent : bool Whether to suppress all output.

    verbose : bool Whether to write verbose output.

    Return
    ------

    TBD!


    """
    # Handle the arguments. Do not need to sanity check all arguments,
    # as this can be done by the back end and it makes sense to do it
    # just once, but we do need to handle a few things. First, put most
    # of the options into the dict to send:
    sendData = {
        "catalogue": catalogue,
        "bands": bands,
        "whichData": whichData,
        "timeFormat": timeFormat,
        "sigma": sigma,
        "detectionsAsRates": detectionsAsRates,
        "skipDetections": skipDetections,
        "useCatValues": useCatValues
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
        if "ULData" in tmp:
            tmp["ULData"] = pd.DataFrame(tmp["ULData"], columns=tmp['Columns'])
        if "DetData" in tmp:
            tmp["DetData"] = pd.DataFrame(tmp["DetData"])
    tmp.pop("OK", None)
    return tmp
