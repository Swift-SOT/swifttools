# How to retrieve the products

Once your [products are complete](JobStatus.md) you will, one assumes, wish to access them. There are three things you can retrieve:

* [The data files.](#download-the-data)
* [The light curve.](#retrieve-the-light-curve)
    * [Plot the light curve.](#plot-the-light-curve)
* [The spectral fits.](#retrieve-the-spectral-fits)
* [The positions](#retrieve-the-positions)
* [The source list](#retrieve-the-source-list)

## Download the data

To download the set of data produced for your request, you need the `downloadProducts()` method.

This method has a single mandatory parameter: the directory into which you wish to save the products. Thus, the easiest way to download the products is:

```python
In [1]: myReq.downloadProducts('/my/safe/place')
Out[1]:
{'LightCurve': '/my/safe/place/lc.zip',
 'Spectrum': '/my/safe/place/spec.zip',
 'StandardPos': '/my/safe/place/psf.zip',
 'EnhancedPos': '/my/safe/place/enh.zip',
 'AstromPos': '/my/safe/place/xastrom.zip'}
```

This will download all of the products that you asked to build which were complete last time [you checked](JobStatus.md) (from which it follows that you should check if your products are complete before trying to download them!)

There are several optional parameters you can also pass, to control the download:

| Parameter | Values? | Description | Default |
| :----:    |  :----: | :-----      | :----:  |
| what | 'all', or a list/tuple of products | Which products to download | 'all' |
| stem | Any string | A string to prepend to the names of the downloaded files | None |
| format | 'tar' / 'tar.gz' / '.zip' | The format to download the products in. | 'tar.gz'
| silent | True/False | Whether to suppress reporting progress to the standard output | False |
| clobber | True/False | Whether to overwrite the files if they already exist | False |


So, here are some examples:

```python
In [2]: myReq.downloadProducts('/my/safe/place/' what=('LightCurve',), format='zip')
...

In [3]: myReq.downloadProducts('/my/safe/place/', clobber=True, stem='my_test_run_')

...
```

**Important note**: If you are requesting only a single product (e.g. a light curve in the first example above), you must ensure that you give a trailing comma inside the parentheses (or use square brackets), or Python will interpret the
argument as a single string, not a tuple. (My thanks to Greg Sivakoff for identifying this error in my original documentation).

---

## Retrieve the light curve

(This feature was added in v1.8 of the `xrt_prods` module).

You can obtain the light curve data in the [standard light curve
`dict`](https://www.swift.ac.uk/API/ukssdc/structures.md), using the `retrieveLightCurve()` function. This will save the
data in the `lcData` variable of your object (e.g. access it via `myReq.lcData`), and takes three (optional) parameters:

* `returnData` - a `bool` indicating whether the function should return the data, as well as storing it internally (default: `False`).
* `nosys` - Whether to return the data from which WT systematics have been excluded. Can be 'yes', 'no' or 'both' (default: 'no').
* `incbad` - Whether to return the light curve(s) which include data from times when no centroid could be obtained. Can be 'yes', 'no' or 'both' (default: 'no').

For more information on the latter two options, [the light curve documentation](https://www.swift.ac.uk/user_objects/lc_docs.php#systematics).

### Plot the light curve

Having downloaded the light curve, you may wish to plot it. There is a [common plotting function](https://www.swift.ac.uk/API/ukssdc/commonFunc.md#plotlightcurve) supplied
in the `swifttools.ukssdc` module, and the `xrt_prods` class contains a wrapper to this

```python
In [5]: myReq.plotLC(xlog=True, ylog=True, fileName='mylc.png')
```

**Note** This requires you to have `matplotlib.pylab` installed.

For full details of the plotting function see the [Module-level Functions documentation](https://www.swift.ac.uk/API/ukssdc/commonFunc.md).
This function returns the `fig, ax` objects created by a `pyplot.subplot()` call, so you can capture these for further
manipulation.


### Rebin the light curve

If, having downloaded and inspected the light curve, you want to change the binning you can do this
without having to submit a new request. You do this by calling `myReq.rebinLightCurve(**kwarg)`. This literally
just wraps the [`rebinLightCurve()` module-level function](https://www.swift.ac.uk/API/ukssdc/commonFunc.md#rebinlightcurve),
and all arguments are passed straight through to that. The rebin functionality is shared by various aspects of the
`swifttools.ukssdc` module, and so is [documented with the common functions](https://www.swift.ac.uk/API/ukssdc/commonFunc.md#rebinning-light-curves).

---

## Retrieve the spectral fits

(This feature was added in v1.8 of the `xrt_prods` module).

You can obtain details of the spectra and the fits to them using the `retrieveSpectralFits()` function. This takes the
single optional argument `returnData`, which is a `bool` and defaults to `False`.

Assuming that your request included a spectrum, which has been completed, this function retrieves a 'spectum `dict`':
the python `dict` structured as standard for spectra throughout the `swifttools.ukssdc` module (described in the [Data
Structures documentation](https://www.swift.ac.uk/API/ukssdc/structures.md)). This `dict` will be saved to the `specData`
variable of your request, and so can be accessed via `myReq.specData`. If you specified `returnData=True` then it
will also be returned by the `retrieveSpectralFits()` function call.

**Important note** the values returned will be the values from the automated spectral fit(s) if requested. This
does not mean that the fit is appropriate or good. Inspection of the spectrum and fit is strongly advised.


### Download and extract the spectral data

(This feature was added in v1.10 of the `xrt_prods` module).

In addition to the generic `downloadProducts()` function, there is a function tailored purely to obtaining
the spectral files: `saveSpectralData()`. This was added as part of `swifttools` v3.0, and is really just a wrapper to
the `saveSpectrum()` function common to the `swifttools.ukssdc` module, and documented in the
[Module-level Functions documentation](https://www.swift.ac.uk/API/ukssdc/commonFunc.md). Note that
before calling this function you must get the spectral fit files with `retrieveSpectralFits()`, above.

---

## Retrieve the positions

For the three possible position types (standard, enhanced and astrometric), can can obtain a `dict` containing
details of the position using the three functions:

* `retrieveStandardPos()`
* `retrieveEnhancedPos()`
* `retrieveAstromPos()`

which will attempt to retrieve the position type implied in the function name. Each of these stores the data
in a class variable: `standardPos`, `enhancedPos`, or `astromPos`, and they take the optional `returnData` boolean
argument (which defaults to `False`) if you want them to also return the

This returns a dictionary object, they keys of which depend on the status of the position. There will always be
a key `GotPos` which is a `bool`, indicating whether or not a position is available.

If `GotPos` is `False` then the only other key will be `Reason` which is a string, giving some information about
why no position was available.

If `GotPos` is `True` then keys `RA`, `Dec` and `Err90` exist, giving the position (in decimal degrees, J2000) and 90% confidence
radial position error (in arcsec).

For the standard and astrometric positions there is also the boolean key `FromSXPS` and, if this is `True`,
a key `WhichSXPS`, indicating whether the position was taken from one of the SXPS catalogues, and if so, which one.
When you request a standard or astrometric position, if the input position corresponds to an object in SXPS, and
the dataset requested corresponds exactly with a dataset analysed for the SXPS catalogue, then the position
returned is simply taken from the catalogue, rather than repeating an identical analysis to that carried out for
the catalogue. The most recent SXPS catalogue will also be that used: at the time of writing this is
[2SXPS](https://www.swift.ac.uk/2SXPS); the `WhichSXPS` key is provided to support future releases of the catalogue.

Here are some example position queries:

```python
In [7]: myReq.retrieveStandardPos(returnData=True)
Out[7]:
{'GotPos': True,
 'RA': '335.69850',
 'Dec': '-7.51788',
 'Err90': '3.5',
 'FromSXPS': False}

In [8]: myReq.retrieveEnhancedPos(returnData=True)
Out[8]: {'GotPos': True, 'RA': '335.69928', 'Dec': '-7.51816', 'Err90': '1.7'}

In [9]: myReq.retrieveAstromPos(returnData=True)
Out[9]:
{'GotPos': True,
 'RA': '335.70087',
 'Dec': '-7.51741',
 'Err90': '14.3',
 'FromSXPS': False}
 ```

---

## Retrieve the source list

If you requested source detection, then you can download the source lists directly, using the `retrieveSourceList()` function.
Assuming the source detection has completed with success, this will download a Python `dict`, with one entry per energy band for which
source detection was requested, i.e. either `Total`, or `Total`, `Soft`, `Medium`, and `Hard`. As you should probably
have guessed by now, this will save the data in the `sourceList` class variable; the `returnData` argument, if `True` (which it
is not by default) will cause the function to return the `dict` as well.

Each entry in the `dict` is a list, with one entry per source. That entry is another `dict`, giving the properties of the source.
The details of this dict are described in [the source list file documentation](https://www.swift.ac.uk/user_objects/sourceDet_docs.php#positionFiles)

To demonstrate this (for an example where all energy bands were requested)

```python
In [10]: src = myReq.retrieveSourceList(returnData=True)
In [11]: src.keys()
Out[11]: dict_keys(['Total', 'Soft', 'Medium', 'Hard'])
In [12]: for i in src:
    ...:     print(f"{i}: {len(src[i]):d} sources")
    ...:
Total: 25 sources
Soft: 8 sources
Medium: 13 sources
Hard: 10 sources
In [11]: src['Total'][0]
Out[1]:
{'sno': 1,
 'x': 503.9997227258,
 'y': 470.3955699394,
 'ra': 32.1512120191,
 'ra_pos': 2.28992155234127e-07,
 'ra_neg': -2.28992155234127e-07,
 'dec': 56.9457053386,
 'dec_pos': 1.249e-07,
 'dec_neg': -1.249e-07,
 'err90': 3.50000005791013,
 'l': 133.343725932081,
 'b': -4.35794339989909,
 'C': 1236,
```
