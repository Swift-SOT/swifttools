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



Provided functions.
-------------------

submitAPICall() - actually submits an API request and checks the result
    is formatted correctly, i.e. the request was succesfully received
    and processed. Raises errors if there are problems.

"""

__docformat__ = "restructedtext en"


import requests
import json
import warnings
import math
import os
import numpy as np
import pandas as pd
from distutils.version import StrictVersion
from .version import _apiVersion


SXPS_BAND_NAMES = ("Total", "Soft", "Medium", "Hard")

HAS_ASTROPY = False
try:
    import astropy.coordinates

    HAS_ASTROPY = True
except ImportError:
    pass

HAS_ASTROQ = False
try:
    import astroquery  # noqa

    HAS_ASTROQ = True
except ImportError:
    pass


_apiWarned = False

APIURL = "https://www.swift.ac.uk/API/main.php"


# _funcList = {"getMetadata": "getMetadata", "queryDB": "queryDB", "listObs"}


def submitAPICall(func, data, minKeys=None, skipErrors=False, verbose=False):
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

        skipErrors : bool, optional
            Whether to ignore any errors (default ``False``)

        minKeys: tuple, optonal
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
    data["APIVersion"] = _apiVersion

    if verbose:
        print(f"Uploading data to {APIURL}")
    #        print(data)

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
    if "ERROR" in ret and not skipErrors:
        msg = f"An error occurred processing your request. Code {ret['ERROR']}."
        if "ERRORTEXT" in ret:
            msg = msg + f" Message: `{ret['ERRORTEXT']}`"
        raise RuntimeError(msg)

    if "OK" not in ret and not skipErrors:
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
    # but first remove the keys we've handled.
    if not skipErrors:
        ret.pop("OK", None)
    ret.pop("APIVersion", None)

    return ret


def _createDir(destDir, silent=True, verbose=None):
    """Internal function to make a directory.

    Parameters
    ----------

    destDir : str
        Directory path

    silent : bool, optional
        Whether to suppress all output (default: ``True``).

    verbose : bool, optional
        Whether to write verbose output (default: ``False``).

    """
    if not os.path.isdir(destDir):
        if not silent:
            print(f"Making directory {destDir}")
        os.mkdir(destDir)
        if not os.path.isdir(destDir):
            raise RuntimeError(f"Cannot make directory {destDir}")


def makeAng(a):
    """Convert an angle into an astropy.coordinates.angle object."""
    if math.isnan(a):
        return None
    b = astropy.coordinates.Angle(a, unit="deg")
    return b


def makeSex(dec):
    """Convert angle from decimal to sexagesimal.

    Parameters
    ----------
    dec : float
        The decimal angle.

    Returns
    -------
    list
        The sexagesimal angle (d, m, s)

    """
    if math.isnan(dec):
        return None
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
    if math.isnan(RA):
        return None
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
    if math.isnan(dec):
        return None
    sex = makeSex(dec)
    return f"{sex[0]}d {sex[1]}m {sex[2]:0.1f}s"


def plotLightCurve(
    lcData,
    xlog=False,
    ylog=False,
    whichCurves=None,
    fileName=None,
    T0=None,
    xlabel=None,
    ylabel=None,
    cols={},
    clobber=False,
    fig=None,
    ax=None,
    silent=True,
    verbose=False,
    oldAPI=False,
):
    """Create a plot of the light curve, if retrieved.

    This creates a basic plot of the suppied light curve, following
    normal XRT procedures.

    Parameters
    ----------

    lcData : dict
        A 'light curve ``dict``', in the standard format of the ukssdc
        module.

    xlog : bool, optional
        Whether to plot with the x axis logarithmic (default: ``False``)

    ylog : bool, optional
        Whether to plot with the y axis logarithmic (default: ``False``)

    whichCurves : list or tuple, optional
        If supplied, contains a subset of the light curve datasets to
        plot. NB, this will still interact with ``nosys`` and ``incbad``
        so if you set ``whichCurves=('PC_incbad',)`` but also
        ``incbad=False``, no data will be plotted.

    fileName : str, optional
        If ``None``, the light curve is plotted to screen, otherwise
        the light curve plot is saved to the specified file
        (default: ``None``).

    T0 : float, optional
        The T0 value, to use on the x-axis label.

    xlabel : str, optional
        The x-axis label (will be auto-set if not supplied.)

    ylabel : str, optional
        The y-axis label (will be auto-set if not supplied.)

    cols : dict, optional
        The colours to use for the data; should have keys: WT and PC.

    clobber : bool, optional
        Whether to overwrite the file if it exists (default ``False``).

    fig: matplotlib.figure.Figure, optional:
        A `matplotlib.figure.Figure` instance to use for the plotting.

    ax : matplotlib.axes._subplots.AxesSubplot, optonal
        A `matplotlib.axes._subplots.AxesSubplot` instance to use for
        plotting.

    silent : bool
        Whether to suppress all console output (default: ``True``).

    verbose : bool
        Whether to give verbose output for everything
        (default: ``False``).

    oldAPI : bool, optional
        Internal parameter, identifying if the lc columns are from an
        old version of the API.

    Returns
    -------
    fix,ax
        The objects containing the figure, created by
        ``matplolib.pyplot.subplots()``.

    """
    if verbose:
        silent = False

    if lcData is None:
        raise RuntimeError("No light curve has been supplied")

    if "Datasets" not in lcData:
        raise ValueError("Supplied lcData is not a light curve dict.")

    if whichCurves is None:
        whichCurves = lcData["Datasets"]

    if (fileName is not None) and (not clobber) and os.path.exists(fileName):
        raise RuntimeError(f"File `{fileName}` exists and clobber is False.")

    import matplotlib.pyplot as plt
    import numpy as np

    if (fig is None) or (ax is None):
        if verbose:
            print("Creating new subplot object")
        fig, ax = plt.subplots()

    # Another stupid hack because of bad old column names
    tneg = "TimeNeg"
    tpos = "TimePos"
    rneg = "RateNeg"
    rpos = "RatePos"
    ulCol = "UpperLimit"
    if oldAPI:
        tneg = "T_-ve"
        tpos = "T_+ve"
        rneg = "Rateneg"
        rpos = "Ratepos"
        ulCol = "Rate"

    hadRate = False
    hadHR = False

    if "WT" not in cols:
        cols["WT"] = "blue"

    if "PC" not in cols:
        cols["PC"] = "red"

    if "other" not in cols:
        cols["other"] = "red"

    # Have to work out which PC and WT datasets to use.
    for ds in whichCurves:
        if ds in cols:
            colour = cols[ds]
            label = ds
        elif "wt" in ds.lower():
            colour = cols["WT"]
            label = "WT"
        elif "pc" in ds.lower():
            colour = cols["PC"]
            label = "PC"
        else:
            colour = cols["other"]
            label = ds

        if "UL" in ds:
            hadRate = True
            if not silent:
                print(f"Plotting {ds} as upper limits")
            empty = np.zeros(len(lcData[ds]["Time"]))
            ulSize = np.zeros(len(lcData[ds]["Time"])) + 0.002
            ax.errorbar(
                lcData[ds]["Time"],
                lcData[ds][ulCol],
                xerr=[-lcData[ds][tneg], lcData[ds][tpos]],
                yerr=[ulSize, empty],
                uplims=True,
                elinewidth=1.0,
                color=colour,
                label=label,
                zorder=5,
                fmt="none",
            )

        elif "HR" in ds:
            hadHR = True
            if not silent:
                print(f"Plotting {ds} as a hardness ratio")
            trneg = "HRNeg"
            trpos = "HRPos"
            if (trneg not in lcData[ds].columns) and ("HRErr" in lcData[ds].columns):
                trneg = "HRErr"
                trpos = "HRErr"

            ax.errorbar(
                lcData[ds]["Time"],
                lcData[ds]["HR"],
                xerr=[-lcData[ds][tneg], lcData[ds][tpos]],
                yerr=[-lcData[ds][trneg], lcData[ds][trpos]],
                fmt=".",
                elinewidth=1.0,
                color=colour,
                label=label,
                zorder=5,
            )

        else:
            hadRate = True
            if not silent:
                print(f"Plotting {ds} as rates")
            trneg = rneg
            trpos = rpos
            if (trneg not in lcData[ds].columns) and ("RateErr" in lcData[ds].columns):
                trneg = "RateErr"
                trpos = "RateErr"

            ax.errorbar(
                lcData[ds]["Time"],
                lcData[ds]["Rate"],
                xerr=[-lcData[ds][tneg], lcData[ds][tpos]],
                yerr=[-lcData[ds][trneg], lcData[ds][trpos]],
                fmt=".",
                elinewidth=1.0,
                color=colour,
                label=label,
                zorder=5,
            )

    if xlog:
        ax.set_xscale("log")
    if ylog:
        ax.set_yscale("log")

    # See if we can make some nice axis labels
    if xlabel is None:
        xlabel = lcData["TimeFormat"]
        if "met" in lcData["TimeFormat"].lower():
            if T0 is not None:
                xlabel = f"Time since MET={T0} (s)"
            else:
                xlabel = "Time (s)"

    if ylabel is None:
        ylabel = "Count rate"
        if hadHR:
            if hadRate:
                ylabel = "Count rate or HR"
            else:
                ylabel = "Hardness ratio"

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    if fileName is None:
        plt.show()
    else:
        if verbose:
            print(f"Saving file {fileName}")
        plt.savefig(fileName)

    return fig, ax


def bayesRate(N, B, conf):
    """Calculate source brightness using Krafr, Burrows & Nousek 1991.

    This function receives the number of measured counts from some
    extraction, the number of expected background counts in the same
    location and a confidence level; it then return the mean number of
    source counts and the lower and upper bounds at the supplied
    confidence level.


    Parameters
    ----------

    N : int
        The number of counts in the source region.

    B : float
        The expected number of background counts.

    conf : float
        The confidence interval

    Returns
    -------
    list
        (min, max, mean)

    """
    if conf > 1:
        conf = conf / 100.0

    srcdim = 1000000
    srcstp = 0.001

    if N == 0:
        nlower = 0
        nupper = int(B * 1.1)
        if nupper < 30:
            nupper = 30
    else:
        tmp = int(N - B)
        if tmp < 0:
            tmp = 0
        nlower = tmp - 20 * tmp**0.5
        if nlower < 0:
            nlower = 0
        nupper = N + 20 * N**0.5
        if nupper < B:
            nupper = int(B * 1.1)
            if nupper < 30:
                nupper = 30

    mean = B + np.arange(nlower, nupper, srcstp)
    srcdim = len(mean) - 1

    # Calculate probability distribution
    if N > 0:
        alpha = -mean + N * np.log(mean) - math.log(math.factorial(N))
    else:
        alpha = -mean
    psrc = np.exp(alpha)

    # Peak and index of peak
    pmax = max(psrc)
    nmax = psrc.tolist().index(pmax)

    # Normalize distribution
    t = sum(psrc) - psrc[0]
    area = ((psrc[0] + psrc[srcdim]) / 2.0) + t
    t = 0.0
    psrc = psrc / area

    nupper = nmax
    nlower = nmax
    area = 0.0

    for i in [1, 2]:
        if psrc[nlower] == 0:
            nupper = nupper + 1
        elif psrc[nlower - 1] >= psrc[nupper + 1]:
            nlower = nlower - 1
        else:
            nupper = nupper + 1

    # By starting at the most probable
    # value and integrating in both directions,
    # always choosing to sum the side with the higher
    # probability, we can guarantee that the
    # confence interval chosen is the smallest
    # possible one.

    area = (psrc[nupper] + psrc[nlower]) / 2 + psrc[nlower + 1]

    for i in range(srcdim - 3):
        if nlower == 0:
            nupper = nupper + 1
            area = area + (psrc[nupper - 1] + psrc[nupper]) / 2
        else:
            if psrc[nlower - 1] >= psrc[nupper + 1]:
                nlower = nlower - 1
                area = area + (psrc[nlower + 1] + psrc[nlower]) / 2
            else:
                nupper = nupper + 1
                area = area + (psrc[nupper - 1] + psrc[nupper]) / 2

        if area >= conf:
            # Upper and lower limits are converted
            # into source rates.
            Smax = mean[nupper] - B  # nupper * srcstp
            Smin = mean[nlower] - B  # * srcstp
            return [Smin, Smax, nmax * srcstp]


def mergeLightCurveBins(
    lc,
    rows=None,
    remove=False,
    insert=False,
    forceRate=False,
    forceUL=False,
    ulConf=0.997,
    detThresh=None,
    silent=True,
    verbose=False,
):
    """Merge bins in a light curve.

    This function allows you to combine bins (rows) in a light curve;
    this is not the same as rebinning, where all bins are recalcuated,
    but rather for merging a subset of data. For example, if a
    light curve shows a series of consecutive upper limits that you want
    to merge, while leaving the rest of the light curve unaffected.

    This uses the Bayesian (Kraft, Burrows & Nousek 1991) method to
    find rates / limits, so if bins that combine to contain large
    numbers of counts are provided, performance may be poor. This may be
    reconsidered in future if use cases for merging bins with many
    counts are presented to the developers.

    The default behaviour of this function is to return a pandas Series
    containing the entry for the new bin, and to remove the old bins
    (that have been merged) from the light curve that you supplied.
    You can modify this using the arguments below, using ``remove`` to
    determine whether the merged bins are removed, and ``insert`` to
    add the new row to your light curve.

    NOTE: By default, this function will decide for itself whether to
    produce a (3-sigma) upper limit, or a count-rate with (1-sigma)
    error-bars, depending on whether then new bin has a 3-sigma lower
    limit above zero. You can determine what was produced by checking
    whether the returned Series contains the 'UpperLimit' or 'Rate' key.
    If you specify ``insert=True`` this will not happen, instead the bin
    will be forced to match the supplied light curve, i.e. it will be an
    upper limit if the light curve was one of upper limits, or a rate
    otherwise -- regardless of whether the bin constitutes a detetions.
    You can also use the ``force*`` arguments to control the type of bin
    created, but these are ignored if ``insert`` is ``True``.

    NOTE: The sigma value is not set by this method, as it requires
    knowledge of the relative sizes of the source and background regions
    which is not contained in the light curve file.

    Parameters
    ----------

    lc : pandas.DataFrame
        The light curve to work on

    rows : pandas.Series, optional
        A pandas series defining the rows to merge. If not supplied,
        all are merged.

    remove : bool, optional
        Whether to remove the merged lines from the light curve, as
        well as adding the new result (default: ``False``).

    insert : bool or str, optional
        Whether to add the new entry to the light curve. If ``True``
        the entry will be added to your light curve DataFrame.
        If ``False``, it will not be added, and this function will
        return the new entry.
        If 'match' it will only be added if it is the right `type`, i.e.
        if the merged bin is an upper limit, it will be added if the
        original light curve was of upper limits and the converse for a
        detection.

        **Warning** if ``insert`` is ``True`` then the type of bin
        created from the merge (rate or upper limit) will be forced to
        match that of the supplied light curve - and no test is done to
        determine if this is appropriate.

        (Default: ``False``).

    forceRate : bool, optional
        Return a count-rate and 1-sigma error, whether the data
        constitute a detection or not (default: ``False``).

    forceUL : bool, optional
        Return a 3-sigma upper limits, whether the data constitute a
        detection or not (default: ``False``).

    ulConf : float, optional
        The confidence level at which the upper limit should be
        determined, should be a probability (0-1); if >1 is assumed to
        be a percentage  (default: 0.997).

    detThresh : float or None, optional
        The probability threshold at which the count-rate is >0 for a
        detection to be determined (only used if ``detectionsAsRates``
        is ``True``). If ``None`` then this is set to ``conf``
        (default: ``None``).

    silent : bool
        Whether to suppress all console output (default: ``True``).

    verbose : bool
        Whether to give verbose output for everything
        (default: ``False``).


    Returns
    -------
    list
        The returned list has 3 entries (isUL, inserted, newData)

        'isUL' is a `bool` indicating whether the new bin is an upper
        limit.

        'inserted' is a `bool` indicating whether the new bin has been
        inserted into the supplied light curve.

        'newData' is a pandas Series containing the new bin.

    """
    if verbose:
        silent = False

    if forceRate and forceUL:
        raise RuntimeError("You can't force an upper limit and a rate!")

    if isinstance(insert, str):
        insert = insert.lower()
    if (insert is not True) and (insert is not False) and (insert != "match"):
        raise ValueError("Insert must be a boolean or 'match")

    if (insert is True) and (forceRate or forceUL) and not silent:
        if forceRate:
            print("WARNING: Ignoring `forceRate` as insert=True")
        else:
            print("WARNING: Ignoring `forceUL` as insert=True")

    if not isinstance(ulConf, float):
        raise ValueError("`conf` parameter must be a float!")
    if ulConf > 1:
        if verbose:
            print(f"Interpreting conf={ulConf} as a percentage")
        ulConf = ulConf / 100.0

    dtIsC = False

    if detThresh is None:
        detThresh = ulConf
        dtIsC = True
    else:
        if not isinstance(detThresh, float):
            raise ValueError("`detThresh` parameter must be a float!")
        if detThresh > 1:
            if verbose:
                print(f"Interpreting detThresh={detThresh} as a percentage")
            detThresh = detThresh / 100.0

    # If we have upper limits we have to weight CF by exposure,
    # otherwise by counts.
    isOrigUL = False
    sumCol = "CtsInSrc"
    if "UpperLimit" in lc.columns:
        isOrigUL = True
        sumCol = "Exposure"

    tmp = []
    if rows is None:
        tmp = lc.copy()
    else:
        tmp = lc[rows].copy()

    # Need to calculate some new columns.
    # CFE = CF * E, will need this for the new CF
    tmp["CFE"] = tmp["CorrFact"] * tmp[sumCol]
    # Start and stop to get new time
    tmp["START"] = tmp["Time"] + tmp["TimeNeg"]
    tmp["STOP"] = tmp["Time"] + tmp["TimePos"]
    # Need BGRate and error.
    # These will be the current bins' exposure-weighted mean, but for
    # error should add in quadature, so need err**2
    tmp["BGRSQ"] = tmp["BGerr"] ** 2
    tmp["BGE"] = tmp["BGrate"] * tmp["Exposure"]
    tmp["BGErrE"] = tmp["BGRSQ"] * tmp["Exposure"]

    # Now calculate the values for the new bin
    E = tmp["Exposure"].sum()
    C = int(tmp["CtsInSrc"].sum())
    B = tmp["BGInSrc"].sum()
    CFE = tmp["CFE"].sum()
    weight = tmp[sumCol].sum()
    CF = CFE / weight

    # And time properities

    meanT = tmp["Time"].mean()
    startT = tmp["START"].min()
    stopT = tmp["STOP"].max()
    dur = stopT - startT
    tPos = stopT - meanT
    tNeg = startT - meanT
    fracExp = E / dur

    # And background properties
    bgRate = tmp["BGE"].sum() / E
    bgErr = math.sqrt(tmp["BGErrE"].sum()) / E

    # # And remove the temporary columns
    # NO NEED - they are in tmp. Only reinstate this if I need to.
    # lc.drop(["CFE"], axis=1, inplace=True)
    # lc.drop(["START"], axis=1, inplace=True)
    # lc.drop(["STOP"], axis=1, inplace=True)

    # Do we need a rate or UL? Or is it up to me to decide?
    # If force* is set, we do not decide.
    # If insert it set, we do not decide.
    # Otherwise we do.
    # Let's some some variables also to track what we need, and what
    # we got
    getUL = None
    UL = None
    gotUL = False
    if insert is True:
        getUL = isOrigUL
    elif forceRate:
        getUL = False
    elif forceUL:
        getUL = True
    else:
        if verbose:
            print("Checking whether the new bin is a detection.")
        (smin, smax, mean) = bayesRate(C, B, detThresh)
        if dtIsC:
            gotUL = True
        UL = smax * CF / E
        if smin > 0:
            getUL = False
            if not silent:
                print("The new bin is a detection")
        else:
            getUL = True
            if not silent:
                print("The new bin is an upper limit")

    # Create variable for the new bin
    newRow = {
        "Time": meanT,
        "TimePos": tPos,
        "TimeNeg": tNeg,
        "RatePos": 0,
        "RateNeg": 0,
        "FracExp": fracExp,
        "BGRate": bgRate,
        "BGErr": bgErr,
        "CorrFact": CF,
        "CtsInSrc": C,
        "BGInSrc": B,
        "Exposure": E,
        "Sigma": math.nan,
        "SNR": 0,
    }

    newIndex = [
        "Time",
        "TimePos",
        "TimeNeg",
        "HOLDER",
        "RatePos",
        "RateNeg",
        "FracExp",
        "BGRate",
        "BGErr",
        "CorrFact",
        "CtsInSrc",
        "BGInSrc",
        "Exposure",
        "Sigma",
        "SNR",
    ]

    # Are we finding an UL?
    if getUL:
        # If we haven't already found it, get it.
        if not gotUL:
            (smin, smax, mean) = bayesRate(C, B, ulConf)
            UL = smax * CF / E
        # Create new row with UL
        newRow["UpperLimit"] = UL
        newIndex[3] = "UpperLimit"

    # If we need a rate, get it:
    if not getUL:
        (smin, smax, mean) = bayesRate(C, B, 0.683)
        rate = mean * CF / E
        neg = (smin - mean) * CF / E
        pos = (smax - mean) * CF / E
        snr = rate / abs(neg)
        # Create new row with rate
        newRow["Rate"] = rate
        newRow["RatePos"] = pos
        newRow["RateNeg"] = neg
        newRow["SNR"] = snr
        newIndex[3] = "Rate"

    newData = pd.Series(newRow, index=newIndex)

    if remove:
        lc.drop(tmp.index, inplace=True)

    # If insert is True we save this row.
    # If insert is "match" we save it if it is the same format as the
    # existing table.
    inserted = False
    if (insert is True) or ((insert == "match") and (getUL == isOrigUL)):
        if verbose:
            print("Inserting merged bin into the light curve.")
        lc.loc[-1] = newData
        inserted = True

    lc.sort_values(
        by=[
            "Time",
        ],
        axis=0,
        inplace=True,
    )

    lc.reset_index(drop=True, inplace=True)

    return (getUL, inserted, newData)


def mergeUpperLimits(
    ultab, rows=None, detectionsAsRates=True, bands="all", conf=0.997, detThresh=None, silent=True, verbose=False
):
    """Merge rows in an upper limit table returned.

    This function allows you to combine rows in a set of upper limits
    returned by the uds.getUpperLimits() function.

    This uses the Bayesian (Kraft, Burrows & Nousek 1991) method to
    find rates / limits, so if bins that combine to contain large
    numbers of counts are provided, performance may be poor. This may be
    reconsidered in future if use cases for merging bins with many
    counts are presented to the developers.

    This returns a single `dict` with the upper limit and/or rate,
    along with the error and the details of the counts, bg counts etc.

    Parameters
    ----------

    ultab : pandas.DataFrame
        The upper limit result to work on

    rows : pandas.Series, optional
        A pandas series defining the rows to merge. If not supplied,
        all are merged.

    detectionsAsRates : bool, optional
        Whether to check if the source is actually detected (i.e. has a
        lower confidence bound >0) in the merged result. If ``True``
        then, the {band}Rate, {band}_RatePos, {band}_RateNeg and
        {band}_RateIsDetected columns will be returned; the former three
        will be NaN  if the source is not detected (default: `True``).

    bands : str or list or tuple, optional
        Which bands to calculate the merged result for. If 'all' then
        all bands are processed. Note: if bands are selected but not
        supplied in the ultab, they will be skipped.

    conf : float, optional
        The confidence level at which the upper limit should be
        determined, should be a probability (0-1); if >1 is assumed to
        be a percentage  (default: 0.997).

    detThresh : float or None, optional
        The probability threshold at which the count-rate is >0 for a
        detection to be determined (only used if ``detectionsAsRates``
        is ``True``). If ``None`` then this is set to ``conf``
        (default: ``None``).

    silent : bool
        Whether to suppress all console output (default: ``True``).

    verbose : bool
        Whether to give verbose output for everything
        (default: ``False``).


    Returns
    -------
    dict
        The dictionary of results.

    """
    if verbose:
        silent = False

    if not isinstance(conf, float):
        raise ValueError("`conf` parameter must be a float!")
    if conf > 1:
        if verbose:
            print(f"Interpreting conf={conf} as a percentage")
        conf = conf / 100.0

    if detThresh is None:
        detThresh = conf
    else:
        if not isinstance(detThresh, float):
            raise ValueError("`detThresh` parameter must be a float!")
        if detThresh > 1:
            if verbose:
                print(f"Interpreting detThresh={detThresh} as a percentage")
            detThresh = detThresh / 100.0

    useBands = []
    if isinstance(bands, str):
        if bands.lower() == "all":
            useBands = SXPS_BAND_NAMES
        else:
            tb = bands[0].upper() + bands[1:].lower()
            if tb not in SXPS_BAND_NAMES:
                raise ValueError(f"Band `{tb}` is not recognised")
            useBands = [
                tb,
            ]
    elif isinstance(bands, (tuple, list)):
        for b in bands:
            tb = b[0].upper() + b[1:].lower()
            if tb not in SXPS_BAND_NAMES:
                raise ValueError(f"Band `{tb}` is not recognised")
            useBands.append(tb)

    tmp = []
    if rows is None:
        tmp = ultab.copy()
    else:
        tmp = ultab[rows].copy()

    needCols = ("SourceExposure", "ImageExposure")
    for c in needCols:
        if c not in tmp.columns:
            raise ValueError(f"Column `{c}` is mandatory but not in your supplied data frame")
    totSourceExp = tmp["SourceExposure"].sum()
    totImExp = tmp["ImageExposure"].sum()

    ret = {"SourceExposure": totSourceExp, "ImageExposure": totImExp}

    needCols = ("Counts", "BGCounts", "CorrectionFactor")
    for b in useBands:
        # First, do we have all of the columns?
        gotAll = True
        for c in needCols:

            if f"{b}_{c}" not in tmp.columns:
                gotAll = False
                break
        if not gotAll:
            if not silent:
                print(f"Skipping band `{b}` as data are missing")
            continue

        tmp[f"{b}_CFE"] = tmp[f"{b}_CorrectionFactor"] * tmp["ImageExposure"]

        totC = int(tmp[f"{b}_Counts"].sum())
        totB = tmp[f"{b}_BGCounts"].sum()
        CF = tmp[f"{b}_CFE"].sum() / totImExp

        # Don't want to do unneeded calls.
        # So, if we have to check det, do that first.
        # If it is undetected, and conf == detThresh then no need to
        # recalc.
        # Otherwise, getUL
        # Get Rate if rates are req or detected.
        ul = None
        isDet = False
        rate = math.nan
        ratePos = math.nan
        rateNeg = math.nan
        if detectionsAsRates:
            # Check detection
            (smin, smax, mean) = bayesRate(totC, totB, detThresh)
            # If detThresh == conf then we've also already got the UL so save it
            if detThresh == conf:
                ul = smax * CF / totImExp

            # Now get the rate if we need it
            if smin > 0:  # Detection
                if not silent:
                    print("Merge gives a detection.")
                isDet = True
                # Get rate and errors:
                (smin, smax, mean) = bayesRate(totC, totB, 0.683)
                rate = mean * CF / totImExp
                rateNeg = (smin - mean) * CF / totImExp
                ratePos = (smax - mean) * CF / totImExp
            elif not silent:
                print(f"Merge does not give a detection in band {b}.")

        if ul is None:  # Haven't got UL. Always get UL
            (smin, smax, mean) = bayesRate(totC, totB, conf)
            ul = smax * CF / totImExp
        ret[f"{b}_UpperLimit"] = ul
        ret[f"{b}_Counts"] = totC
        ret[f"{b}_BGCounts"] = totB
        ret[f"{b}_CorrectionFactor"] = CF
        if detectionsAsRates:
            ret[f"{b}_Rate"] = rate
            ret[f"{b}_RatePos"] = ratePos
            ret[f"{b}_RateNeg"] = rateNeg
            ret[f"{b}_IsDetected"] = isDet

    return ret
