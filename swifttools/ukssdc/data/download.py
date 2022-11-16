"""Data download functions.

This module provides functions for downloading data or products.

"""
__docformat__ = "restructedtext en"


import os
import os.path
import io
import shutil
import requests
import re
import fnmatch
import pandas as pd
import subprocess
from .. import main as base


_allowedInstruments = ["bat", "xrt", "uvot"]
_allowedSources = ["uk", "uk_reproc", "us", "italy"]

try:
    from tqdm.auto import tqdm
except ImportError:

    def tqdm(*args, **kwargs):
        """A real simple replacement for tqdm if it's not locally installed"""
        print(f"Downloading {len(args[0])} files...")
        return args[0]


def downloadObsData(
    obsid,
    source="uk_reproc",
    instruments="all",
    destDir="data",
    getAuxil=True,
    getTDRSS=False,
    getLog=False,
    match=None,
    reMatch=None,
    clobber=False,
    skipErrors=False,
    silent=True,
    verbose=False,
    **kwargs,
):
    """Download observation data files.

    This function receives an obsid, or a list thereof, and
    downloads the Swift obsdata for this. It will create one directory
    per obsID, and download files into that. If the directory exists,
    an error will be thrown unless ``clobber=True`` was set, in which
    case the directory will be removed and recreated.

    Parameters
    ----------

    obsid : str or int or list or tuple
        The obsid to download.

    source : str
        Which datacentre to downloaded the data from.

    instruments : str or list or tuple.
        Which instruments to download data for. A list or 'all'.

    destDir : str, optional
        The top-level directory to save files into (default: 'data').

    getAuxil : bool, optional
        Whether to include the 'auxil' directory in the download
        (default: ``True``).

    getTDRSS : bool, optional
        Whether to include the 'tdrss' directory in the download
        (default: ``True``).

    getLog : bool, optional
        Whether to include the 'log' directory in the download
        (default: ``True``).

    match : str or list, optional
        A "glob"-style wildcard string to match against filenames; only
        files matching this will be downloaded. If a list is supplied
        then files which match any of the globs in the list will be
        downloaded. Note, only one of 'match' and 'reMatch' can be set.

    reMatch : str or list, optional
        A regular expression string to match against filenames; only
        files matching this will be downloaded. If a list is supplied
        then files which match any of the expressions in the list will
        be downloaded. Note, only one of 'match' and 'reMatch' can be
        set.

    clobber : bool, optional
        Whether to overwrite files if they exist (default: ``False``).

    skipErrors : bool, optional
        Whether to continue to the next file/observation if an error is
        encountered (default: ``False``).

    silent : bool, optional
        Whether to suppress all output (default: ``True``).

    verbose : bool, optional
        Whether to write verbose output (default: ``False``).

    """
    if verbose:
        silent = False

    # Check validity
    if isinstance(obsid, (str, int)):
        obsid = [obsid]

    if not isinstance(obsid, (list, tuple)):
        raise ValueError("`obsid` must be a list, tuple, int or string.")

    # -------------------------------------
    # Check instruments and handle which we want to get.
    dirs = None

    # Check that 'instruments' and 'source' are valid, and destDir exists
    if isinstance(instruments, str):
        if instruments.lower() == "all":
            dirs = _allowedInstruments
        else:
            raise ValueError("instruments parameter must be 'all' or a list")
    elif isinstance(instruments, (list, tuple)):
        dirs = []
        for i in instruments:
            if i.lower() not in _allowedInstruments:
                raise ValueError(f"`{i}` is not a recognised instrument")
            else:
                dirs.append(i.lower())
    elif instruments is None:
        dirs = []
    else:
        raise ValueError("instruments parameter must be 'all', None or a list")

    if getAuxil:
        dirs.append("auxil")
    if getTDRSS:
        dirs.append("tdrss")
    if getLog:
        dirs.append("log")

    # ---------------------------------------
    # Check match and rematch
    if (match is not None) and (reMatch is not None):
        raise ValueError("Cannot have both match and reMatch set")

    if match is not None:
        if isinstance(match, str):
            match = [match]
        if not isinstance(match, (list, tuple)):
            raise ValueError("`match` must be a list, tuple or string")
    if reMatch is not None:
        if isinstance(reMatch, str):
            reMatch = [reMatch]
        if not isinstance(reMatch, (list, tuple)):
            raise ValueError("`reMatch` must be a list, tuple or string")
        tmp = []
        for r in reMatch:
            tmp.append(re.compile(r))
        reMatch = tmp

    # ---------------------------------------
    # Is the source valid
    if source.lower() not in _allowedSources:
        raise ValueError(f"`{source}` is not a valid data source.")
    source = source.lower()

    # clobber = False
    # if "clobber" in kwargs.keys():
    #     clobber = bool(kwargs["clobber"])

    # skipErrors = False
    # if "skipErrors" in kwargs.keys():
    #     skipErrors = bool(kwargs["skipErrors"])

    # Do we need to make the dest dir?
    base._createDir(destDir, silent=silent, verbose=verbose)

    if not silent:
        print(f"Downloading {len(obsid)} datasets")

    for obs in obsid:
        if isinstance(obs, str):
            obs = int(obs)
        if isinstance(obs, int):
            obs = f"{obs:011d}"
        else:
            raise ValueError(f"Obsid `{obs}` is not valid.")
        if verbose:
            print(f"Getting obsid {obs}")

        # Path already exists?
        obsPath = f"{destDir}/{obs}"
        if os.path.exists(obsPath):
            if clobber:
                if not silent:
                    print(f"WARNING: Deleting / overwriting directory {obsPath}.")
                shutil.rmtree(obsPath)
            else:
                raise RuntimeError(f"Directory {obsPath} exists and clobber is False.")

        # Make the path
        base._createDir(obsPath, silent=silent, verbose=verbose)

        # Get the file list for this obs.
        fileData = _getFileList(obs, dirs, source, silent, verbose)
        fileTree = fileData["fileList"]

        # Does it exist?
        if ("dirs" not in fileTree.keys()) or ("files" not in fileTree.keys()):
            if skipErrors:
                if not silent:
                    print(f"Cannot find obs {obs}, skipping")
            else:
                raise RuntimeError(f"Cannot find obs {obs}.")

        if len(fileTree["files"]) == 0:
            if not silent:
                print(f"Obs `{obs}` has no files to download, skipping")
            continue

        # Make all directories
        for dir in fileTree["dirs"]:
            # Skip the top level dir, already made
            if len(dir) == 0:
                continue
            outDirName = f"{obsPath}/{dir}"
            base._createDir(outDirName, silent=silent, verbose=verbose)

        # Now get the files, use tqdm to plot progress:
        # display = not silent
        urlBase = fileData["url"]

        if silent:
            myList = fileTree["files"]
        else:
            myList = tqdm(fileTree["files"], desc=f"Downloading {obs}", unit="files")

        # for f in tqdm(fileTree["files"], desc=f"Downloading {obs}", unit="files", display=display):
        for f in myList:
            url = f"{urlBase}/{f}"
            outPath = f"{obsPath}/{f}"

            if match is not None:
                isOK = False
                for m in match:
                    if fnmatch.fnmatch(os.path.basename(f), m):
                        isOK = True
                        break
                if not isOK:
                    if verbose:
                        print(f"Skipping file {f}")
                    continue
            elif reMatch is not None:
                isOK = False
                for m in reMatch:
                    if m.search(os.path.basename(f)) is not None:
                        isOK = True
                        break
                if not isOK:
                    if verbose:
                        print(f"Skipping file {f}")
                    continue

            r = requests.get(url, stream=True, allow_redirects=True)
            if r.ok:
                filedata = r.raw.read()
                with open(outPath, "wb") as outfile:
                    outfile.write(filedata)
            else:
                if not skipErrors:
                    raise RuntimeError(f"Failed to download {url}")
                if not silent:
                    print(f"Failed to download {url}")


def downloadObsDataByTarget(targetID, silent=True, verbose=False, **kwargs):
    """Download observation data files by target.

    This function receives a targetID, or a list of targetIDs, and then
    calls ``downloadObsData()`` for each obsID within each target.

    Parameters
    ----------

    targetID : str or int or list or tuple
            The targetID/s to download.

    silent : bool, optional
        Whether to suppress all output (default: ``True``).

    verbose : bool, optional
        Whether to write verbose output (default: ``False``).

    **kwargs : dict, optional
        Arguments to pass to ``downloadObsData()``.

    """
    if verbose:
        silent = False

    # Check validity
    if isinstance(targetID, (str, int)):
        targetID = [targetID]

    if not isinstance(targetID, (list, tuple)):
        raise ValueError("`targetID` must be a list, tuple, int or string.")

    for targ in targetID:
        o = _getObsList(targ, silent=silent, verbose=verbose)
        if verbose:
            print(f"For {targ}, have to get obsIDs: {o}")
        downloadObsData(o, silent=silent, verbose=verbose, **kwargs)


def _getObsList(targetID, silent=True, verbose=False):
    """Internal function get the the obsID list for a targetID.

    Parameters
    ----------

    targetID : int or str
        The targetID.

    silent : bool, optional
        Whether to suppress all output (default: ``True``).

    verbose : bool, optional
        Whether to write verbose output (default: ``False``).

    Returns
    -------

    list
        The list of obsIDs.

    """
    if verbose:
        silent = False

    sendData = {"targetID": targetID}
    ret = base.submitAPICall("getObsByTarg", sendData, minKeys=["obsList"], verbose=verbose)
    return ret["obsList"]


# --------------------------------------------------------------------
# Functions not explicitly exported to the public, although usable
# internally.


def _saveURLToFile(url, path, prefix=None, name=None, clobber=False, silent=True, verbose=False):
    """Internal function to download and save a file.

    Parameters
    ----------

    url : str
        The URL of the file to download.

    path : str
        The path to the directory into which the file should be saved.

    prefix : str, optional
        A prefix to prepend to file names

    name : str,optional
        The filename to save. If None uses the basename of the URL
    clobber: bool, optional
        Overwrite existing files? (default ``False``)

    silent : bool, optional
        Whether to suppress all output (default: ``True``).

    verbose : bool, optional
        Whether to write verbose output (default: ``False``).

    """
    if verbose:
        silent = False

    if prefix is None:
        prefix = ""
    if name is None:
        fname = os.path.basename(url)
    else:
        fname = name
    fname = f"{path}/{prefix}{fname}"
    if (os.path.exists(fname)) and (not clobber):
        if not silent:
            print(f"`{fname}` exists and clobber=False, SKIPPING")
        return False

    if verbose:
        print(f"Downloading file `{fname}`")

    # # TEMP LINES
    # from requests.auth import HTTPBasicAuth

    d = requests.get(
        url,
        # auth=HTTPBasicAuth("LSXPS", "CatPreview"),
    )
    if verbose:
        print(f"Saving file `{fname}`")

    with open(fname, "wb") as f:
        f.write(d.content)
        return True


def _getFileList(obs, dirs, source, silent=True, verbose=False):
    """Run an API call to get the file list.

    Parameters
    ----------

    obs : str
        The obsid.

    dirs : list
        The directories to list.

    source : str
        Where to get the data from.

    silent : bool, optional
        Whether to suppress all output (default: ``True``).

    verbose : bool, optional
        Whether to write lots of output (default: ``False``).

    Returns
    -------

    dict
        Containing the URL, directory and file list.

    """
    if verbose:
        silent = False

    #
    sendData = {"obsid": obs, "source": source, "dirs": dirs}
    if verbose:
        print(f"Getting filelist for {obs} from {source} archive.")

    ret = base.submitAPICall("listObsFiles", sendData, minKeys=["url", "fileList"], verbose=verbose)
    return ret


def _handleLightCurve(data, oldCols=False, silent=True, verbose=False):
    """Convert light curves returned via API into pandas DataFrames.

    This is a generic function which receives light curves returned by
    the API, which have a fixed form, and converts them into pandas
    DataFrames for ease of use.

    Parameters
    ----------

    data : dict
        The data decoded from JSON.

    oldCols : bool, optional
        Whether to accept the old xrt_prods UL column
        (default: ``False``).

    silent : bool, optional
        Whether to suppress all output (default: ``True``).

    verbose : bool, optional
        Whether to write lots of output (default: ``False``).

    Returns
    -------
    pandas.DataFrame
        Light curve in a DataFrame

    """
    if verbose:
        silent = False

    ret = {}
    url = {}
    skipKeys = []
    for key in data["Datasets"]:
        tmpKey = f"{key}Data"
        if tmpKey not in data:
            raise RuntimeError(f"Expected to find `{key}` data, but it is not present.")
        if "columns" not in data[tmpKey]:
            raise RuntimeError(f"`{key}` contains no column information.")
        cols = data[tmpKey]["columns"]
        skipKeys.append(tmpKey)

        if len(data[tmpKey]["data"]) > 0:
            if len(cols) != len(data[tmpKey]["data"][0]):
                # print(f"ARSE - {tmpKey}")
                # print(cols)
                # print(data[tmpKey]["data"])
                raise RuntimeError(f"Unable to handle the {tmpKey} light curve, corrupt data?")

        if "UL" in key and not oldCols:
            cols = ["UpperLimit" if x == "Rate" else x for x in cols]

        tmpDF = pd.DataFrame(data[tmpKey]["data"], columns=cols, dtype=str)

        types = {}
        for c in cols:
            if c in ("ObsID", "URL"):
                types[c] = str
            else:
                types[c] = float

        ret[key] = tmpDF.astype(types)
        # -- OPTION - could remove the RatePos and RateNeg columns if "UL" in tmpKey

        if "ObsID" in ret[key].columns:
            ret[key]["ObsID"] = ret[key]["ObsID"].apply(lambda x: f"{int(float(str(x).replace('::ObsID=', ''))):011d}")
        if "URL" in data[tmpKey]:
            url[key] = data[tmpKey]["URL"]

    for k, v in data.items():
        if k not in skipKeys:
            ret[k] = v

    if len(url) > 0:
        ret["URLs"] = url

    return ret


def _saveLightCurveFromURL(
    data, destDir="lc", prefix="", nosys="no", incbad="yes", clobber=False, skipErrors=False, silent=True, verbose=False
):
    """Save light curves to disk.

    This (internal) function receives a data structure, ideally produced
    by _handleLightCurve(), but at least containing the ``Datasets`` and
    ``URLs`` entries.

    It then downloads the relevant data, and saves them.

    Parameters
    ----------

    data : dict
        The light cure data

    destDir : str, optional
        The directory in which to save the light curves (default: "lc").

    prefix : str, optional
        A prefix to prepend to the file names before saving.

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

    clobber : bool, optional
        Whether to overwrite files that already exist
        (default: ``False``).

    skipErrors : bool, optional
        Whether to continue if a problem occurs with one file
        (default: ``False``).

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

    base._createDir(destDir, silent=silent, verbose=verbose)

    if not (("URLs" in data) and ("Datasets" in data)):
        raise ValueError("data must contain keys 'URLs' and 'Datasets'.")

    # Now build the file list. This will be "fun", thanks to incbad, nosys, and the HRs sharing a file
    files = []
    for tmpkey in data["Datasets"]:
        if tmpkey not in data["URLs"]:
            raise RuntimeError(f"Cannot find `{tmpkey}` in the URLs. Is your swittools version up to date?")
        url = data["URLs"][tmpkey]
        # Skip if we have it:
        if url in files:
            continue

        # Do we want this file?
        if ("nosys" in tmpkey) and (nosys == "no"):
            continue
        if ("incbad" in tmpkey) and (incbad == "no"):
            continue
        if ("nosys" not in tmpkey) and (nosys == "yes"):
            continue
        if ("incbad" not in tmpkey) and (incbad == "yes"):
            continue
        files.append(url)

    if len(files) == 0:
        if not silent:
            print("No files selected to download")
        return

    # display = not silent
    if silent:
        myList = files
    else:
        myList = tqdm(files, desc="Downloading light curves", unit="files")

    #    for url in tqdm(files, desc="Downloading light curves", unit="files", display=display):
    for url in myList:
        file = os.path.basename(url)
        outPath = f"{destDir}/{prefix}{file}"
        if (os.path.exists(outPath)) and (not clobber):
            if not skipErrors:
                raise RuntimeError(f"File `{outPath}` already exists.")
            if not silent:
                print(f"File `{outPath}` already exists, SKIPPING")

        if verbose:
            print(f"Saving {outPath}")
        r = requests.get(url, stream=True, allow_redirects=True)
        if r.ok:
            filedata = r.raw.read()
            with open(outPath, "wb") as outfile:
                outfile.write(filedata)
        else:
            if not skipErrors:
                raise RuntimeError(f"Failed to download {url}")
            if not silent:
                print(f"Failed to download {url}")


def _getQDPHeader(data, curve, sep):
    """Get the qdp-style header lines for a given light curve.

    This is an internal function, not designed for user calls.

    This examines the DataFrame corresponding to a specific light
    curve, and works out what the READ commands for qdp should be.
    It then returns a string containing this line/s and also a
    qdp comment line giving the headers.

    Parameters
    ----------

    data : dict
        A light curve dict, created by this API.

    source : str
        The source being saved; must be an index in ``data``.

    curve : str
        The label defining the light curve; must be an index in
        ``data``.

    sep : str
        The column separator to use when writing the header.

    Returns
    -------

    str
        The header that needs printing before the data.

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


def _saveDFToDisk(data, fname, cols, header, sep, qdpH, asQDP, clobber=False, silent=False, verbose=True):
    """Actually save a DataFrame to disk.

    Parameters
    ----------

    data : DataFrame
        The DataFrame to save.

    fname : str
        The file name.

    cols : list
        The columns to write.

    header : bool
        Whether to write a header columns.

    sep : str
        The column delimiter.

    qdpH : str or None
        The qdp-style header (READ lines).

    asQDP : bool
        Whether to save as a qdp file.

    clobber : bool, optional
        Whether to overwrite files if they exist (default: ``False``).

    silent : bool, optional
        Whether to suppress all output (default: ``True``).

    verbose : bool, optional
        Whether to write verbose output (default: ``False``).

    Returns
    -------

    bool
        Whether everything worked OK or not.

    """
    if verbose:
        silent = False

    if os.path.exists(fname) and not clobber:
        if not silent:
            print(f"Cannot write `{fname}`, already exists and clobber=False.")
            return False

    # print("COLUMNS: ",data.columns.tolist())
    # print("LIST: ", cols)

    txtBuffer = io.StringIO()
    data.to_csv(txtBuffer, index=False, sep=sep, header=False, columns=cols)
    with open(fname, "w") as outfile:
        if verbose:
            print(f"Writing file: `{fname}`")
        if asQDP and qdpH is not None:
            outfile.write(f"{qdpH}\n")
        if header:
            if asQDP:
                outfile.write("!")
            outfile.write(sep.join(cols) + "\n")

        outfile.write(txtBuffer.getvalue())

    return True


# --------------------------------------------------------------------
# Product-related functions, that are shared between modules
# --------------------------------------------------------------------

# -----------------------------
# Light curve related functions


def _getLightCurve(
    type,
    objectID,
    returnData=False,
    saveData=True,
    nosys="no",
    incbad="yes",
    destDir="lc",
    prefix="",
    clobber=False,
    skipErrors=False,
    silent=True,
    verbose=False,
):
    """Get a specific XRT light curve.

    This function is not intended to be called directly by the user,
    but rather, via wrappers which will work out 'type' and 'objectID'.

    This function can do two things:

    * Download light curve data and return it as a data structure.

    * Save the light curve files to disk.

    These are not mutually exclusive; you can do them both.

    Parameters
    ----------

    type : str
        The type of light curve to get (e.g. 'GRB', 'REBIN_LC' etc.)

    objectID : int
        The ObjectID

    returnData : bool, optional
        Whether to return the organised light curve data from this
        function (default: ``False``).

    saveData : bool, optional
        Whether to save the light curve data to disk (default:
        ``False``).

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
        datapoints (default: 'yes').

    destDir : str, optional
        The directory in which to save the light curves (default: "lc").

    prefix : str, optional
        A prefix to prepend to the file names before saving.

    clobber : bool, optional
        Whether to overwrite files that already exist
        (default: ``False``).

    skipErrors : bool, optional
        Whether to continue if a problem occurs with one file
        (default: ``False``).

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

    if not (returnData or saveData):
        raise RuntimeError("I have to do at least one of save or return!")

    if isinstance(incbad, bool):
        if incbad:
            incbad="yes"
        else:
            incbad="no"
    
    if isinstance(nosys, bool):
        if nosys:
            nosys="yes"
        else:
            nosys="no"

    sendData = {"type": type, "objectID": objectID, "incbad": incbad, "nosys": nosys}

    tmp = base.submitAPICall("downloadLightCurve", sendData, verbose=verbose, minKeys=("Datasets",))
    ret = None

    if "NOLC" in tmp:
        if returnData:
            ret = tmp
    else:
        if returnData:
            ret = _handleLightCurve(tmp, silent=silent, verbose=verbose)
        else:
            ret = {}
            # If we didn't want to return, let's not waste CPU time making the
            # DataFrames, but we still need the URLs:
            url = {}
            for key in tmp["Datasets"]:
                tmpKey = f"{key}Data"
                if tmpKey not in tmp:
                    raise RuntimeError(f"Expected to find `{key}` data, but it is not present.")

                if "URL" in tmp[tmpKey]:
                    url[key] = tmp[tmpKey]["URL"]

            if len(url) > 0:
                ret["URLs"] = url
                ret["Datasets"] = tmp["Datasets"]

        if saveData:
            _saveLightCurveFromURL(
                ret,
                destDir=destDir,
                clobber=clobber,
                incbad=incbad,
                nosys=nosys,
                prefix=prefix,
                skipErrors=skipErrors,
                silent=silent,
                verbose=verbose,
            )

    if returnData:
        return ret


def _saveLightCurveFromDict(
    data,
    destDir="lc",
    asQDP=False,
    whichDatasets="all",
    clobber=False,
    header=False,
    sep=",",
    prefix="",
    suff=None,
    timeFormatInFname=False,
    binningInFname=False,
    skipErrors=False,
    silent=False,
    verbose=False,
    **kwargs,
):
    """Save a light curve dict as files on disk.

    This function take a standard light curve ``dict`` and saves the
    requested datasets to disk following the conventions set by the
    function parameters.

    Parameters:
    -----------

    data : dict
        A standard light curve ``dict`` of the data to save.

    destDir : str, optional
        The directory in which to save the files (default: 'lc').

    asQDP : bool, optional
        Whether to save in qdp format. Overrides ``sep`` and ``suff``
        (default: ``False``).

    whichDatasets : list or str, optional
        A list of the keys identifying the datasets to save, or 'all'
        (default: 'all').

    clobber : bool
        Whether to overwrite files if they exist.

    header : bool, optional
        Whether to print a header row (default: ``False``).

    sep : str, optional
        Separator to use for columns in the file (default: ',').

    prefix : str, optiona;
        An optional string to prepend to the dataset label in creating
        the file names.

    suff : str, optional
        The file suffix to use. If ``None`` then it will be "qdp" if
        ``asQDP`` is ``True``, else ".dat" (default: ``None``).

    timeFormatInFname : bool, optional
        Whether the filename should include the time format of the light
        curve (default: ``False``).

    binningInFname : bool, optional
        Whether the filename should include the binning method of the
        light curve (default: ``False``).

    skipErrors : bool, optional
        If an error occurs saving a file, do not raise a RuntimeError
        but simply continue to the next file (default ``False``).

    silent : bool, optional
        Whether to suppress all output (default: ``True``).

    verbose : bool, optional
        Whether to write verbose output (default: ``False``).

    **kwargs: dict, optional
        This exists so that if extra parameters are passed to this
        function they do not cause errors; this is necessary because
        the data.SXPS.getLightCurves() module will pass some extra
        arguments to this function.

    """
    if verbose:
        silent = False

    if "Datasets" not in data:
        raise ValueError("The `data` parameter should be a light curve dict. It isn't.")

    theseCurves = []
    if (whichDatasets is None) or (whichDatasets == "all"):
        theseCurves = data["Datasets"]
    else:
        theseCurves = whichDatasets

    base._createDir(destDir, silent=silent, verbose=verbose)

    # Grab some helper vars
    b = data["Binning"]
    t = data["TimeFormat"]
    if t == "Swift MET":
        t = "MET"

    if suff is None:
        if asQDP:
            suff='qdp'
        else:
            suff='dat'

    for c in theseCurves:
        fname = f"{destDir}/{prefix}{c}"
        if timeFormatInFname:
            fname = fname + f"_{t}"
        if binningInFname:
            fname = fname + f"_{b}"
        fname = fname + f".{suff}"

        if c not in data["Datasets"]:
            if not silent:
                print(f"Not saving {prefix}{c} as this curve does not exist.")
            continue

        cols = data[c].columns.tolist()
        qdpheader = None
        if asQDP:
            cols = [x for x in cols if x != "ObsID"]
            qdpheader = _getQDPHeader(data, c, sep)

        ok = _saveDFToDisk(
            data[c],
            fname,
            cols,
            header,
            sep,
            qdpheader,
            asQDP,
            clobber=clobber,
            silent=silent,
            verbose=verbose,
        )
        if not (ok or skipErrors):
            raise RuntimeError("Cannot write `{fname}`")


# ---------
# Rebin fns


def _rebinLightCurve(type, objectID, binMeth=None, silent=True, verbose=False, **kwargs):
    """Submit a job to request a light curve.

     This function is not intended to be called directly by the user,
     but rather, via wrappers which will work out 'type' and 'objectID'.

     Parameters
     ----------

    type : str
         The type of light curve to get (e.g. 'GRB', 'REBIN_LC' etc.)

     objectID : int
         The ObjectID

     binMeth : str
         What binning method to apply ('snapshot', 'observation', 'time',
         'counts').

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

    sendData = {"type": type, "objectID": objectID, "binMeth": binMeth}
    sendData.update(kwargs)

    tmp = base.submitAPICall("rebinLightCurve", sendData, verbose=verbose, minKeys=("JobID",))
    t = int(tmp["JobID"])
    if verbose:
        print(f"Success: JobID={t}")
    return t


def _checkRebinStatus(JobID, silent=True, verbose=False):
    """Check the status of a rebin job.

    This takes the JobID (returned by ``rebinLightCurve()``) and returns
    its status.

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

    sendData = {"JobID": JobID}

    tmp = base.submitAPICall("checkRebinStatus", sendData, verbose=verbose, minKeys=("status", "text"))

    ret = {"statusCode": tmp["status"], "statusText": tmp["text"]}

    return ret


def _rebinComplete(JobID):
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

    tmp = _checkRebinStatus(JobID, silent=True, verbose=False)

    if tmp["statusCode"] == 4:
        return True
    else:
        return False


def _cancelRebin(JobID, silent=True, verbose=False):
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

    bool
        Whether the was cancelled or not.

    """
    if verbose:
        silent = False

    if not isinstance(JobID, int):
        raise ValueError("JobID must be an int")

    sendData = {"JobID": JobID}
    tmp = base.submitAPICall("cancelRebin", sendData, verbose=verbose, skipErrors=True)

    if "OK" in tmp:
        return True
    else:
        if verbose or not silent:
            print("Cannot cancel job - it may have already completed.")
        return False


# ---------------------------------
# Spectrum related functions


def _saveSpectrum(
    data,
    destDir="spec",
    spectra="all",
    specSubDirs=False,
    saveImages=True,
    saveData=True,
    prefix="",
    extract=False,
    removeTar=False,
    clobber=False,
    skipErrors=False,
    silent=True,
    verbose=False,
):
    """Internal function to save spectra to disk.

    This saves the spectra files, identified in the supplied dict,
    to disk. This expects to receive the standard dict structure
    returned by the API back end.

    Parameters
    ----------

    data : dict
        The object containing the data.

    destDir : str, optional
        The directory in which to save the spectra (default: "spec").

    spectra : str or list, optional
        Which spectra to save data for ("all" or a list; default "all").

    specSubDirs : bool, optional
        Whether to save each spectrum to its own subdirectory (with the
        spectrum name) (default: ``False``).

    saveImages : bool, optional
        Whether to save the gif images (default ``True``).

    saveData : bool, optional
        Whether to save the actual spectral data (default ``True``).

    prefix : str, optional
        A prefix to prepend to the image file names before saving.

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

    silent : bool, optional
        Whether to suppress all output (default: ``True``).

    verbose : bool, optional
        Whether to write verbose output (default: ``False``).

    """
    if verbose:
        silent = False

    # Structure of data is: regions => modes => models => spectra
    # Datafile appears by regions
    # image by spectrum

    # Step over regions
    if "rnames" not in data:
        raise ValueError("data dict is missing the 'Spectra' entry")

    if not (saveData or saveImages):
        if not silent:
            print("Nothing to do, not selected anything to save.")
            return

    base._createDir(destDir, silent=silent, verbose=verbose)

    for rname in data["rnames"]:
        if (spectra == "all") or (rname in spectra):
            if verbose:
                print(f"Saving `{rname}` spectrum")
            path = destDir
            if specSubDirs:
                path = f"{destDir}/{rname}"
                base._createDir(path, silent=silent, verbose=verbose)

            # The data file is at the spectrum level so if we wanted it, save it now
            if saveData and ("DataFile" in data[rname]):
                url = data[rname]["DataFile"]
                ok = _saveTar(
                    url,
                    path,
                    prefix=prefix,
                    extract=extract,
                    removeTar=removeTar,
                    clobber=clobber,
                    silent=silent,
                    verbose=verbose,
                )
                if not ok:
                    if not skipErrors:
                        raise RuntimeError(f"Cannot save/extract {url} in {path}/")

            if saveImages and ("Modes" in data[rname]):
                for mode in data[rname]["Modes"]:
                    for model in data[rname][mode]["Models"]:
                        if "Image" in data[rname][mode][model]:
                            url = data[rname][mode][model]["Image"]
                            ok = _saveURLToFile(
                                url,
                                path,
                                prefix=prefix,
                                clobber=clobber,
                                silent=silent,
                                verbose=verbose,
                            )
                        if not ok:
                            if skipErrors:
                                continue
                            else:
                                raise RuntimeError(f"Cannot save {url} into {path}/")


def _saveTar(
    url,
    path,
    prefix="",
    extract=False,
    removeTar=False,
    strip=False,
    clobber=False,
    silent=True,
    verbose=False,
    **kwargs,
):
    ok = _saveURLToFile(url, path, prefix=prefix, clobber=clobber, silent=silent, verbose=verbose)
    if not ok:
        return False

    if extract:
        fname = os.path.basename(url)
        fname = f"{path}/{fname}"

        os.chdir(path)
        if not silent:
            print(f"Extracting `{fname}`")
        comm = ["tar", "-xzf", fname]
        if strip:
            comm.insert(1, "--strip-components=1")
        if verbose:
            comm.insert(1, "-v")
            # pcomm = " ".join(comm)
            # print(f"Calling `{pcomm}`")

        status = subprocess.run(comm, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if status.returncode != 0:
            if verbose:
                print(f"tar command exited with {status.returncode}")
            return False
        if verbose:
            print(status.stdout.decode("utf-8"))
            print(status.stderr.decode("utf-8"))
        if removeTar:
            os.unlink(fname)
            if verbose:
                print(f"Removing file {fname}")

    return True
