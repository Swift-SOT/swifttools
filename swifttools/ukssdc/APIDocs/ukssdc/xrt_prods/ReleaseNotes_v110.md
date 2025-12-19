# swifttools.ukssdc.xrt_prods v1.10 Release Notes

Version 1.10 of the `xrt_prods` module was released as part of `swifttools v3.0` on 2022 August 31.

This release features a number of important changes mainly relating to the way in which data products
are returned and formatted. We have made significant efforts to support backwards compatibility, so **all of your
existing scripts should continue to work in the present release, provided you add one line at the top of your code**.
However, this will not be the case indefinitely: the affected old behaviour is deprecated and will be removed in a
future release.

The simplest way to force the old behaviour is to set the `XRTProductRequest.useDeprecate` variable to `True`, which
you can do straight after importing. So if you have followed the previous documentation for styling you will change to:

```python
In [1]: from swifttools.xrt_prods import XRTProductRequest
In [2]: XRTProductRequest.useDeprecate = True
```

More details on managing deprecations appear below.

As well as changing certain behaviour, we have also introduced a number of new features; these are briefly
described below but discussed in more detail in the [main API documentation](xrt_prods/README.md).

We have provided a [Jupyter notebook with a hands-on whistle-stop tour of the changes](xrt_prods_110.ipynb)
for those who prefer to learn by use, rather than reading documenation.

## Contents / change list

* [New functionality](#new-functionality)
  * [Spectral fitting controls](#spectral-fitting-controls)
  * [Saving spectra](#saving-spectra)
  * [Rebinning light curves](rebinning-light-curves)
  * [Light curve manipulation](#light-curve-manipulation)
* [Managing the deprecated features](#managing-the-deprecated-features)
* [Deprecated functionality](#deprecated-functionality)
  * [Importing `xrt_prods`](#importing-xrt_prods)
  * [Retrieving data products](#retrieving-data-products)
    * [Retrieving light curves](#retrieving-light-curves)
  * [Data structures](#data-structures)
  * [Parameter name changes](#parameter-name-changes)
  * [Why the changes?](#why-the-changes)

---

## New functionality

`xrt_prods` v1.10 includes a few new features which I hope will be of use to you. I like them already. These are introduced
in the next two sections, but documented more completely in the main documentation (as linked to below).

### Spectral fitting controls

In August 2022 the [XRT product generator](https://www.swift.ac.uk/user_objects) was modified to give greater control
over the automated fits to the generated spectra. v1.10 brings support for these changes to the `xrt_prods` API as well.
These changes allow you to completely skip the spectral fitting phase, to control whether an absorber fixed at the
Galactic value is included, to set the significance of the parameter errors, and to choose from among 3 possible
emission models. The new parameters for a spectrum are:

* `doNotFit` (`bool`, default `False`): Whether to skip the fitting step.
* `galactic` (`bool`, default `False`): Whether to include the Galactic absorption.
* `models` (`list` or `tuple`): A list of which models to fit. Contents can be "powerlaw", "APEC", or "blackbody" (case insensitive).
* `deltaFitStat` (float, default 2.706): The change in fit statistic to use in determining errors in fitted parameters.

These are discussed fully on the [How to request products page](xrt_prods/RequestJob.md#spectrum-parameters)

**Note** Use of these features requires using the [new data structures](#data-structures) introduced in v1.10 of `xrt_prods`.
If you make use of these new features while also setting `useDeprecate=True` then, well I don't actually know what will happen,
but it probably won't be pretty. Don't try it.

### Saving spectra

We have added a new function `saveSpectralData()`, which allows you to download the data related to your created spectra.
You can select to save only the `png` images of the spectra, or the actual data, as a `tar.gz` archive which you can
also select to extract. This is more fully documented on the [How to retrieve the products page](xrt_prods/RetrieveProducts.md).

This is in addition to the `downloadProducts()` function which is unchanged.


### Light curve manipulation

Two new features have been included which let you do more with your light curves. The first is the `rebinLightCurve()`
function, which lets you rebin the lightcurve without having to rerun the whole product build, it just redoes the
binning phase of the light curve. The second is a function called `mergeLightCurveBins()`. This allows you to, er, merge
bins in a light curve. For example, you may have created a light curve with a bin per observation, but your source had
an extended period in which this yielded no detection, and you want to merge the resultant upper limits (either to get a
deeper limit, or see if this merging yields a detection).

Both of these are shared functions within the `swifttools.ukssdc` module and so iare
[documented on the common functions page](https://www.swift.ac.uk/API/docs/commoFunc.md) rather than here, but it will work
with light curves created and retrieved using the `xrt_prods` module.

**Note** `mergeLightCurveBins()` has certain expectation of the light curve you give it, and it will not work
on a light curve retrieved with deprecation enabled. So if you did give the `useDeprecate=True` argument
then the light curve you obtained will not be properly handled by this new function. If you want to use the v1.10 functionality,
you need to use v1.10, rather than forcing older behaviour.

---

## Managing the deprecated features

As just noted above, the quick-and-easy solution to not caring about the changes is to tell `xrt_prods` to
use the deprecated features. You can do this in a few ways (the code snippets below assume you've imported
the `XRTProductRequest` object).

```python
In [1]: XRTProductRequest.useDeprecate = True
In [2]: myReq = XRTProductRequest('YOUR_EMAIL_HERE', useDeprecate=True)
In [3]: myReq.deprecate=True
```

Obviously, running all 3 above would be a bit pointless since they all do the same thing, I'm just showing
the options. In my opinion the top option is the best one, because it is a simple one-off entry at the
top of your script/notebook/whatever and affects everything in the script. The second and third options
obviously affect only a single request, and demonstrate changing the setting during the constructor or
after the case. Of course, it is possible to set the variable to `False` instead of `True`.

While you are using the deprecated behaviour, you will get warnings appear the first time a script calls one of the
deprecated functions. After about 11 seconds you may find this annoying, so you can turn them off by setting the (new)
`showDepWarnings` variable in an `XRTProductRequest` object to `False`. You can do this when creating the object or
subsequently, as in the two examples calls below:

```python
In [4]: myReq = XRTProductRequest('YOUR_EMAIL_HERE', showDepWarnings=False)
In [5]: myReq.showDepWarnings=False
```

(Of course, calling both of these would be overkill).

Frankly, however, if you are going to modify your code to stop all those pesky warnings from appearing,
it would be better to modify it to stop using deprecated behaviour. The needed modifications are generally pretty small,
so let's take a look at them.

## Deprecated functionality

The changes in functionality are pretty minor, and almost entirely relate to the way in which you retrieve products
that you have requested. I've added a quick note about why this change exists at the end of this section, for the curious,
but let's dive straight into exploring the changes. We'll start with a really trivial one and then move on to the slightly
more impactful things.

### Importing xrt_prods

The `xrt_prods` module has been moved inside the new `swifttools.ukssdc` module, and so "should" be imported with

```python
In [6]: from swifttools.ukssdc.xrt_prods import XRTProductRequest
```

Or if you prefer to keep your namespaces clean:

```python
In [7]: import swifttools.ukssdc.xrt_prods as ux
```

(You don't have to use the `as ux` but it's a bit shorter, and also follows a convention for all the `swifttools.ukssdc` imports).

**You do not have to do this.** I have created a wrapper file, so the module `swifttools.xrt_prods` still appears to exist,
and I have no current plans ever to change this, but I'd still advise it partly in case I ever change my mind, and also
because it makes all the new imports look more homogenous and pretty.

### Retrieving data products

The `XRTProductRequest` class includes functions for retrieving the data products you built, but the behaviour of these
differed from product to produce. All of the functions would return the retrieved data, but `retrieveLightCurve()` and
`retrieveSpectrum()` would also store the retrieved data inside a class variable (`myReq.lcData` and `myReq.specData`).

From v1.10, this behaviour has been homogenised and slightly altered. Now all `retrieve...() functions`:

* store the retrieved data in a class variable,
* do not return the data by default.

You can still ask the function to return the data, by passing the (new) argument `returnData=True`, e.g.

```python
In [8]: lc = myReq.retrieveStandardPos(returnData=True)
```

and/or you can access the returned data via the class variables (most of which are new):

* `lcData`
* `specData`
* `sourceList`
* `standardPos`
* `enhancedPos`
* `astromPos`.

Note that these are class variables, i.e. they belong to your `XRTProductRequest` object, so if you called this `myReq` as in
all my demos, you would prepend `myReq.` to the above variable names to access them.

#### Retrieving light curves

There is an extra small change to the `retrieveLightCurve()` function. The `incbad` and `nosys` arguments
can now be "yes", "no" or "both" (or still `True` and `False` as before); i.e. instead of having to choose between
only getting data with/out unreliable bins and with/out WT systematic errors, you can now get both. If you're wondering
how you know what is what in your dataset, then read on&hellip;

### Data structures

The format of light curve and spectral data that you retrieve via the `retrieveLightCurve()` and `retrieveSpectralFits()`
functions has been revised somewhat. The object returned in each case is still a `dict` but with some changes
to the structure compared to v1.9. These new structures are common across the entire `swifttools.ukssdc` module,
and are described in detail on [a dedicated page](https://www.swift.ac.uk/API/ukssdc/structures.md); the key changes compared
to v1.9 are:

* Some of the column names in the light curves and spectra have changed.
* The light curve `dict` has some extra contents, describing the downloaded data.
* The light curves themselves may have different keys: if you requested the 'incbad' light curve, you will
need to access `lcData['PC_incbad']` instead of `lcData['PC']` in PC mode, for example (this is how you differentiate
datasets if you said `incbad='both'`, see above).
* The spectral `dict` has more layers, supporting the ability to fit different models.

The column name changes are the only details I will explain here, for all else, please read the
[description of the new structures](https://www.swift.ac.uk/API/ukssdc/structures.md).

The changes to column names are all for purposes of homogenisation: the capitalisation of column names was previously all over
the place, and the way in which error columns were labelled were likewise different in different places. From v1.10,
all column labels are in CamelCase, and error columns end with "Pos" or "Neg". So, for example:

* In light curves "Time, "T_+ve", "T_-ve" have become "Time", "TimePos", "TimeNeg".
* In spectra, "gamma", "gammapos" and "gammaneg" are "Gamma", "GammaPos" and "GammaNeg" etc.

Also, for light curves consisting of upper limits, the "Rate" column has been renamed "UpperLimit" to help
avoid confusion.

### Parameter name changes

When you request a light curve, the `timeType` parameter has been replaced with `timeFormat`. `timeType` still works
and is rewritten to `timeFormat` if you use it.

### Why the changes?

For those of you cursing me, wondering why I have made you change your scripts, I can only (and sincerely) apologise:
I hate it when people break backwards compatibility, even if they do it via deprecation, and having now done so myself
I am the subject of my own contempt. I have persuaded myself that it was necessary (obviously, or I wouldn't have done it)
and for anyone who cares, or can be persuaded to forgive me, I will briefly explain.

There were really three things at stake here.

1. The creation of the `swifttools.ukssdc` module.
1. The realisation that the existing behaviour was not very homogeneous.
1. The need to support new functionality.

These are somewhat interconnected so I will just explain (briefly) prosaically.

When creating the new `ukssdc` module, with features to access data (including light curves and spectra) for GRBs and the SXPS
catalogues, I intended to make the behaviour identical to that of the `xrt_prods` module which I hope you will agree was a
laudable goal. It quickly became obvious that the `xrt_prods` behaviour was, frankly, rubbish. Column names had no consistency
in their formatting (for historical reasons, specifically: "2007 me was an idiot."), some functions saved data to class
variables and others didn't, and so on. I also realised that there were things I wanted to be able to do in this new module
which the `xrt_prods` module didn't support -- such as the `incbad='both'` option for getting light curves, and for the reasons above
it made sense to port these options to the `xrt_prods` module as well. For spectra, the SXPS catalogues contain two different
spectral model fits, so the structure in which these fits are returned needed adjusting. I did consider not porting this
new structure to `xrt_prods`, but instead took the opportunity to implement a long-promised feature for the product generator:
the ability to fit more than just power-laws. Having done this, it was obviously essential that `xrt_prods` uses the new structure.

Having persuaded myself that these changes were justified, I have made considerable effort not to immediately break anyone's scripts,
by adding a ridiculous amount of code and the front and back ends to ensure that users still on v1.9 or earlier get back from the server
the data format they were expecting, and users on v1.10 can request the "deprecated mode", in which case the new-format data
come back from the server, and then are internally "rewritten" to the old format.
