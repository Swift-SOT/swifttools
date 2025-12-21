# Common module-level functions

There are a handful of functions which are called by various elements of the `swifttools.ukssdc` module, so rather than documenting them every time they appear, they are introduced here, and I will link back here in the other documentation as and when these functions are used.

In most cases, you will never actually call these functions direct (indeed, they're not exported into any of the module namespaces&dagger;), but the functions that you do use will ultimately make use of these functions, passing on appropriate arguments; those arguments usually appear as `**kwargs` in the docstrings of the functions you are calling. The purpose of this page is to introduce those arguments so you know what they mean.

Because these functions are not intended to be called directly, to demonstrate them I will use the [`swifttools.ukssdc.data.GRB` module](data/GRB.ipynb), but it's the common behaviour I'm trying to show.

The handful of functions you can call direct are documented at the end of this page.

(&dagger; Just to be awkward, there is one function which doesn't fall into this divide. `plotLightCurve()` is directly available if you want it, but equally the various modules in this package all provide wrappers to it).

## Page contents

* [General notes](#general-notes)
* [Functions called indirectly](#indirect)
    * [`getLightCurve()`](#getlightcurve)
    * [`saveLightCurveFromDict()`](#savelightcurvefromdict)
    * [`plotLightCurve()`](#plotlightcurve)
    * [Rebinning light curves](#rebinning-light-curves)
      * [`rebinLightCurve()`](#rebinlightcurve)
      * [`checkRebinStatus()`](#checkrebinstatus)
      * [`rebinComplete()](#rebinComplete)
      * [`getRebinnedLightCurve()`](#getlightcurve)
    * [`saveSpectrum()`](#savespectrum)
* [Functions you call](#functions-you-call)
    * [`mergeLightCurveBins()`](#mergelightcurvebins)
    * [`mergeUpperLimits()`](#mergeupperlimits)
    * [`bayesRate()`](#bayesrate)


## General notes

Nearly every function takes the following two arguments:

* `silent` - bool: Whether to suppress all output.
* `verbose` - bool: Whether to write lots of output.

These are not listed for each function below.

When using the `data` module, you can supply these to whichever function you are calling and they will
be passed through. If you are using the `query` module then you do not specify these, they are properties
of your query object, and are passed from that. If this makes no sense, it will when you've read about those two modules.

## Functions called indirectly

Let's start with some terminology. These are not (with one exception) functions that you are going to call directly.
You are going to call some function in the `data` or `query` module, and it will itself call these ones, passing
on any relevant arguments you supplied. I am going to refer to the function you actually called as "the parent function"
throughout this page.

With that one exception (`plotLightCurves()`) these functions are not exported into the main namespace; you get at them
through the parent functions, but the parent functions' docstrings don't detail all of the individual arguments that can
get passed through (unless the parent also uses them). That's why I've written this page, but you can get at the docstrings
if you wish, as below:

```python
import testtools.ukssdc.data as ud
help(ud.download._getLightCurve)
```

Note that the function name is `_getLightCurve` - it starts with `_`. For all functions shown in this section (except, again,
`plotLightCurves()`) you can get at the help as above, prepending an underscore to the function name.

---

### `getLightCurve()`

The `getLightCurve()` function is called in cases where you want to, well, get light curves. In all cases (I think)
the parent function is `getLightCurves()` (i.e. almost the same, but in the plural).

This function can download the light curve files from the UKSSDC server and save them to disk and/or it can read the light curve data from the UKSSDC and
store it in a [light curve `dict`](structures.md#the-light-curve-dict). When you call something which uses
`getLightCurve()` you can set the following arguments which are passed through:

* `returnData` - bool: Whether the function should return a light curve `dict`.
* `saveData` - bool: Whether the function should download the light curve files to disk.
* `nosys` - string: Whether to get the data without WT-mode systematics (can be "yes", "no" or "both").
* `incbad` - string: Whether to get the data with unreliable centroids (can be "yes", "no" or "both").
* `clobber` - bool: Whether to overwrite files that already exist.
* `skipErrors` - bool: Whether to continue if an error occurs related to one file.

**Note**: `nosys` and `incbad` relate to specifics of the light curves the UKSSDC tools produce, to learn more, please see [the light curve documentation](https://www.swift.ac.uk/user_objects/lc_docs.php#systematics).

(Small note: at the present time the [`xrt_prods.XRTProductRequest.retrieveLightCurve()` function](xrt_prods/RetrieveProducts.md#retrieve-the-light-curve) does not use this common function, because of the need for that module to support deprecated behaviour. This may change in future. The SXPS parts of the `data` and `query` modules also do not use this for very, very boring reasons, but their options are intentionally as similar as possible to those discussed above).

---

### `saveLightCurveFromDict()`

Some functions let you save a [light curve `dict`](structures.md#the-light-curve-dict) to files. This is slightly different
from saving the light curve data directly from the URLs using `getLightCurve(saveData=True)` as above, and the usage and reasons
for this will be covered in the different modules where we actually employ this functionality. For now, let's just deal with the
function. In most cases this is called by parent functions called `saveLightCurves()`.

Functions that call this can pass through the following arguments:

* `asQDP` - bool: Whether to save in qdp format (overrides `sep` and `suff`)
* `whichDatasets` - list or str: A list of the keys identifying the datasets to save, or 'all'. If not 'all'
then it must be a list, and all of the entries in it must be in the 'Datasets' list of the light curve `dict`.
* `clobber` - bool: Whether to overwrite files that already exist.
* `header` - bool: Whether to print a header row with the column names.
* `sep` : string: A single-character string to use as the column separator.
* `suff` : string or `None`: The suffix for output files to use. If `None` then it will be "qdp" if `asQDP`
is `True`, otherwise ".dat".
* `timeFormatInFname` - bool: Whether the filename should include the time format of the light curve.
* `binningInFname` - bool: Whether the filename should include the binning method of the light curve.
* `skipErrors` - bool: Whether to continue if an error occurs related to one file.

---


### `plotLightCurve()`

This is the one function which you can call directly or indirectly. For those objects which can store light curves internally
([`XRTProductRequest`](xrt_prods/README.md), [`GRBQuery`](query/GRB.md), [`SXPSQuery`](query/SXPS.md)) a wrapper function is
provided, for light curves you store in your own variables (e.g. those obtained via the [`swifttools.ukssdc.data`](data.md) module)
you call the function directly. I have documented it in this section as it fits with the two functions above, I think.

To call the function directly you will first need to import it, e.g.

```python
from swifttools.ukssdc import plotLightCurve
```

And its arguments are:

* `lcData` - `dict`: This is a position argument (i.e. must come first, does not need the argument name specifying),
and should be a valid [light curve `dict`](structures.md#the-light-curve-dict).
* `xlog` - `bool`: Whether to plot with the x axis logarithmic (default: ``False``)
* `ylog` - `bool`: Whether to plot with the y axis logarithmic (default: ``False``)
* `whichCurves` - list or tuple: If supplied, contains a subset of the light curve datasets to
plot. Everything given in here should be an entry in the `Datasets` list of the `lcData` `dict`.
* `fileName` - string: If supplied, the light curve plot is saved to the specified file instead of being
plotted to screen (NB, in Jupyter it appears to be plotted to screen as well).
* `T0` : `float` - If supplied, the T0 value to include in the label for the x axis label.
* `xlabel` : string - The x-axis label (will be auto-set if not supplied).
* `ylabel` : string - The y-axis label (will be auto-set if not supplied).
* `cols` : `dict` - An optional `dict` specifying the colours to be used in plotting. The keys can be
`PC`, `WT` (specifying the colours for the two XRT modes), any entry in the `Datasets` list of `lcData`, or `other`.
The values are valid `matplotlib` colours.
* `clobber` - `bool`: If `fileName` was supplied but already exists, should it be overwritten?
* `fig` - `matplotlib.figure.Figure`: An optional existing object (to be supplied along with `ax`, below)
to plot on.
* `ax` - `matplotlib.axes._subplots.AxesSubplot`: An optional existing object (to be supplied along with `fig`, above)
to plot on.


**Note** If you call this via one of the class functions (called `plotLightCurve()` everywhere except in
`XRTProductRequest`, where it is `plotLC()` for backwards compatibility), the first, positional argument
(`lcDict`) is removed or replaced; see the relevant class documentation for details.

This function uses `matplotlib.pyplot` and uses the `subplots()` function. This returns two arguments which
in `matplotlib` conventions are stored as `fig` and `ax`, and are the outputs of `subplots()`. These are returned
so that you can carry out subsequent manipulation, but you can also pass those objects into the call, if you want
to plot on an existing canvas you have created, or (for example), plot multiple light curves on the same plot using
this function - examples of this appear in various of the documentation pages herein.

---

### Rebinning light curves

Both the [`swifttools.ukssdc.data.GRB`](data/GRB.md) and [`swifttools.ukssdc.xrt_prods`](xrt_prods/RetrieveProducts.md) modules
give you the option to rebin a light curve. These use a series of common functions which are documented here; for a worked
example see [the `data.GRB` documentation](data/GRB.md#rebin).

There are a few functions, first the actual function to request rebinning, then functions to check on the status of the rebinning
job and to get the products. These are all wrapped by functions of the same name in the module you are using, so as above I will just
detail the arguments that you set, that get passed through to these functions, and anything they return.

One **important note** before I proceed though: in what follows below I have noted that the request to rebin a curve returns a job ID, and
that you then have to pass this to the other functions. *This is not true for the `XRTProductRequest` object*. In that case, the
ID is stored in your object, and passing it around is handled internally by the class wrapper functions to those detailed below.

#### `rebinLightCurve()`

`rebinLightCurve()` is the function which requests something be rebinned. There are many arguments that you can supply,
but many of these depends upon how you want the light curve to be binned. This is controlled by the `binMeth` parameter, which is mandatory,
and must be one of:

* 'obsid' - One bin per obsid
* 'snapshot' - One bin per snapshot
* 'time' - Bins are of a fixed duration
* 'counts' - Fixed numbers of counts per bin ('GRB-like').

By a curious coincidence*, all of the other parmeters are identical to the parameters you would set in the `xrt_prods`
module and so [are documented already](https://www.swift.ac.uk/user_objects/API/pyDocs/RequestJob.md#light-curve-parameters) but
I have copied that documentation below, rather than making you jump around too many pages.

One note before you read on though: this function `rebinLightCurve()` returns an integer number which you need to capture in a
variable; this is the identifier for your rebin job, and is necessary for checking if the job is complete, and for getting the light curve.


(* It isn't coincidence.)

##### Arguments for all light curve types

| Parameter | Mandatory? | Type  | Description | Default |
| :----     |  :----:    | :---: | :-----      | :----:  |
| `binMeth` | Yes | str | Which binning method to use. Must be one of {'counts', 'time', 'snapshot', 'obsid'} | -- |
| `minEnergy` | No | float/int | Minimum energy for the main light curve, in keV | 0.3 |
| `maxEnergy` | No | float/int | Maximum energy for the main light curve, in keV | 10 |
| `softLo` | No | float/int | Minimum energy for the soft-band, in keV. Must be &geq;minEnergy | 0.3 |
| `softHi` | No | float/int | Maximum energy for the soft-band, in keV. Must be &leq;maxEnergy | 1.5 |
| `hardLo` | No | float/int | Minimum energy for the hard-band, in keV. Must be &geq;minEnergy | 1.5 |
| `hardHi` | No | float/int | Maximum energy for the hard-band, in keV. Must be &leq;maxEnergy | 10 |
| `minSig` | No | float/int | Minimum significance (in Gaussian &sigma;) for a bin to be considered a detection | 3 |
| `grades` | No | str | What event grades to include. Can be 'all', '0' or '4' | 'all' |
| `allowUL` | No | str | Whether upper limit are allowed. Must be one of {'no' 'pc', 'wt', 'both'}. | 'both' |
| `allowBayes` | No | str | Whether Bayesian bins are allowed. Must be one of {'no' 'pc', 'wt', 'both'}. | 'both' |
| `bayesCounts` | No | float,int | Threshold for counts in a bin, below which to use Bayesian statistics. | 15 |
| `bayesSNR` | No | float,int | Threshold for S/N in a bin, below which to use Bayesian statistics to measure count rate and error.  | 2.4 |
| `timeFormat` | No | str | The units to use on the time axis. Must be one of {'s'(=seconds), 'm'(=MJD)} | 's' |
| `whichData` | No | str | Which observations to use for the light curve. Must be one of {'all', 'user'} | 'all' |
| `useObs` | If `whichData='user'` | str | The specific observations to use to create the light curve [[Details](https://www.swift.ac.uk/user_objects/docs.php#useobs)] |  -- |



##### Arguments for &lsquo;counts&rsquo; binning

&lsquo;Counts&rsquo; binning is where a bin requires a certain number of counts to be considered complete (unless it spans the maximum inter-observation gap). This is the binning method used by the [XRT GRB light curve repository](https://www.swift.ac.uk/xrt_curves).

| Parameter | Mandatory? | Type  | Description | Default |
| :----     |  :----:    | :---: | :-----      | :----:  |
| `pcCounts`  | Yes | int  | Minimum counts in a PC-mode bin for it to be full (at 1 ct/sec if dynamic binning is on) | -- |
| `wtCounts`  | Yes | int  | Minimum counts in a WT-mode bin for it to be full (at 1 ct/sec if dynamic binning is on) | -- |
| `dynamic`   | Yes | bool | Whether dynamic binning is enabled or not | -- |
| `rateFact`  | No  | float,int | Rate factor for dynamic binning | 10. |
| `binFact`  | No  | float,int | Binning factor for dynamic binning | 1.5 |
| `pcBinTime` | No | float,int | Minimum bin duration in PC mode in seconds | 2.51 |
| `wtBinTime` | No | float,int | Minimum bin duration in WT mode in seconds | 0.5 |
| `minCounts` | No | int | The absolute minimum counts/bin that dynamic binning can't fall below, unless the maxgap parameters below force truncation | 15 |
| `minSNR` | No | float,int| The minimum S/N a bin must have to be considered full, unless the maxgap parameters below force truncation | 2.4|
| `pcMaxGap` | No | float,int | The maximum observing gap a PC mode bin can straddle - even if not 'full' it will be stopped at this length (in seconds). | 10<sup>8</sup> |
| `wtMaxGap` | No | float,int | The maximum observing gap a WT mode bin can straddle - even if not 'full' it will be stopped at this length (in seconds). | 10<sup>8</sup> |

##### Arguments for fixed-time binning

| Parameter | Mandatory? | Type  | Description | Default |
| :----     |  :----:    | :---: | :-----      | :----:  |
| `pcBinTime` | No | float,int | Bin duration in PC mode in seconds | 2.51 |
| `wtBinTime` | No | float,int | Bin duration in WT mode in seconds | 0.5 |
| `matchHR`   | No | bool | Whether the hardness ratio should have the same bins as the main curve. | True |
| `pcHRBinTime` | No | float,int | Hardness ratio bin duration in PC mode in seconds | 2.51 |
| `wtHRBinTime` | No | float,int | Hardness ratio bin duration in WT mode in seconds | 0.5 |
| `minFracExp` | No | float,int | Minimum fractional exposure a bin can have, bins with a lower fractional exposure are discarded. | 0. |

The other binning methods have no specific arguments.

#### `checkRebinStatus()`

The `checkRebinStatus` function, well, checks on the status of your rebinning request. If takes a single argument,
which is the jobID, the value returned by [`rebinLightCurve()`](#rebinlightcurve).

It returns a `dict` with two keys. `statusCode` which is a numerical value and `statusText` which is a text description of the status.
The codes are:

* -10 = No status returned by the server. Implies something has gone wrong!
* -4 = The job was cancelled by the user (i.e. you).
* -3 = The product could not be built, the job was called OK, but did not produce a product.
* -2 = An internal error occurred at the UKSSDC, and the attempt to add the job to the queue failed.
* -1 = An internal error occured at the UKSSDC, and the job could not even be requested.
* 1  = Job has been requested, but not yet queued.
* 2  = Job has been entered into our processing queue.
* 3  = The job is actually running (progress information may be available)
* 4  = The job completed OK. Your products are available
* 5  = [Status code only for astrometric positions]: the astrometry is waiting for the standard PSF position to be produced, and will then correct that.

#### `rebinComplete()`

This function simply tells you whether your rebin job is complete. If takes a single argument,
which is the jobID, the value retured by [`rebinLightCurve()`](#rebinlightcurve),
and returns a `bool` (`True` meaning, "Yes, it's complete").

#### `getRebinnedLightCurve()`

This function again just takes a jobID, and literally all it does it then call
[`getLightCurve()`](#getlightcurve), so I will not repeat the documentation for that here, you can [scroll up](#getlightcurve).

---

### `saveSpectrum()`

The ability to save spectral data to disk appears in almost every area of the `swifttools.ukssdc` module, and in each
case it is powered behind the scenes by the same function, described here. There are two things that can be saved
to disk: `gif` images of the spectrum and fit, and `.tar.gz` archives containing the spectral files. The common
arguments passed through to this common function are:

* `specSubDirs` - `bool`: Whether each spectral time-slice ("rname") should be saved in its own subdirectory.
* `saveImages` - `bool`: Whether to save the gif images.
* `saveData` - `bool`: Whether to save the spectral data files.
* `extract` - `bool`: Whether to extract the spectral files from the tar archive.
* `removeTar` - `bool`: Whether to remove the tar file after extracting. **This
parameter is ignored unless ``extract`` is ``True``**.
* `clobber` - `bool`: Whether to overwrite files if they exist.
* `skipErrors` - `bool`: If an error occurs saving a file, do not raise a RuntimeError
but simply continue to the next file (default ``False``).

---

## Functions you call

There are three functions (plus [`plotLightCurve()`, above](#plotlightcurve)) which are designed to be called
directly by you, and no wrappers are supplied. These are all related to combining light curve data.

The first of these, [`mergeLightCurveBins()`](#mergelightcurvebins) is for use with a [light curve
`dict`](structures.md#the-light-curve-dict) and can be applied to datasets containing count-rates or upper limits.

The second, [`mergeUpperLimits()`](#mergeupperlimits) is used for combining upper limits **not** in a light curve `dict`, but
as returned by the [SXPS upper limit tool](data/SXPS.md#ul).

The third, [`bayesRate()`](#bayesrate) is a helper function used by the above, but may be of occasional use to you as well.

All of these are in the `swifttools.ukssdc` module and I recommend using them like this:

```python
import testtools.ukssdc as uk

uk.mergeLightCurveBins(...)
```

etc.

### `mergeLightCurveBins()`

This function is used to combine bins within a single "dataset" within a [light curve
`dict`](structures.md#the-light-curve-dict); for example, you may wish to sum up all upper limits to give the deepest
possible limit, or combine some bins where the source is faint to give smaller errors etc.

**Note** At the present time, this function only allows combining bins within the same "dataset". That is, if
you want to combine some bins from the set of upper limits with some bins from the set of detections you will -- at present --
have to do this yourself.

This function works by summing up the number of counts in the identified bins and the number of expected background
counts, and then using the [`bayesRate()` function](#bayesrate) to determine the number of expected counts (and
confidence interval) using the method of [Kraft, Burrows & Nousek
(1991)](https://ui.adsabs.harvard.edu/abs/1991ApJ...374..344K/abstract). The exposure is also summed across the bins,
and the (exposure-weighted) mean correction factor is found, and the count-rate and confidence interval thus found.

It should be noted that combining bins can change their "type", in particular, combining upper limits can result in a detection.
The `mergeLightCurveBins()` function lets you force the result to be an upper limit, or a count-rate (with 1-sigma errors),
or to determine its type automatically. You can also choose whether the result should be added into the light curve supplied
or not, and whether the bins that have been merged should be removed from the light curve.

`mergeLightCurveBins()` takes the following arguments:

* `lc` - The light curve `DataFrame` to work on. This is a mandatory position argument which must come first.
* `rows` - `pandas.Series`: An optional  `pandas Series` defining the rows to merge. This is best
defined by a `pandas` filter expression as demonstrated for the [`query module subset creation`](query.md#subsets)
* `remove` - `bool`:  Whether to remove from the light curve the bins that have been merged.
* `insert`  - `bool` or 'match': Whether to add the new entry to the light curve. See the note below for more information on
this parameter.
* `forceRate` - `bool`:  Whether to always return a bin containing a count-rate and 1-sigma error, regardless of the properties of the bin.
* `forceUL` - `bool`: Whether to always return a bin containing an 3-sigma upper limit, regardless of the properties of the bin.
* `ulConf` - `float`: The confidence interval at which upper limits should be created (default: 0.997)
* `detThresh` - `float` or `None`: The confidence interval at which the source must be detected for count-rate and errors to be produced,
instead of an upper limit. If `None` (the default) this is set to `ulConf`.

**Note on `insert`** A new, merged bin can only be inserted into the light curve if it is the same type (count-rate with errors, or upper limit)
as the rest of the light curve. Accordingly, if you set `insert=True` this will force the merged bin to be of the same type as the
supplied light curve, ignoring the `forceRate` and `forceUL` arguments (if set). `insert='match'` is more equivocal: the function will
test to see if the merged bin constitutes a detection, it will then only be inserted into the light curve if its type matches that
of the light curve. You can determine the upshot of this from the function's return.

**Return data** The function returns a tuple with three entries: (isUL, inserted, newData)

* 'isUL' is a `bool` indicating whether the new bin is an upper limit.
* 'inserted' is a `bool` indicating whether the new bin has been inserted into the supplied light curve.
* 'newData' is a pandas Series containing the new bin.

**Quick demonstration of `rows`** If you don't want to have to read another page to see how to define a subset of rows to filter,
then here's an example of me asking to only merge the bins in a specified time range:

```python
ul = lcData['PCUL']  # Makes the next lines more readable
res = uk.mergeLightCurveBins(ul,
                             rows=(ul['Time']>59770)&(ul['Time']>59790) )
```

### `mergeUpperLimits()`

`mergeUpperLimits()` is analogous to the above `mergeLightCurveBins()` function, except that it works on the set of SXPS
upper limits produced by [`swifttools.ukssdc.data.SXPS.getUpperLimits()`](data/SXPS.md#ul). It returns a `dict` of results,
and does not have the `match` or `remove` options.

* `ulTab` - The `DataFrame` with the upper limits to work on.
* `rows` - `pandas.Series`: An optional  `pandas Series` defining the rows in `ulTab` to merge. This is best
defined by a `pandas` filter expression as demonstrated for the [`query module subset creation`](query.md#subsets)
* `detectionsAsRates` - `bool`: Whether to check if the source is actually detected (i.e. has a lower confidence bound >0)
in the merged result. If `True` then, the '{band}Rate', '{band}_RatePos', '{band}_RateNeg' and '{band}_RateIsDetected ' keys
will be included in the returned `dict`; the former three will be NaN if the source is not detected (default: `True``).
* `bands` - list/tuple or 'all': Which bands to calculate the merged result for. Note: if bands are listed here but not
supplied in the ultab, they will be skipped.
* `conf` - `float`: The confidence interval at which upper limits should be created (default: 0.997)
* `detThresh` - `float` or `None`: The confidence interval at which the source must be detected for count-rate and errors to be produced,
instead of an upper limit. If `None` (the default) this is set to `conf`.

The return value is a `dict` with the keys: UpperLimit, Counts, BGCounts, CorrectionFactor, Rate, RatePos, RateNeg, IsDetected for each
band requested.

### `bayesRate()`

`bayesRate` is an implementation of the [Kraft, Burrows & Nousek (1991)](https://ui.adsabs.harvard.edu/abs/1991ApJ...374..344K/abstract)
method for calculating confidence intervals.

This receives three positional arguments:

* N - `int`: The number of measured counts in the source region.
* B - `float`: The expected number of background counts in the source region.
* conf -`float`: The confidence interval to calculate (0-1).

The return is a tuple of (min, max, mean) number of source counts.
