# How to request products

The main part of requesting products be built is, well, requesting that products be built(!). This is relatively
straightforward in concept and can be done with a very small number of commands; however, it does require you to know
what parameters can be set, and which ones are mandatory. Fortunately, this page gives you all of that information.
**Note**: This documentation is not designed to introduce the XRT Product Generator. If you are not familiar with this
facility we strongly advise you to read [that facility's documentation](https://www.swift.ac.uk/user_objects/docs.php) first, and we also recommend
that you build a few products via [the web interface](https://www.swift.ac.uk/user_objects/) web interface to familiarise yourself
with the system before trying to use the Python module.

On this page we will:

* [Detail the Python commands used to create a product request](#python-commands-relating-to-product-creation)
  * [Managing global parameters](#managing-global-parameters)
  * [Managing specific parameters](#managing-specific-products)
  * [Submitting the request](#submitting-the-request)
* [List the parameters than can/must be set, by category](#configurable-parameters):
  * [Global parameters](#global-parameters)
  * [`XRTProductRequest` parameter](#xrtproductrequest-parameters)
  * [Light curve parameters](#light-curve-parameters)
  * [Spectrum parameters](#spectrum-parameters)
  * [Position parameters](#position-parameters)
  * [Image parameters](#image-parameters)
  * [Source detection parameters](#source-detection-parameters)


---

## Python commands relating to product creation

The first step for creating a product request is to create an `XRTProductRequest` object. For this you need the email address you
[registered](https://www.swift.ac.uk/user_objects/register.php) with:

```python
In [1]: import swifttools.ukssdc.xrt_prods as ux
In [2]: myReq = ux.XRTProductRequest('YOUR_EMAIL_HERE', silent=False)
```

Now we need to build up the request. The basic controls are to set global parameters, add products and set their parameters, and to check if the request has all the mandatory parameters set. These steps are all described below.

One little note: in this documentation I am describing all of the options (with code examples from an ipython shell). This is to give an introduction to the API, and of course, you may want to play around like this yourself. However, scripted requests will likely not use many of the functions described below: for example, a script won't decide to add a light curve and then change its mind!

---

### Managing global parameters

Global parameters are set using the `setGlobalPars` function which receives the parameters as keyword arguments. That is, we simply use
"par=value" as the function arguments, where the "par"s are the [global parameters](#global-parameters). i.e.

```python
In [3]: myReq.setGlobalPars(centroid=True, posErr=1.5)
```

You can set as many global parameters as you want at a time, and can call `setGlobalPars` as many times as you want.

If you want to check what values certain global parameters have, you can use the `getGlobalPars` function. This takes an optional
argument which is a parameter name or 'all' (which is the default). The former case will return the value of the specified parameter
(or `None` if it is not yet set). The latter will return a dictionary of all of the parameters that have been set. Optionally in the latter case
you can set `showUnset=True` and this will list all global parameters.

```python
In [4]: myReq.getGlobalPars('centroid')
Out[4]: True

In [5]: print(myReq.getGlobalPars('detMeth')) # add print because (i)python does not show anything for None without it!
Out[5]: None

In [6]: myReq.getGlobalPars() # same as getGlobalPars('all')
Out[6]: {'centroid': True, 'posErr': 1.5}

In [7]: myReq.getGlobalPars(showUnset=True)
Out[7]:
{'name': None,
 'targ': None,
 'T0': None,
 'SinceT0': None,
  ...etc...
}
```

---

### Managing specific products

The basic format for adding and manipulating products is simple and is the same for all products, except that the product name changes.
In the list below I have used the light curve product, but if you replace `LightCurve` with another product name then you will have the command
for the other product.

The products available are:

* LightCurve
* Spectrum
* StandardPos
* EnhancedPos
* AstromPos
* Image
* SourceDet

And the functions to manipulate them are:

* `addLightCurve()`
* `removeLightCurve()`
* `setLightCurvePars()`
* `getLightCurvePars()`
* `removeLightCurvePar()`

So now let's unpack this a bit.

To add a product you use the `add...()` function. This can be called either with no parameters, or you can pass parameters as well. These are passed as Python keyword arguments, i.e. just as par=value pairs. The permitted parameters and values for each product appear further down this page.

```python
In [8]: myReq.addLightCurve(binMeth='counts')
Successfully created a light curve
```

You can only have one of each type of product per request, so if you call `addLightCurve` when `myReq` already has a light curve,
you will get an error. If you wanted to completely forget the light curve request you'd formed and start again, you can
simply add the argument `clobber=True` to the `addLightCurve()` function (or the `addSpectrum()` etc. function for different
products).

If you didn't pass the parameters at creation time, or didn't pass all of them or you want to change them,
you can do this with the `set..()` function:

```python
In [9]: myReq.setLightCurvePars(pcCounts=20, wtCounts=30, dynamic=True)
```
We can check the light curve parameters as we did for the globals:

```python
In [9]: myReq.getLightCurvePars('binMeth')
Out[9]: 'counts'

In [10]: myReq.getLightCurvePars()
Out[10]: {'binMeth': 'counts'}

In [11]: myReq.getLightCurvePars(showUnset=True)
Out[11]:
{'binMeth': 'counts',
 'soft1': None,
 'soft2': None,
 'hard1': None,
 ...etc...
}
```

Conceivably we may want to remove a parameter we'd set. For example, for a spectrum we may have set a redshift, and then changed our minds, so we can remove it with `remove...()` thus:

```python
In [12]: myReq.addSpectrum(redshift=1.23)
myReq.addSpectrum(redshift=1.23)
Successfully created a spectrum
Also setting hasRedshift = True

In [13]: myReq.removeSpectrumPar('redshift')
Also setting hasRedshift = False
```

This example lets me introduce one other concept. There are a few parameters that are automatically set if another parameter is set. In the case above you can see that when we set the redshift the code was intelligent enough to realise that this means we want to fit the spectrum with a redshift, and so it set the `hasRedshift` parameter to `True`, and then do the inverse when the redshift was removed.

Finally, we may decide that we don't want to build this product after all, so we can remove it:

```python
In [14]: myReq.removeSpectrum()
```

#### Little aside

In the above I've described the functions of the form `getLightCurvePars()` etc. These are actually convenience functions which are really just wrappers,
internally they call generic functions and pass the product name. I can foresee circumstances where your scripts may also prefer to do this (i.e. where you want the product type to be in a variable). In that case you can use the generic functions below:

* `addProduct(what)`
* `removeProduct(what)`
* `setProductPars(what)`
* `getProductPars(what)`
* `removeProductPar(what)`

Here `what` is the product type, i.e. `LightCurve`, `Spectrum` etc. Any extra arguments as defined in the product-specific examples can be passed as well, e.g.
`myReq.setProductPars('LightCurve', binMeth='counts')` is the same as `myReq.setLightCurvePars(binMeth='counts')`

---


### Submitting the request

This step is very straightforward:

```python
In[15]: ok = myReq.submit()
```

Note that we captured the return in a variable `ok`, because `submit()` returns a bool, telling us whether or not the job was successfully submitted.
If this is `True` you can jump to the pages about [cancelling the job](CancelJob.md), [querying its status](JobStatus.md), or [downloading the data](RetrieveProducts.md). Or you can have a look at the [data returned by the server](ReturnData.md) if you are curious about that.

But, submission isn't always OK. Indeed, in the case illustrated just here, submission failed, and I want to know why:

```python
In [16]: print(ok)
False
In [17]: print(myReq.submitError)
The request is not ready to submit:

The following problems were found:
* Global parameter `centroid` is not set.
* Global parameter `name` is not set.
* Global parameter `useSXPS` is not set.
* Global parameter `RA` is not set, and nor is the alternative: `getCoords`.
* Global parameter `Dec` is not set, and nor is the alternative: `getCoords`.
* Global parameter `targ` is not set, and nor is the alternative: `getTargs`.
```

Ah, yes, that would explain it. I forgot to set a bunch of parameters. In this particular case the request submission failed before python even tried to submit it to the server, because some internal checks are done before submission. You can do these checks yourself before running `submit()` if you want, via the `isValid()` function. This takes one (optional) argument, which is either 'all' (the default) or a list/tuple of products to check. It returns a list with two entries: first a `bool` indicating whether the product/request is valid or not, and second a text string saying what's wrong (if it's not ready).

```python
In [18]: status = myReq.isValid( ['LightCurve', 'Spectrum'])
In [19]: print(status[0])
False
In [20]: print(status[1])
The following problems were found:

light curve problems:
* Global parameter `centroid` is not set.

spectrum problems:
* Global parameter `centroid` is not set.

In [19]: status = myReq.isValid()
In [20]: print(status[1])
The following problems were found:
* Global parameter `centroid` is not set.
* Global parameter `name` is not set.
* Global parameter `useSXPS` is not set.
* Global parameter `RA` is not set, and nor is the alternative: `getCoords`.
* Global parameter `Dec` is not set, and nor is the alternative: `getCoords`.
* Global parameter `targ` is not set, and nor is the alternative: `getTargs`.

light curve problems:
* Global parameter `centroid` is not set.

spectrum problems:
* Global parameter `centroid` is not set.

```

**Note** if you supply a product/list of products then the global variables as a whole are not checked. Some globals are only needed by certain products and these will be checked (hence `centroid` being listed above), but the entire set of shared globals is not. To check that your request is ready to submit you should use `isValid('all')` (or just `isValid()`). The `submit()` function does this internally before trying to submit the job.

**Note 2** even if `isValid()` returns `True`, request submission can still fail. For example, I created this request with the userID: 'YOUR_EMAIL_HERE'. This is a) not a valid email address and b) not registered with the service. So although the Python module will submit the request to the UKSSDC servers, those servers will reject it. Such a failure is handled in the same way as in these examples: `myReq.submit()` will return false and `myReq.submitError` will contain a textual description of the problem.

#### Advanced submission notes

`submit()` has an optional parameter, `updateProds`, which defaults to `True`. If this is True then the parameters in your request will be updated to those which [the server returned](ReturnData.md). Normally, this doesn't affect you at all, since you can't change the parameters after submission, nor do you need them. So why does this happen?

When you submit a request, you don't have to supply every possible parameter, many of them have default values. And some parameters ask the server to calculate
other values: for example if `getCoords` is `True` then the server will try to resolve the supplied name, to get the position. You may want to know what values the server actually used, either for sanity checking (is the resolved position what you were expecting?) or so that you can submit a later job with the same set of parameters.

Of course, you can find this out by looking at [the data returned by the server](ReturnData.md), but you then have to manage those data yourself. On the other hand, as discussed in [Advanced usage](advanced.md), we provide a simple mechanism to dump the parameters and values from one request and paste them into another: this is useful if you want to create a similar / identical request (for example, to update a product every time it is re-observed, without changing any of the parameters). For this case, it is helpful to have your request parameters updated to include those set by the server, so that if you dump or copy those parameters you know that you are copying the exact parameters. Since changing the product parameters after submission has no effect on the running jobs (and indeed, you can't manually change parameters after submission), this option is `True` by default, For more infomration see [Advanced usage](advanced.md).

---


## Configurable parameters

Above we have explained how to create an `XRTProductRequest` object and submit the request to the servers to create an actual
product-build job. Below we list all of the different parameters that can be set. These come in specific groups:

* `XRTProductRequest` parameters
* Global parameters
* Product-specific parameters.

The first set are parameters directly related to the Python object you
have created, rather than to the products requested. The global
parameters are not tied to any specific product but affect all products.
The product-specific parameters are, as the name implies, tied to
specific parameters.

Most fields are self-explanatory. Times can be entered in any of the [formats specified in the XRT Products documentation](https://www.swift.ac.uk/user_objects/docs.php#timeformat). the `useObs` fields can contain either a list of Swift obsIDs, or a comma-separated list of *start-stop* values, where start/stop are times in the formats just described.

---

**All parameter names are case-sensitive**

### `XRTProductRequest` parameters

These parameters relate to the Python object you have created (i.e. `myReq` in the above). They are set/read by accessing them directly as variables, e.g. `myReq.silent=False`.
**Parameter names are case-sensitive**

| Parameter         | Writable?  | Type   | Description |
| :----             |  :----:    | :---:  | :-----      |
| UserID            | Yes        | str    | Your registered email address. |
| silent            | Yes        | bool   | Whether messages should be printed to stdout as you go. |
| submitted         | No         | bool   | Whether your request has been succesfully submitted. |
| statusCode        | No         | int    | A numerical code describing the current status of the request. |
| statusText        | No         | str    | A textual description of the current status of the request. |
| status            | No         | list   | A list of (statusCode, statusText). |
| globalPars        | No         | dict   | The dictionary of currently-assigned global parameters. |
| *JobID            | No         | int    | The ID assigned to the job on successful submission. |
| *complete         | No         | bool   | Whether your products have finished building. |
| *subRetData       | No         | dict   | All of the data returned by the server when you attempted to submit a job. |
| *jobPars          | No         | dict   | The job parameters returned by the server on submission, e.g. with defaults added etc. |
| *URL              | No         | str    | The URL where your products will appear on completion. |
| *submitError      | No         | str    | The textual description of why job submission failed. |

Parameters marked with * are only set when you submit your request. Some parameters will only be set if the submission
is (un)successful.

There are also variables for each product you have requested, e.g. `myReq.LightCurve`, `myReq.Spectrum` etc. These
are intended to be access only to copy products from one request to another, as described in [Miscellaneous methods and advanced usage](advanced.md).

---

### Global parameters:

Global parameters are set/retrieved with the `setGlobalPars()` and `getGlobalPars()` (described [above](#managing-global-parameters)). All possible global paramters are given in the table below. **Parameter names are case-sensitive**

| Parameter | Mandatory? | Type  | Description | Default |
| :----     |  :----:    | :---: | :-----      | :----:  |
| name      | Yes        | str   | The object name | -- |
| targ      | Yes*    | str   | A comma-separated list of targetIDs to use (e.g. '00945521,00013267') | -- |
| T0        | No**        | float/int | T0 time to use as a reference (e.g light curve zeropoint) | -- |
| SinceT0   | No         | bool | Whether all other time variables are relative to T0 | False |
| RA        | Yes***       | float | Object RA in decimal degrees (J2000) | -- |
| Dec       | Yes***       | float | Object declination in decimal degrees (J2000) | -- |
| centroid  | If lightcurve/spectrum<br/> is created | bool | Whether to try to centroid in the XRT coordinate frame | -- |
| centMeth  | If `centroid=True` | str | Which centroid method to employ, "simple" or "iterative" | "simple" |
| maxCentTries | If `centroid=True` | int | How many obsIDs to attempt centroiding on before aborting | 10 |
| posErr    | If `centroid=True` | float/int | How far from the input position the centroid position can be (arcmin) | -- |
| sss       | No  | bool | Whether this is a super-soft source**** | False |
| useSXPS   | No  | bool | Whether to use source lists from SXPS where possible | False |
| wtPupRate | No | float/int | The count-rate above which WT data are tested for pile up (ct/sec) | 150 |
| pcPupRate | No | float/int | The count-rate above which PC data are tested for pile up (ct/sec) | 0.6 |
| notify    | No | bool | Whether to email you when the products are complete / fail | False |
| getTargs  | No* | bool | Whether to ask the server to complete the `targs` field automatically | False |
| getT0  | No** | bool | Whether to ask the server to complete the `T0` field automatically | False |
| getCoords  | No*** | bool | Whether to ask the server to complete the `RA` and `Dec` fields automatically | False |

*: The targetID(s) must be supplied; these tell the server which sets of data to include in your products, and it can be a comma-separated list if more than one targetID corresponds to your object. You can either supply the targetIDs in the `targ` field, or set `getTargs=True`. In the latter case, the server will select all targetIDs in the database where the object name matches that in the `name` field, **and**  targets in the database where the XRT field of view will overlap the position in the (`RA`, `Dec`) fields. If `getCoords=True` then the targetID determination is carried out **after** the name has been resolved
into a position.

**: A start time is not mandatory, but is helpful, particularly to zero the time axis on light curve, but it can also be used as a reference point for all other input times. You can either supply it in the `T0` field, or set `getT0=True`. In the latter case the server will try to work it out, either as the trigger time (if the object is a GRB), or as the start time of the first observation of the object. In this case `T0` will be set in the [data returned by the server](ReturnData.md)

***: Coordinates must be supplied. You can either supply these directly using the `RA` and `Dec` fields, or you can set `getCoords=True`. In the latter case the server will attempt to resolve the name (using [SIMBAD](http://simbad.u-strasbg.fr/simbad/)). If resolving fails, your submission will fail. If it succeeds, the `RA` and `Dec` fields will be set in the [data returned by the server](ReturnData.md).

**** Super-soft sources tend to be more strongly affected by pile up, and at lower fluxes than normal sources. Setting `sss=True` will cause the
light curves and spectra to be created using grade 0 events only, and sets `wtpuprate` and `pcpuprate` to lower default values.



---

### Light curve parameters

Light curve parameters are set/retrieved with the `setLightCurvePars()` and `getLightCurvePars()` (described [above](#managing-specific-products)). All possible light curve parameters are given in the table below. **Parameter names are case-sensitive**


Some of the light curve parameters are relevant for all binning methods, some only for specific ones.

#### For all light curve types

| Parameter | Mandatory? | Type  | Description | Default |
| :----     |  :----:    | :---: | :-----      | :----:  |
| binMeth | Yes | str | Which binning method to use. Must be one of {'counts', 'time', 'snapshot', 'obsid'} | -- |
| minEnergy | No | float/int | Minimum energy for the main light curve, in keV | 0.3 |
| maxEnergy | No | float/int | Maximum energy for the main light curve, in keV | 10 |
| softLo | No | float/int | Minimum energy for the soft-band, in keV. Must be &geq;minEnergy | 0.3 |
| softHi | No | float/int | Maximum energy for the soft-band, in keV. Must be &leq;maxEnergy | 1.5 |
| hardLo | No | float/int | Minimum energy for the hard-band, in keV. Must be &geq;minEnergy | 1.5 |
| hardHi | No | float/int | Maximum energy for the hard-band, in keV. Must be &leq;maxEnergy | 10 |
| minSig | No | float/int | Minimum significance (in Gaussian &sigma;) for a bin to be considered a detection | 3 |
| grades | No | str | What event grades to include. Can be 'all', '0' or '4' | 'all' |
| allowUL | No | str | Whether upper limit are allowed. Must be one of {'no' 'pc', 'wt', 'both'}. | 'both' |
| allowBayes | No | str | Whether Bayesian bins are allowed. Must be one of {'no' 'pc', 'wt', 'both'}. | 'both' |
| bayesCounts | No | float,int | Threshold for counts in a bin, below which to use Bayesian statistics. | 15 |
| bayesSNR | No | float,int | Threshold for S/N in a bin, below which to use Bayesian statistics to measure count rate and error.  | 2.4 |
| timeFormat | No | str | The units to use on the time axis. Must be one of {'s'(=seconds), 'm'(=MJD)} | 's' |
| whichData | No | str | Which observations to use for the light curve. Must be one of {'all', 'user'} | 'all' |
| useObs | If `whichData='user'` | str | The specific observations to use to create the light curve [[Details](https://www.swift.ac.uk/user_objects/docs.php#useobs)] |  -- |
| srcrad | No | int | The maximum radius the source extraction region can be (pixels). |  -- |




#### For &lsquo;counts&rsquo; binning

&lsquo;Counts&rsquo; binning is where a bin requires a certain number of counts to be considered complete (unless it spans the maximum inter-observation gap). This is the binning method used by the [XRT GRB light curve repository](https://www.swift.ac.uk/xrt_curves).

| Parameter | Mandatory? | Type  | Description | Default |
| :----     |  :----:    | :---: | :-----      | :----:  |
| pcCounts  | Yes | int  | Minimum counts in a PC-mode bin for it to be full (at 1 ct/sec if dynamic binning is on) | -- |
| wtCounts  | Yes | int  | Minimum counts in a WT-mode bin for it to be full (at 1 ct/sec if dynamic binning is on) | -- |
| dynamic   | Yes | bool | Whether dynamic binning is enabled or not | -- |
| rateFact  | No  | float,int | Rate factor for dynamic binning | 10. |
| binFact  | No  | float,int | Binning factor for dynamic binning | 1.5 |
| pcBinTime | No | float,int | Minimum bin duration in PC mode in seconds | 2.51 |
| wtBinTime | No | float,int | Minimum bin duration in WT mode in seconds | 0.5 |
| minCounts | No | int | The absolute minimum counts/bin that dynamic binning can't fall below, unless the maxgap parameters below force truncation | 15 |
| minSNR | No | float,int| The minimum S/N a bin must have to be considered full, unless the maxgap parameters below force truncation | 2.4|
| pcMaxGap | No | float,int | The maximum observing gap a PC mode bin can straddle - even if not 'full' it will be stopped at this length (in seconds). | 10<sup>8</sup> |
| wtMaxGap | No | float,int | The maximum observing gap a WT mode bin can straddle - even if not 'full' it will be stopped at this length (in seconds). | 10<sup>8</sup> |

#### For fixed-time binning

| Parameter | Mandatory? | Type  | Description | Default |
| :----     |  :----:    | :---: | :-----      | :----:  |
| pcBinTime | No | float,int | Bin duration in PC mode in seconds | 2.51 |
| wtBinTime | No | float,int | Bin duration in WT mode in seconds | 0.5 |
| matchHR   | No | bool | Whether the hardness ratio should have the same bins as the main curve. | True |
| pcHRBinTime | No | float,int | Hardness ratio bin duration in PC mode in seconds | 2.51 |
| wtHRBinTime | No | float,int | Hardness ratio bin duration in WT mode in seconds | 0.5 |
| minFracExp | No | float,int | Minimum fractional exposure a bin can have, bins with a lower fractional exposure are discarded. | 0. |


---

### Spectrum parameters

Spectrum parameters are set/retrieved with the `setSpectrumPars()` and `getSpectrumPars()` (described [above](#managing-specific-products)). All possible spectrum parameters are given in the table below. **Parameter names are case-sensitive**

Some parameters are relevant all the time, some are only needed if you are definining time-slices for your spectra.


#### For all spectra


| Parameter | Mandatory? | Type  | Description | Default |
| :----     |  :----:    | :---: | :-----      | :----:  |
| hasRedshift | Yes | bool | Whether to fit with a redshifted absorber | -- |
| redshift | If `hasRedshift=True` | float,int | The redshift of the source | -- |
| whichData | No | str | Which observations to use for the spectrum. Must be one of {'all', 'user', 'hours'} | 'hours' |
| specStem | No | str | If `whichData='all`' this allows you to specify the stem for the spectrum files | 'interval0' |
| useObs | If `whichData='user'` | str | The specific observations to use to create the spectrum [[Details](https://www.swift.ac.uk/user_objects/docs.php#useobs)] | -- |
| incHours | If `whichData='hours'` | float,int | Observations within this many hours of the first one selected will be included in the spectrum. | 12 |
| timeslice | No | str | What spectra to create, must be one of {'single', 'user', 'snapshot', 'obsid'} | 'single' |
| grades | No | str |  What event grades to include. Can be 'all', '0' or '4' | 'all' |
| doNotFit | No | bool | Whether the skip the spectral fitting step. | True |
| galactic | No | bool | Whether to include an absorber fixed at the Galactic value, as well as a free absorber. | False |
| models | No | list/tuple | A list of emission models to fit (options are 'apec', 'powerlaw' and 'blackbody'). | ('powerlaw') |
| deltaFitStat | No | float | The change in fit statistic used to calculate the parameter errors on the spectral fit. | 2.706 |
| srcrad | No | int | The maximum radius the source extraction region can be (pixels). |  -- |

The last 3 parameters were newly introduced in v1.10 of the module (part of `swifttools` v3.0) and represent
functionality recently added to the service and also available via the website. If `galactic` is `True`, the value
of the Galactic component is taken from [Willingale et al., (2013)](https://ui.adsabs.harvard.edu/abs/2013MNRAS.431..394W/abstract).
The `models` parameter is case-insensitive and if it contains multiple elements then multiple models will be fitted.
**Note** Specifying multiple models will give separate fits with the different emisssion models. i.e. If you supply
`models=('apec', 'blackbody')` then you will get two fits, an absorbed APEC and an absorbed blackbody. You will **not** get
an absorbed "APEC+blackbody".

#### If defining specific sub-spectra

If timeslice=="user" then you must define the spectra you wish to create, giving each one a label (alphanumeric characters only) and a GTI interval, as defined in [the product generator documentation](https://www.swift.ac.uk/user_objects/docs.php#timeformat). You can specify between 1 and 4 spectra, using these parameters:

| Parameter | Mandatory? | Type  | Description | Default |
| :----     |  :----:    | :---: | :-----      | :----:  |
| rname1    | Yes  | str     | The name/label for the first spectrum | -- |
| gti1      | Yes  | str | The GTI expression for the first spectrum | -- |
| rname2    | No   | str     | The name/label for the second spectrum | -- |
| gti2      | No   | str | The GTI expression for the second spectrum | -- |
| rname3    | No   | str     | The name/label for the third spectrum | -- |
| gti3      | No   | str | The GTI expression for the third spectrum | -- |
| rname4    | No   | str     | The name/label for the fourth spectrum | -- |
| gti4      | No   | str | The GTI expression for the fourth spectrum | -- |

---

### Position parameters

There are three types of position: Standard, Enhanced and Astrometric.

Most of the position-related parameters are shared by these positions so only set once. If you have requested more than one position and change one of these 'shared' parameters for any of them, it will affect all of them.

| Parameter | Mandatory? | Type  | Description | Default |
| :----     |  :----:    | :---: | :-----      | :----:  |
| posRadius | No | float,int | How far the source can be from the input position, in arcsec. | 20 |
| whichData | No | str | Which datasets to use to get the position. Must be one of {'all', 'user', 'hours'} | 'hours' |
| useObs   | If `whichData='user'` | str | The specific observations to use to create the position [[Details](https://www.swift.ac.uk/user_objects/docs.php#useobs)] | -- |
| incHours | If `whichData='hours'` | float,int | Observations within this many hours of the first one selected will be included in the position. | 12 |


There is also a parameter for the astrometric position only:

| Parameter | Mandatory? | Type  | Description | Default |
| :----     |  :----:    | :---: | :-----      | :----:  |
| useAllObs | No | bool | Whether to force all available data to be used for this position | False |

The reason for this parameter is that both the
standard and enhanced positions tend to become systematics-limited relatively quickly (unless the source is very faint) so for speed reasons one may
choose not to use all data. However the astrometric position relies on matching serendipitous X-ray sources with 2MASS sources, and so the systematics
are strongly affected by how many X-ray sources were found. Thus, including all available data for the astrometric position can make a big difference.


---

### Image parameters

The following parameters can be set for creating an image.

| Parameter | Mandatory? | Type  | Description | Default |
| :----     |  :----:    | :---: | :-----      | :----:  |
| energies  | No | str | A string comprising a comma-separated list of energy bands for your images. | '0.3-10,0.3-1.5,1.51-10' |
| whichData | No | str | Which datasets to use in the image. Must be one of {'all', 'user'} | 'all' |
| useObs   | If `whichData='user'` | str | The specific observations to use to create the image [[Details](https://www.swift.ac.uk/user_objects/docs.php#useobs)] | -- |


---

### Source detection parameters

When requesting source detection **and no other products** you do not need to set the global parameters
RA, Dec, centroid or useSXPS, since these have no meaning for source detection.

The parameters below can be set for source detection. **Note that `whichData` is mandatory** unlike for other products.
This is because the setting this parameter to `all` should only be done consciously, and cautiously: requesting source
detection over a large number of datasets can take longer than the 12 hour runtime limit this facility supports.
Instead, we encourage you to identify which datasets you want to use for source detection, and set the `useObs` parameter
accordingly (which `whichData='user'`).

| Parameter | Mandatory? | Type  | Description | Default |
| :----     |  :----:    | :---: | :-----      | :----:  |
| whichData | Yes | str | Which datasets to use. Must be one of {'all', 'user'} | 'all' |
| useObs   | If `whichData='user'` | str | The specific observations to use for source searching [[Details](https://www.swift.ac.uk/user_objects/docs.php#useobs)] | -- |
| whichBands | No | str | Whether to use search the total energy band (`total`) or all SXPS energy bands (`all`) | 'Total' |
| fitStrayLight | No | Bool | Whether the code should try to identify and model stray light, if necessary. | True |
