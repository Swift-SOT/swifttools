"""Module-wide variables and functions.

This file contains some constants and functions which are not intended
for export within the swiftools.ukssdc module, but which are common to
various things within that module. As such it should be considered to
be a 'private' module.

Essentially, this provides some core functionality which is of no use
in isolation but is called by the various classes.

Provided variables.
-------------------

_apiVersion : str  The version of the swifttools.ukssdc API.
    NOTE: This is distinct from the swifttools version, and the 
    xrt_prods or swift_too versions; the various components of
    swifttools each have their own versions, and this is mainly used to
    warn users when there are back-end changes that should require the
    user to update their module.

_apiWarned : bool Whether a warning of an out-of-date module has already
    been issued this session.

APIURL : str The base URL directory for all API uploads.

_urlList : dict A list of possbile commands along with the actual API
    page (URL) to which the request must be submitted.


Provided functions.
-------------------

submitAPICall() - actually submits an API request and checks the result
    is formatted correctly, i.e. the request was succesfully received
    and processed. Raises errors if there are problems.

"""

import requests
import json
import warnings
import math
from distutils.version import StrictVersion
import pandas as pd
from .version import _apiVersion

HAS_ASTROPY = False
try:
    import astropy.coordinates

    HAS_ASTROPY = True
except ImportError:
    pass

_apiWarned = False

APIURL = "https://www.swift.ac.uk/API/main.php"
MAXROWS = 5000

# _funcList = {"getMetadata": "getMetadata", "queryDB": "queryDB", "listObs"}


def submitAPICall(func, data, minKeys=None, verbose=False):
    """Function to submit an API query and do simple validation.

    This function is designed for internal use by codes within the
    swifttools.ukssdc module; it is not intended for public use.

    This is a simple function to submit a specific query to our servers,
    and check that the returned JSON meets some minimum requirements. If
    the http return code is not 200, an 'ERROR' is returned, 'OK' is
    not returned, or a specified set of keys are not returned,
    this will raise an exception. This means that the different calls
    do not have to all check for success.

    Parameters
    ----------
        func : str
            The function to be carried out.
        data : dict
            A dictionary of the data to send as JSON with the request.
        minKeys: tuple
            A list of minimum keys that must be included in the return
            from the server. Default: None. NB, the "OK" key will ALWAYS
            be needed.

    Returns
    -------
        dict
            The set of returned data.

    """
    global _apiWarned

    # if func not in _funcList:
    #     raise ValueError(f"{func} is not a supported API function.")

    data["APIFunc"] = func

    if verbose:
        print(f"Uploading data to {APIURL}")
        print(data)

    sub = requests.post(APIURL, json=data)
    if sub.status_code != 200:
        print("Received HTTP failure from the server.")
        raise RuntimeError(f"An HTTP error occured - HTTP return code {sub.status_code}: {sub.reason}")

    # Pull the returned data into JSON.
    ret = json.loads(sub.text)

    # Check if we need to warn about the API
    if "APIVersion" in ret:
        if (StrictVersion(str(ret["APIVersion"])) > StrictVersion(_apiVersion)) and (not _apiWarned):
            warnings.warn(
                f"WARNING: you are using version {_apiVersion} of the UKSSDC API component; "
                f"the latest version is {ret['APIVersion']}, it would be advisable to update the swifttools module."
            )
            _apiWarned = True

    if verbose:
        print(f"Returned keys: {ret.keys()}")

    # Check for an error:
    if "ERROR" in ret:
        msg = f"An error occurred processing your request. Code {ret['ERROR']}."
        if "ERRORTEXT" in ret:
            msg = msg + f" Message: `{ret['ERRORTEXT']}`"
        raise RuntimeError(msg)

    if "OK" not in ret:
        raise RuntimeError("An unspecified error occured processing your request.")

    if minKeys is not None:
        if verbose:
            print("Checking returned data for required content.")
        bad = []
        for k in minKeys:
            if k not in ret:
                bad.append(k)
        if len(bad) > 0:
            msg = (
                "Several required properties were missing from the data returned by the server.\n"
                "This may mean that your swifttools version is out of date.\n"
                "If you have the latest version, please contact swift-help@leicester.ac.uk. The missing keys are\n"
            )
            msg = msg + ", ".join(bad) + "\n"
            raise RuntimeError(msg)

    # If we got here, then all is OK, so just return the dict we decoded from JSON

    return ret


def manageResults(data, metadata, ssuffix="_s", useAstropy=None, silent=True, verbose=False):
    """Give columns their correct types.

    This should be called on a pandas DataFrame created by the return
    from a query call. It will work through the metdata and convert
    numerical columns to numbers, and datetime columns to datetimes.
    It will also create sexagesimal versions of any coordinate columns.

    Parameters
    ----------

    data : Object   A pandas dataframe with the query result.

    metadata : Object A pandas dataframe with the table metadata.

    ssuffix : str  A suffix to add to column names for sexagesimal
                   coordinates (default: '_s').

    useAstropy : str The suffix for astropy coordinate columns. If None
                     astropy columns will not be created.

    silent : bool Whether to suppress all output.

    verbose : bool Whether to produce verbose output

    """
    # Plan. Go through each column in data; look for its metadata.
    # If FLOAT/INT/NUM then parse_numeric
    # If COORDD / COORDH then convert to sexagesimal and maybe astropy

    if not silent:
        print("Processing the returned data.")

    for c in data.columns:
        # Bit of a hack for angdist:
        action = 0  # 0 = Nothing, 1 = numeric, 2 = datetime, 3 = coordHr 4 = coordDeg
        # if verbose:
        #     print(f"Working on column {c}")
        if c == "_r":
            action = 1
        else:
            thisMD = metadata.loc[metadata["ColName"] == c]
            if len(thisMD) == 0:
                raise ValueError(f"Column {c} is not in metadata, cannot parse data.")
            thisType = thisMD["Type"].tolist()[0]
            if (thisType == "NUM") or (thisType == "FLOAT") or (thisType == "INT"):
                action = 1
            elif thisType == "UTC":
                action = 2
            elif thisType == "COORDH":
                action = 3
            elif thisType == "COORDD":
                action = 4

        if action == 1:
            if verbose:
                print(f"Parsing column {c} as numeric")
            data[c] = pd.to_numeric(data[c])
        elif action == 2:
            if verbose:
                print(f"Parsing column {c} as UTC Data")
            data[c] = pd.to_datetime(data[c], yearFirst=True)
        elif action == 3:
            scol = f"{c}{ssuffix}"
            if verbose:
                print(f"Parsing column {c} as coordinate, creating sexagesimal column `{scol}`")
            data[c] = pd.to_numeric(data[c])
            data[scol] = data[c].apply(lambda a: ra2sex(float(a)))
            if useAstropy is not None:
                scol = f"{c}{useAstropy}"
                if verbose:
                    print(f"Creating astropy.coordinates.Angle column `{scol}`")
                data[scol] = data[c].apply(lambda a: makeAng(a))
        elif action == 4:
            scol = f"{c}{ssuffix}"
            if verbose:
                print(f"Parsing column {c} as coordinate, creating sexagesimal column `{scol}`")
            data[c] = pd.to_numeric(data[c])
            data[scol] = data[c].apply(lambda a: dec2sex(float(a)))
            if useAstropy is not None:
                scol = f"{c}{useAstropy}"
                if verbose:
                    print(f"Creating astropy.coordinates.Angle column `{scol}`")
                data[scol] = data[c].apply(lambda a: makeAng(a))


def makeAng(a):
    b = astropy.coordinates.Angle(a, unit="deg")
    return b


def makeSex(dec):
    """Convert angle from decimal to sexagesimal.

    Paramters
    ---------
        dec : float The decimal angle.

    Return
    ------
        list : The sexagesimal angle (d, m, s)
    """

    neg = False
    if dec < 0:
        neg = True

    dec = abs(dec)
    d = math.floor(dec)
    dec = (dec - d) * 60
    m = math.floor(dec)
    dec = (dec - m) * 60

    d = f"{d:02d}"
    if neg:
        d = f"-{d}"
    else:
        d = f"+{d}"

    m = f"{m:02d}"

    sex = [d, m, dec]
    return sex


def ra2sex(RA):
    """Convert RA decimal coordinate to sexagesimal.

    Parameters
    ----------
        RA : float The decimal angle

    Return
    ------
        str : The sexagesimal angle.

    """
    RA = RA / 15.0  # To hours
    sex = makeSex(RA)
    return f"{sex[0]}h {sex[1]}m {sex[2]:0.2f}s"


def dec2sex(dec):
    """Convert dec decimal coordinate to sexagesimal.

    Parameters
    ----------
        dec : float The decimal angle

    Return
    ------
        str : The sexagesimal angle.

    """
    sex = makeSex(dec)
    return f"{sex[0]}d {sex[1]}m {sex[2]:0.1f}s"
