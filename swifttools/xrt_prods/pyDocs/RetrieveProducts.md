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

Instead of downloading the archive of all data files, you can retrieve just the light curve data, in the form of a set of `Pandas DataFrame` objects.
For this there is a single function:

`retrieveLightCurve()`

There are two optional boolean arguments which both default to `False`:

* nosys - if `True` then the WT data will not include the systematic errors.
* incbad - if `True` then WT data which may be unreliable as no centroid could be found are included.

For more information on these, see [the light curve documentation](https://www.swift.ac.uk/user_objects/lc_docs.php#systematics)

Assuming that your request included a light curve, which has been completed, this function returns
a python dictionary. This dictionary is also available via the `lcData` property of your `XRTProductRequest`.

They keys of this dictionary are as below, the contents are a `DataFrame`

* WT: WT mode data for bins in which the source is deemed detected. Has 1-sigma errors.
* WTUL: WT mode upper limits for bins in which the source is not detected. "Rate" values are 3-sigma upper limits, errors are 0.
* PC: WT mode data for bins in which the source is deemed detected. Has 1-sigma errors.
* PCUL: PC mode upper limits for bins in which the source is not detected. "Rate" values are 3-sigma upper limits, errors are 0.


The columns in the `DataFrames` have labels describing them. You can view these thus:

myReq.lcData['PC'].columns

```python
In [4]: myReq.lcData['PC'].columns
Out[4]: Index(['Time', 'T_+ve', 'T_-ve', 'Rate', 'Ratepos', 'Rateneg', 'FracExp',
        'BGrate', 'BGerr', 'CorrFact', 'CtsInSrc', 'BGInSrc', 'Exposure',
        'Sigma', 'SNR'],
         dtype='object')
```

These are described in detail in the [light curve data
documentation](https://www.swift.ac.uk/user_objects/lc_docs.php#format)
(see &lsquo;Detailed data downloads&rsquo;).

### Plot the light curve

Having downloaded the light curve, you may wish to plot it. A very simple plotting function
is provided, purely for quick-look use: you will likely want something much more customised
for your own presentations or publications. You can create the plot thus:

```python
In [5]: myReq.plotLC(xlog=True, ylog=True, fileName='mylc.png')
```

**Note** This requires you to have `matplotlib.pylab` installed. The `xlog` and `ylog` arguments define whether the
x and y axes should be logarithmic, and they default to `False`. If `fileName` is supplied, the figure is saved
to the specified file, otherwise it is plotted on the screen.

A discussion of how `matplotlib` and `pandas` work is beyond the scope of this document, however to aid in creating your
own plots from the data, I give the example below which is the essence of the `plotLC()` function
(this is itself based on an example given to me by Jamie Kennea).

A few small notes are:

* The light curve data have the negative errors as negative numbers; the `errorbar` function in
`pyplot` expects positive values, hence the negative sign in the `xerr` and `yerr` arguments.
* The upper limits syntax was arrived at by trial and error. Because I want to show a down arrow, from
level of the upper limit, I am her supplying data points equivalent to the upper limit (stored as `Rate` in the light curve),
zero values for the positive error, and a uniform number correponding to the arrow size as the negative error.

```python
fig, ax = plt.subplots()

if 'WT' in myReq.lcDatalcData:
    ax.errorbar(myReq.lcDatalcData['WT']['Time'],
                myReq.lcDatalcData['WT']['Rate'],
                xerr=[-myReq.lcDatalcData['WT']['T_-ve'], myReq.lcDatalcData['WT']['T_+ve']],
                yerr=[-myReq.lcDatalcData['WT']['Rateneg'],myReq.lcDatalcData['WT']['Ratepos']],
                fmt=".",elinewidth=1.0,color="blue",label="WT",zorder=5)

if 'WTUL' in myReq.lcDatalcData:
    empty = np.zeros(len(myReq.lcDatalcData['WTUL']['Time']))
    ulSize = np.zeros(len(myReq.lcDatalcData['WTUL']['Time']))+0.002
    ax.errorbar(myReq.lcDatalcData['WTUL']['Time'],
                myReq.lcDatalcData['WTUL']['Rate'],
                xerr=[-myReq.lcDatalcData['WTUL']['T_-ve'], myReq.lcDatalcData['WTUL']['T_+ve']],
                yerr=[ulSize,empty],
                uplims=True,elinewidth=1.0,color="blue",label="WT",zorder=5)

if 'PC' in myReq.lcDatalcData:
    ax.errorbar(myReq.lcDatalcData['PC']['Time'],
                myReq.lcDatalcData['PC']['Rate'],
                xerr=[-myReq.lcDatalcData['PC']['T_-ve'], myReq.lcDatalcData['PC']['T_+ve']],
                yerr=[-myReq.lcDatalcData['PC']['Rateneg'],myReq.lcDatalcData['PC']['Ratepos']],
                fmt=".",elinewidth=1.0,color="red",label="PC",zorder=5)

if 'PCUL' in myReq.lcDatalcData:
    empty = np.zeros(len(myReq.lcDatalcData['PCUL']['Time']))
    ulSize = np.zeros(len(myReq.lcDatalcData['PCUL']['Time']))+0.002
    ax.errorbar(myReq.lcDatalcData['PCUL']['Time'],
                myReq.lcDatalcData['PCUL']['Rate'],
                xerr=[-myReq.lcDatalcData['PCUL']['T_-ve'], myReq.lcDatalcData['PCUL']['T_+ve']],
                yerr=[ulSize,empty],
                uplims=True,elinewidth=1.0,color="red",label="PC",zorder=5)

if xlog:
    ax.set_xscale("log")
if ylog:
    ax.set_yscale("log")

plt.show()
```

---
## Retrieve the spectral fits

(This feature was added in v1.8 of the `xrt_prods` module).

Instead of downloading the archive of all data files, you can retrieve just the spectral fit values.

**Important note** the values returned will be the values from the automates spectral fit. This does not mean that the fit
is appropriate. Inspection of the spectrum and fit is strongly advised.

To retrieve the spectral fits you call the `retrieveSpectralFits()` function, which takes no arguments.
Assuming that your request included a spectrum, which has been completed, this function returns
a python dictionary. This dictionary is also available via the `specData` property of your `XRTProductRequest`.

The dictionary contains a few parameters common to the request, and then a dictionary for each of the
spectra you requested, by their name. If you did not specify names or timeslices, the spectrum will be
called `interval0`. Each of these dictionaries in turn will contain some keys giving information
about the spectrum, then another dictionary for each mode with a valid spectral fit. Those
dictionaries then contain the actual fit details.

The top-level dictionary contains keys:

* T0: The reference T0 time for the spectra
* GalNH: The Galactic NH (from Willingale et al., 2013) along the
    line of sight. This is NOT included in the fit

And a dictionary for each spectrum produced. Those contain keys:

* start: Time in sec after T0 of the first data in this spectrum
* stop: Time in sec after T0 of the last data in this spectrum
* HaveWT: Whether there is a valid WT-mode fit
* WT: a dict of the WT mode fit (if HaveWT=True)
* HavePC: Whether there is a valid PC-mode fit
* PC: a dict of the WT mode fit (if HavePC=True)

The WT/PC dicts contain:

* meantime: Mean photon arrival time (in sec since T0) in this 
            spectrum
* nh: Best-fitting column density in cm^-2
* nhpos: 90% CL positive error on NH
* nhneg: 90% CL negative error on NH
* gamma: Best-fitting photon index
* gammapos: 90% CL positive error on gamma
* gammaneg: 90% CL negative error on gamma
* obsFlux: Best-fitting observed flux in erg cm^-2 s^-1
* obsFluxpos: 90% CL positive error on the observed flux
* obsFluxneg: 90% CL negative error on the observed flux
* unabsFlux: Best-fitting unabsorbed flux in erg cm^-2 s^-1
* unabsFluxpos: 90% CL positive error on the unabsorbed flux
* unabsFluxneg: 90% CL negative error on the unabsorbed flux
* cstat: The C-stat of the best fit (technically Wstat, see the
            xspec manual for details)
* dof: The degrees of freedom in the fit
* fitChi: The Churazov-weighed chi^2 test statistic. This is not
            used in the minimisation, just to asses fir quality.
* exposure: The exposure time in the spectrum

To help illustrate this, here is an example returned from a job with two spectra requested, which I named
"spectrum 1" and "spectrum 2", because that's how imaginative I am. (Note, I have artificially adjusted
the indentation of the output to help clarify the structure.

```python
In [6]: myReq.retrieveSpectralFits()
Out[6]: {
        'T0': 636878303,
        'GalNH': 4.465814e+21,
        'spectrum 1': 
            {'start': '91.5458518266678',
            'stop': '998.996383428574',
            'HaveWT': 1,
            'WT': 
                {'meantime': 112.45307648182,
                'nh': 7.58231e+21,
                'nhpos': 3.63443658e+21,
                'nhneg': -2.765281571e+21,
                'gamma': 2.0417,
                'gammapos': 0.415690796,
                'gammaneg': -0.373606428,
                'obsFlux': 2.4276719478251e-10,
                'obsFluxpos': 5.1385948118663e-11,
                'obsFluxneg': -4.3181474356172e-11,
                'unabsFlux': 4.4164162583654e-10,
                'unabsFluxpos': 1.925535760887e-10,
                'unabsFluxneg': -9.3536052181061e-11,
                'cstat': 158.3754728,
                'dof': 181,
                'fitChi': 194.9756569,
                'exposure': 45.74681532383},
            'HavePC': 1,
            'PC': 
                {'meantime': 461.84811258316,
                'nh': 7.47829e+21,
                'nhpos': 2.120201129e+21,
                'nhneg': -1.817659945e+21,
                'gamma': 1.75085,
                'gammapos': 0.224694582,
                'gammaneg': -0.212939735,
                'obsFlux': 9.9770006382255e-11,
                'obsFluxpos': 1.1417579530478e-11,
                'obsFluxneg': -1.0113710949934e-11,
                'unabsFlux': 1.5052200686321e-10,
                'unabsFluxpos': 2.1797350767084e-11,
                'unabsFluxneg': -1.5808475755874e-11,
                'cstat': 247.1350548,
                'dof': 316,
                'fitChi': 276.0133063,
                'exposure': 860.00390005112}
            },
        'spectrum 2':
            {'start': '1000',
            'stop': '6089.67395174503',
            'HaveWT': 0,
            'HavePC': 1,
            'PC': 
                {'meantime': 3507.7555564642,
                'nh': 8.6891e+21,
                'nhpos': 3.10760318e+21,
                'nhneg': -2.580664317e+21,
                'gamma': 1.80562,
                'gammapos': 0.326599551,
                'gammaneg': -0.305913706,
                'obsFlux': 9.7768735896742e-12,
                'obsFluxpos': 1.677279147949e-12,
                'obsFluxneg': -1.4061334490069e-12,
                'unabsFlux': 1.5606301757026e-11,
                'unabsFluxpos': 3.7986385002847e-12,
                'unabsFluxneg': -2.2855050636094e-12,
                'cstat': 169.5760982,
                'dof': 201,
                'fitChi': 189.0071024,
                'exposure': 1890.5042001009}
            }
        }
```

---

## Retrieve the positions

For the three possible position types (standard, enhanced and astrometric), instead of downloading the data files, you may 
just wish to get the position. For this we provide three functions:

* `retrieveStandardPos()`
* `retrieveEnhancedPos()`
* `retrieveAstromPos()`

which will attempt to retrieve the position type implied in the function name.

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
In [7]: myReq.retrieveStandardPos()
Out[7]:
{'GotPos': True,
 'RA': '335.69850',
 'Dec': '-7.51788',
 'Err90': '3.5',
 'FromSXPS': False}

In [8]: myReq.retrieveEnhancedPos()
Out[8]: {'GotPos': True, 'RA': '335.69928', 'Dec': '-7.51816', 'Err90': '1.7'}

In [9]: myReq.retrieveAstromPos()
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
Assuming the source detection has completed with success, this will return a Python dict, with one entry per energy band for which
source detection was requested, i.e. either `Total`, or `Total`, `Soft`, `Medium`, and `Hard`.

Each of these entries is itself a list, with one entry per source. That entry is another dict, giving the properties of the source.
The details of this dict are described in [the source list file documentation](https://www.swift.ac.uk/user_objects/sourceDet_docs.php#positionFiles)

To demonstrate this (for an example where all energy bands were requested)

```python
In [10]: src = myReq.retrieveSourceList()
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


