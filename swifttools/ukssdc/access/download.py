"""Data download functions.

This module provides functions for downloading data or products.

Provided functions:

    downloadObsData()

"""


import os
import shutil
import requests
import pandas as pd
from .. import main as base


_allowedInstruments = ["bat", "xrt", "uvot"]
_allowedSources = ["uk", "uk_reproc", "us", "italy"]

try:
    from tqdm.auto import tqdm
except ImportError:

    def tqdm(*args, **kwargs):
        """A real simple replacement for tqdm if it's not locally installed"""
        if "display" in kwargs.keys() and kwargs["display"] is not False:
            print(f"Downloading {len(args[0])} files...")
        return args[0]


def downloadObsData(data, source="uk_reproc", instruments="all", destDir=".", silent=True, verbose=False, **kwargs):
    """Download observation data files.

    This function receives an obsid/targetID, or a list thereof, and
    downloads the Swift obsdata for this. It will create one directory
    per obsID, and download files into that. If the directory exists,
    an error will be thrown unless 'clobber=True' was set, in which case
    the directory will be removed and recreated.

    Parameters
    ----------

        data : Union[str,int,list,tuple] : The obs/targIDs to download.

        source : str Which datacentre to downloaded the data from.

        instruments : Union[str,list,tuple]. Which instruments to
            download data for. A list or 'all'.

        destDir : str The top-level directory to save files into.

        silent : bool Whether to suppress all output.

        verbose : bool Whether to write verbose output.

        **kwargs : Other optional arguments, including:

            getTDRSS : bool Download tdrss/ directory if available.

            getLog : bool Download log/ directory if available.

            noAuxil : bool Do not get the auxil/ directory.

    """
    # Check validity
    if isinstance(data, (str, int)):
        data = [data]

    if not isinstance(data, (list, tuple)):
        raise ValueError("`data` must be a list, tuple, int or string.")

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
    else:
        raise ValueError("instruments parameter must be 'all' or a list")

    if ("noAuxil" not in kwargs) or (not kwargs["noAuxil"]):
        dirs.append("auxil")
    if ("getTDRSS" in kwargs) and kwargs["getTDRSS"]:
        dirs.append("tdrss")
    if ("getLog" in kwargs) and kwargs["getLog"]:
        dirs.append("log")

    # ---------------------------------------
    # Is the source valid
    if source.lower() not in _allowedSources:
        raise ValueError(f"`{source}` is not a valid data source.")
    source = source.lower()

    clobber = False
    if "clobber" in kwargs.keys():
        clobber = bool(kwargs["clobber"])

    skipErrs = False
    if "skipErrs" in kwargs.keys():
        skipErrs = bool(kwargs["skipErrs"])

    # Do we need to make the dest dir?
    if not os.path.exists(destDir):
        os.mkdir(destDir)

    # Now one obsID at a time
    if isinstance(data, (str, int)):
        data = [data]
    for obs in data:
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
                raise RuntimeError(f"Directory {obsPath} exists and clobber not set.")

        # Make the path
        os.mkdir(obsPath)

        # Get the file list for this obs.
        fileData = getFileList(obs, dirs, source, silent, verbose)
        fileTree = fileData["fileList"]

        # Does it exist?
        if ("dirs" not in fileTree.keys()) or ("files" not in fileTree.keys()):
            if skipErrs:
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
            os.mkdir(outDirName)
            if verbose:
                print(f"Creating directory {outDirName}.")

        # Now get the files, use tqdm to plot progress:
        display = not silent
        urlBase = fileData["url"]

        for f in tqdm(fileTree["files"], desc=f"Downloading {obs}", unit="files", display=display):
            url = f"{urlBase}/{f}"
            outPath = f"{obsPath}/{f}"

            r = requests.get(url, stream=True, allow_redirects=True)
            if r.ok:
                filedata = r.raw.read()
                with open(outPath, "wb") as outfile:
                    outfile.write(filedata)
            else:
                if not skipErrs:
                    raise RuntimeError(f"Failed to download {url}")
                if not silent:
                    print(f"Failed to download {url}")


# --------------------------------------------------------------------
# Functions not explicitly exported to the public, although usable
# internally.


def getFileList(obs, dirs, source, silent=True, verbose=False):
    """Run an API call to get the file list.

    Parameters
    ----------

    obs : str       The obsid.

    dirs : list     The directories to list.

    source : str    Where to get the data from.

    silent : bool   Whether to suppress all output (default: True).

    verbose : bool  Whether to write lots of output (default: False).

    Return
    -------

    dict            Containing the URL, directory and file list.

    """
    #
    sendData = {"obsid": obs, "source": source, "dirs": dirs}
    if verbose:
        print(f"Getting filelist for {obs} from {source} archive.")

    ret = base.submitAPICall("listObsFiles", sendData, minKeys=["url", "fileList"], verbose=verbose)
    return ret


def handleLightCurve(data, silent=True, verbose=False):
    """Convert light curves returned via API into pandas DataFrames.

    This is a generic function which receives light curves returned by
    the API, which have a fixed form, and converts them into pandas
    DataFrames for ease of use.

    Parameters
    ----------

    data : dict The data decoded from JSON.

    silent : bool   Whether to suppress all output (default: True).

    verbose : bool  Whether to write lots of output (default: False).
        silent : bool Whether to suppress all output.

    Return
    ------
    pandas.DataFrame

    """
    ret = {}

    for key in data["datasets"]:
        tmpKey = f"{key}Data"
        if tmpKey not in data:
            raise RuntimeError(f"Expected to find `{key}` data, but it is not present.")
        if "columns" not in data[tmpKey]:
            raise RuntimeError(f"`{key}` contains no column information.")
        if "columns" not in data[tmpKey]:
            raise RuntimeError(f"`{key}` contains no data!")
        cols = data[tmpKey]["columns"]

        ret[key] = pd.DataFrame(data[tmpKey]["data"], columns=cols, dtype=float)
        if 'ObsID' in ret[key].columns:
            ret[key]['ObsID'] = ret[key]['ObsID'].apply(lambda x: f"{int(float(str(x).replace('::ObsID=', ''))):011d}")

    if 'TimeSys' in data:
        ret['TimeSys'] = data['TimeSys']
    if 'Binning' in data:
        ret['Binning'] = data['Binning']

    ret['datasets'] = data['datasets']

    return ret
