# Data structures in the `ukssdc` module.

There are a few data structures used throughout the `swifttools.ukssdc` module, for which this page is
the reference.

These are:

* [Light curve `dict`s](#the-light-curve-dict)
* [Spectrum `dict`s](#the-spectrum-dict)
* [Burst Analyser `dict`s](#the-burst-analyser-dict)

The first two appear in quite a few places, the last one is only present for GRBs.
All three are explained and demonstrated below in some detail. In each case I first give a short explanation of
the structure, then an example, and then a detailed walkthrough the contents&dagger;. My hope is that you can glance over
the introduction and this will be enough that these make sense when you encounter them in the main
documentation. The full details are there for only when you really need them. But please do read them before contacting
me for help&hellip;

(&dagger; For the burst analyser `dict` I do not give a walkthrough. Since that data structure is only used
for GRBs the walkthrough appears on the [`swifttools.ukssdc.data.GRB` page](data/GRB.md#burst-analyser)).

## The light curve dict

Light curves are all stored in a `dict` following a specific structure, and referred to throughout
this documentation as a "light curve `dict`". This, as the name suggests, is a Python `dict` and
it contains the following keys:

* 'Datasets' - This is a list of all of the light curves downloaded.
* 'Binning' (optional) - The method used to bin the data.
* 'TimeFormat' (optional) - The time format used for the time axis.
* 'T0' (optional) - The zeropoint of the light curve, in Swift MET (see below).
* 'URLs' (optional) - A `dict` giving, for each light curve in `Datasets`, the URL to the light curve file.

There will also be a key for each entry in `Datasets`, the value of which is the actual light curve, in the form of a pandas `DataFrame`.
As you can see, not all of these keys need to exist for the object to be a light curve `dict`, only the  'Datasets'
key, and a key for each entry in 'Datasets' are guaranteed to exist.

This structure is probably best demonstrated, and the values explained, with an example:

```python
{
  'Datasets': ['WT', 'WT_incbad', 'PC', 'PC_incbad', 'PCUL', 'PCUL_incbad', 'PCHard', 'PCSoft', 'PCHR'],
  'Binning': 'Counts',
  'TimeFormat': 'MET',
  'T0': 672786064,
  'URLs': {'WT_incbad':'https://www.swift.ac.uk/xrt_curves/01104343/WTCURVE.qdp', ...}
  'WT_incbad': ...,
  'PC_incbad': ...,
  'PCUL_incbad': ...,
  ...
}
```

In the above I have suppressed some contents for readability. Now let's go through these
in turn and see what they mean,

### Datasets

```python
  'Datasets': ['WT', 'WT_incbad', 'PC', 'PC_incbad', 'PCUL_incbad', 'PCHard', 'PCSoft', 'PCHR'],
```

The 'Datasets' key is just a list of all the light curves contained in the set; the above is not exhaustive,
just intended to give a reasonable range. The format of the name is as follows:

`$mode$what$nosys$incbad`

Where the elements are:

$mode
: The XRT mode, "WT" or "PC".

$what
: The type of light curve. If blank, a normal light curve; "UL" indicates it contains upper limits, and
"Hard", "Soft", "HR" indicate that the data are the hard band, soft band or hardness ratio time series respectively.

$nosys
: Either blank or "_nosys"; the latter indicating that the WT-mode systematic errors have been removed.

$incbad
: Either blank or "_incbad"; the latter indicating that the datapoints where the XRT centroid could not be verified
have been excluded.

So, for example, the dataset "WT" is the WT-mode light curve, with systematics and without the unreliable datapoints.
"PCUL_incbad" is the PC-mode upper limits, including potentially unreliable datapoints.

For an explanation of the systematics and unreliable datapoints, please see the [the light curve
documentation](https://www.swift.ac.uk/user_objects/lc_docs.php#systematics).

### Binning

```python
  'Binning': 'Counts',
```

The 'Binning' entry is a single string indicating how the light curve was binned. This will be one of the following:

Counts
: Binned based on the counts per bin ("GRB-style")

Time
: Bins with fixed durations

Observation
: One bin for each Swift obsid.

Snapshot
: One bin for each snapshot (continuous pointing with Swift).

Unknown
: For some reason the binning method was not recorded.

### TimeFormat

```python
  'TimeFormat': 'MET',
```

The 'TimeFormat' entry tells you what the value in the Time columns actually mean. These can be

MJD
: Modified Julian Date (UTC)

TDB
: Barycentric dynamical time.

MET
: Swift Mission Elapsed Time. This is a value in seconds, either since the Swift reference time (2001 Jan 01 at 00:00:00 UTC),
or in seconds since the value in the 'T0' entry.

<a id='metwarn'></a>
Note that MET values are determined by the spacecraft onboard clock; to convert this to a universal time system such as
a UT calendar date, MJD etc, requires knowledge of the spacecraft clock drift and the leap second history. We recommend
using the `swifttime` tool included in `HEASoft`, which fully corrects for these effects.
### T0

```python
  'T0': 672786064,
```

The 'T0' entry gives the zeropoint used for the light curve. It is in Swift Mission Elapsed Time, which is seconds
since 2001 Jan 01 at 00:00:00 UTC (as counted by the spacecraft onboard clock). This is really only of interest if the 'TimeFormat' is 'MET'
since the other values are absolute anyway.

Please do note the warning above about converting MET to absolute time systems.

### URLs

```python
  'URLs' : {

    'WT': 'https://www.swift.ac.uk/xrt_curves/01104343/WTCURVE.qdp',
    'WT_incbad': 'https://www.swift.ac.uk/xrt_curves/01104343/WTCURVE.qdp',
    'PC': 'https://www.swift.ac.uk/xrt_curves/01104343/PCCURVE.qdp',
    'PC_incbad': 'https://www.swift.ac.uk/xrt_curves/01104343/PCCURVE_incbad.qdp',
    'PCUL_incbad': 'https://www.swift.ac.uk/xrt_curves/01104343/PCUL_incbad.qdp',
    'PCHard': 'https://www.swift.ac.uk/xrt_curves/01104343/PCHR.qdp',
    'PCSoft': 'https://www.swift.ac.uk/xrt_curves/01104343/PCHR.qdp',
    'PCHR': 'https://www.swift.ac.uk/xrt_curves/01104343/PCHR.qdp',
  }
```

The 'URLs' entry is a `dict` with a key for each of the datasets downloaded (and given in 'Datasets'). This points to the
raw light curve data file from which the `DataFrame`s were built, so you can readily get at the original files yourself if you wish.

### The actual light curves

And lastly we come to what you've been waiting patiently for: the actual light curves.

These are simply `pandas DataFrame` objects containing the light curve data. The columns depends on the light curve type,
and some examples (with the rows truncated) are given below. If you want full details of what each row means,
you'll need to see [the light curve documentation](https://www.swift.ac.uk/user_objects/lc_docs.php#format).

First, here's an example of a normal light curve (here, 'PC_incbad'):

<div style='width: 95%; max-height: 200px; overflow: scroll;'><style scoped>    .dataframe tbody tr th:only-of-type {        vertical-align: middle;    }    .dataframe tbody tr th {        vertical-align: top;    }    .dataframe thead th {        text-align: right;    }</style><table border="1" class="dataframe">  <thead>    <tr style="text-align: right;"><th></th><th>Time</th><th>TimePos</th><th>TimeNeg</th><th>Rate</th><th>RatePos</th><th>RateNeg</th><th>FracExp</th><th>BGrate</th><th>BGerr</th><th>CorrFact</th><th>CtsInSrc</th><th>BGInSrc</th><th>Exposure</th><th>Sigma</th><th>SNR</th></tr>  </thead>  <tbody><tr><th>0</th><td>231.329</td><td>9.456</td><td>-10.603</td><td>2.492634</td><td>0.547598</td><td>-0.547598</td><td>1.000000</td><td>0.006904</td><td>0.003088</td><td>2.396688</td><td>21.0</td><td>0.138491</td><td>20.058508</td><td>336.828549</td><td>4.551939</td></tr><tr><th>1</th><td>254.712</td><td>8.638</td><td>-13.928</td><td>2.458382</td><td>0.502403</td><td>-0.502403</td><td>1.000000</td><td>0.001227</td><td>0.001227</td><td>2.314148</td><td>24.0</td><td>0.027698</td><td>22.565840</td><td>865.481752</td><td>4.893247</td></tr><tr><th>2</th><td>272.685</td><td>10.724</td><td>-9.335</td><td>2.265870</td><td>0.510246</td><td>-0.510246</td><td>1.000000</td><td>0.006904</td><td>0.003088</td><td>2.288348</td><td>20.0</td><td>0.138491</td><td>20.058540</td><td>320.682615</td><td>4.440743</td>    </tr>  <tr><td colspan='13' style='text-align: left;'>&hellip;</td></tr>  </tbody></table></div>

An upper limit is similar, except that the "Rate" column is replaced with "UpperLimit":

<div style='width: 95%; max-height: 200px; overflow: scroll;'><style scoped>    .dataframe tbody tr th:only-of-type {        vertical-align: middle;    }    .dataframe tbody tr th {        vertical-align: top;    }    .dataframe thead th {        text-align: right;    }</style><table border="1" class="dataframe">  <thead>    <tr style="text-align: right;">      <th></th>      <th>Time</th>      <th>TimePos</th>      <th>TimeNeg</th>      <th>UpperLimit</th>      <th>RatePos</th>      <th>RateNeg</th>      <th>FracExp</th>      <th>BGrate</th>      <th>BGerr</th>      <th>CorrFact</th>      <th>CtsInSrc</th>      <th>BGInSrc</th>      <th>Exposure</th>      <th>Sigma</th>      <th>SNR</th>    </tr>  </thead>  <tbody>    <tr>      <th>0</th>      <td>246742.809</td>      <td>172770.106</td>      <td>-96881.981</td>      <td>0.001821</td>      <td>0.0</td>      <td>0.0</td>      <td>0.0364</td>      <td>0.000125</td>      <td>0.000005</td>      <td>1.6836</td>      <td>3.0</td>      <td>1.2247</td>      <td>9811.0649</td>      <td>1.4103</td>      <td>inf</td>    </tr>  </tbody></table></div>

The individual hard/soft band data are simpler and have symmetric errors on the rate:

<div style='width: 95%; max-height: 200px; overflow: scroll;'><style scoped>    .dataframe tbody tr th:only-of-type {        vertical-align: middle;    }    .dataframe tbody tr th {        vertical-align: top;    }    .dataframe thead th {        text-align: right;    }</style><table border="1" class="dataframe">  <thead>    <tr style="text-align: right;">      <th></th>      <th>Time</th>      <th>TimePos</th>      <th>TimeNeg</th>      <th>Rate</th>      <th>RateErr</th>    </tr>  </thead>  <tbody>    <tr>      <th>0</th>      <td>243.520</td>      <td>19.831</td>      <td>-22.794</td>      <td>1.323371</td>      <td>0.271083</td>    </tr>    <tr>      <th>1</th>      <td>292.350</td>      <td>31.176</td>      <td>-29.000</td>      <td>0.772638</td>      <td>0.174978</td>    </tr>    <tr>      <th>2</th>      <td>344.898</td>      <td>21.252</td>      <td>-21.372</td>      <td>1.128383</td>      <td>0.252669</td>    </tr>    <tr>      <th>3</th>      <td>396.489</td>      <td>32.344</td>      <td>-30.339</td>      <td>0.752788</td>      <td>0.168329</td>    </tr>    <tr>      <th>4</th>      <td>472.663</td>      <td>56.463</td>      <td>-43.830</td>      <td>0.469917</td>      <td>0.105224</td>    </tr>    <tr>      <th>5</th>      <td>594.830</td>      <td>69.690</td>      <td>-65.705</td>      <td>0.347482</td>      <td>0.078028</td>    </tr>    <tr>      <th>6</th>      <td>704.853</td>      <td>57.453</td>      <td>-40.332</td>      <td>0.478983</td>      <td>0.107709</td>    </tr>    <tr>      <th>7</th>      <td>823.036</td>      <td>74.665</td>      <td>-60.730</td>      <td>0.356802</td>      <td>0.078279</td>    </tr>    <tr>      <th>8</th>      <td>981.211</td>      <td>97.016</td>      <td>-83.510</td>      <td>0.260160</td>      <td>0.058751</td>    </tr>    <tr>      <th>9</th>      <td>1169.651</td>      <td>66.536</td>      <td>-91.425</td>      <td>0.294099</td>      <td>0.066134</td>    </tr>    <tr>      <th>10</th>      <td>1323.066</td>      <td>81.111</td>      <td>-86.879</td>      <td>0.305241</td>      <td>0.065412</td>    </tr>    <tr>      <th>11</th>      <td>1511.165</td>      <td>146.250</td>      <td>-106.988</td>      <td>0.183356</td>      <td>0.041583</td>    </tr>    <tr>      <th>12</th>      <td>1762.130</td>      <td>148.523</td>      <td>-104.715</td>      <td>0.193502</td>      <td>0.040547</td>    </tr>    <tr>      <th>13</th>      <td>6366.778</td>      <td>235.123</td>      <td>-253.803</td>      <td>0.075101</td>      <td>0.016944</td>    </tr>    <tr>      <th>14</th>      <td>7199.183</td>      <td>603.718</td>      <td>-597.281</td>      <td>0.045383</td>      <td>0.008396</td>    </tr>  </tbody></table></div>


And the hardness ratios are likewise simple:

<div style='width: 95%; max-height: 200px; overflow: scroll;'><style scoped>    .dataframe tbody tr th:only-of-type {        vertical-align: middle;    }    .dataframe tbody tr th {        vertical-align: top;    }    .dataframe thead th {        text-align: right;    }</style><table border="1" class="dataframe">  <thead>    <tr style="text-align: right;">      <th></th>      <th>Time</th>      <th>TimePos</th>      <th>TimeNeg</th>      <th>HR</th>      <th>HRErr</th>    </tr>  </thead>  <tbody>    <tr>      <th>0</th>      <td>243.520</td>      <td>19.831</td>      <td>-22.794</td>      <td>1.149509</td>      <td>0.344784</td>    </tr>    <tr>      <th>1</th>      <td>292.350</td>      <td>31.176</td>      <td>-29.000</td>      <td>0.566709</td>      <td>0.160379</td>    </tr>    <tr>      <th>2</th>      <td>344.898</td>      <td>21.252</td>      <td>-21.372</td>      <td>0.801010</td>      <td>0.240731</td>    </tr>    <tr>      <th>3</th>      <td>396.489</td>      <td>32.344</td>      <td>-30.339</td>      <td>0.775909</td>      <td>0.231541</td>    </tr>    <tr>      <th>4</th>      <td>472.663</td>      <td>56.463</td>      <td>-43.830</td>      <td>0.680760</td>      <td>0.197203</td>    </tr>    <tr>      <th>5</th>      <td>594.830</td>      <td>69.690</td>      <td>-65.705</td>      <td>0.562516</td>      <td>0.157879</td>    </tr>    <tr>      <th>6</th>      <td>704.853</td>      <td>57.453</td>      <td>-40.332</td>      <td>0.697443</td>      <td>0.203879</td>    </tr>    <tr>      <th>7</th>      <td>823.036</td>      <td>74.665</td>      <td>-60.730</td>      <td>0.809213</td>      <td>0.239284</td>    </tr>    <tr>      <th>8</th>      <td>981.211</td>      <td>97.016</td>      <td>-83.510</td>      <td>0.737809</td>      <td>0.219589</td>    </tr>    <tr>      <th>9</th>      <td>1169.651</td>      <td>66.536</td>      <td>-91.425</td>      <td>0.681327</td>      <td>0.199567</td>    </tr>    <tr>      <th>10</th>      <td>1323.066</td>      <td>81.111</td>      <td>-86.879</td>      <td>1.048259</td>      <td>0.322824</td>    </tr>    <tr>      <th>11</th>      <td>1511.165</td>      <td>146.250</td>      <td>-106.988</td>      <td>0.838212</td>      <td>0.258235</td>    </tr>    <tr>      <th>12</th>      <td>1762.130</td>      <td>148.523</td>      <td>-104.715</td>      <td>0.925555</td>      <td>0.267684</td>    </tr>    <tr>      <th>13</th>      <td>6366.778</td>      <td>235.123</td>      <td>-253.803</td>      <td>0.942488</td>      <td>0.298569</td>    </tr>    <tr>      <th>14</th>      <td>7199.183</td>      <td>603.718</td>      <td>-597.281</td>      <td>0.688193</td>      <td>0.165654</td>    </tr>  </tbody></table></div>

---

## The Spectrum dict

The spectrum `dict` contains, at core, information about extracted spectra and (if applicable) the fitted model(s).
An extra complexity arises because a given object will often have multiple spectra. To accommodate this the spectral
`dict` has, in all cases, three layers:

1. The spectra that exist (i.e. the time intervals over which spectra were built)
1. The XRT Modes
1. The fitted spectral model(s)

Even in cases where there is only one entry at a given level (e.g. there are only PC-mode data) all layers exist.
There are various relevant keywords in each layer as well. So, the conceptual map of a spectrum `dict` is as follows:

* 'T0' - The reference time.
* 'DeltaFitStat' - The delta fit-statistic used in getting parameter errors.
* 'GalNH_unfitted' (optional): The Galactic absorption column towards the source.
* **'rnames'** - a list of all the time intervals for which spectra were built.
* A `dict` for each entry in 'rname' which contains:
  * 'DataFile' - A URL to get the data for this spectrum
  * 'Start' - The start time of the requested time interval.
  * 'Stop' - The end time of the requested time interval.
  * **'Modes'** - a list of which XRT modes spectra were created
  * A `dict` for each entry in 'Modes' which contains:
      * 'MeanTime' - The mean time of the events in the spectrum.
      * 'Exposure' - The exposure time in the spectrum
      * **'Models'** - A list of which models were fitted.
      * A `dict` for each entry in models, giving details of the spectral fit.

Entries in boldface are lists, which give all the keys in the next layer.

Reading this in the abstract makes it looks rather more complex than it really is, and although I'll give an example
in a second, that en bloc is not really as readable as could be. So, perhaps the best way to explain
the concept is to show how you would actually access the spectral `dict`.

For [GRBs](https://www.swift.ac.uk/xrt_spectra),
there are normally two time slices, which (somewhat unhelpfully) are called "interval0" and "late_time", and only a power-law model fit. If I have the spectrum `dict` for some GRB in the variable `mySpec`, and
I want to know what the best-fitting spectral index was for a power-law fit to the WT model "interval0" spectrum, I can just do:

```python
print(mySpec['interval0']['WT']['Powerlaw']['Gamma])
```

This is somewhat more readable (I hope). There are a lot of layers but the layout is clear and, as you may have noticed, the order
of the keys is just the inverse of the order of my prosaic statement, which, to me at least, seems logical. Of course, if you want something
beyond a spectral fit parameter then you need to check at what level it is relevant, but hopefully this is also logical (and you can check
it on the list above). For example, the exposure by the "late_time" PC mode spectrum doesn't depend on which model was
fitted, so this value appears at the "rname/mode" level.

So, to unpack this a bit more, I will give below a real spectrum `dict` for a GRB, and then I'll move on to the detailed expanation of each key.

**One important note first**: In some cases it may be that the automated spectral fit failed, or you disabled
fitting; sometimes the spectrum for a given time interval could not be produced at all. In these cases the contents
of the various layers differ, as discussed [further down this page](#when-data-are-missing).

Right, let's take a look at a real spectrum `dict`. This is GRB 130925A, if you're interested, and I've added some
blank lines and indentation to try to make it a bit more readable.

```python
{ 'T0': 401775096,
  'DeltaFitStat': 2.706,
  'rnames': ['interval0', 'late_time'],
  'interval0':{
    'DataFile': 'https://www.swift.ac.uk/xrt_spectra/00571830/interval0.tar.gz',
    'Start': 151.206299126148,
    'Stop': 40413.0104033947,
    'Modes': ['WT', 'PC'],
    'WT': {
      'Models': ['PowerLaw'],
      'PowerLaw': {
        'GalacticNH': 1.74728e+20,
        'NH': 2.61822e+22,
        'NHPos': 4.195329499999989e+20,
        'NHNeg': -4.114560899999997e+20,
        'Redshift_abs': 0.347,
        'Gamma': 1.74059,
        'GammaPos': 0.01495348799999996,
        'GammaNeg': -0.014803381000000115,
        'ObsFlux': 3.2308738407058433e-09,
        'ObsFluxPos': 2.0927980842864315e-11,
        'ObsFluxNeg': -2.0775434446476415e-11,
        'UnabsFlux': 5.272662824293303e-09,
        'UnabsFluxPos': 4.9185968693846606e-11,
        'UnabsFluxNeg': -4.730966359732954e-11,
        'Cstat': 1389.742568,
        'Dof': 960,
        'FitChi': 1347.730724,
        'Image': 'https://www.swift.ac.uk/xrt_spectra/00571830/interval0wt_plot.gif'
        },
      'Exposure': 3162.851695179939,
      'MeanTime': 3449.54543888569
      },

    'PC': {
      'Models': ['PowerLaw'],
      'PowerLaw': {
        'GalacticNH': 1.74728e+20,
        'NH': 3.05251e+22,
        'NHPos': 3.1388244100000005e+21,
        'NHNeg': -2.9426779299999997e+21,
        'Redshift_abs': 0.347,
        'Gamma': 2.59379,
        'GammaPos': 0.1405418380000003,
        'GammaNeg': -0.13220066099999972,
        'ObsFlux': 7.526620170564824e-11,
        'ObsFluxPos': 3.860703494878197e-12,
        'ObsFluxNeg': -3.6410524464384235e-12,
        'UnabsFlux': 2.772043237577702e-10,
        'UnabsFluxPos': 5.272611683802778e-11,
        'UnabsFluxNeg': -3.991673128151661e-11,
        'Cstat': 487.9061045,
        'Dof': 490,
        'FitChi': 496.7632034,
        'Image': 'https://www.swift.ac.uk/xrt_spectra/00571830/interval0pc_plot.gif'
        },
      'Exposure': 5029.643800079823,
      'MeanTime': 17427.6717456579
      }
  },


  'late_time': {
    'DataFile': 'https://www.swift.ac.uk/xrt_spectra/00571830/late_time.tar.gz',
    'Start': 5502.69384342432,
    'Stop': 40413.0104033947,
    'Modes': ['PC'],
    'PC': {
      'Models': ['PowerLaw'],
      'PowerLaw': {
        'GalacticNH': 1.74728e+20,
        'NH': 3.15504e+22,
        'NHPos': 3.276992999999999e+21,
        'NHNeg': -3.0701709200000014e+21,
        'Redshift_abs': 0.347,
        'Gamma': 2.68868,
        'GammaPos': 0.14820270499999966,
        'GammaNeg': -0.13902135400000004,
        'ObsFlux': 6.826529950876817e-11,
        'ObsFluxPos': 3.594728145422862e-12,
        'ObsFluxNeg': -3.3616900080457612e-12,
        'UnabsFlux': 2.852200160603111e-10,
        'UnabsFluxPos': 6.096089137778289e-11,
        'UnabsFluxNeg': -4.542858750653171e-11,
        'Cstat': 450.7716251,
        'Dof': 470,
        'FitChi': 458.30322,
        'Image': 'https://www.swift.ac.uk/xrt_spectra/00571830/late_timepc_plot.gif'
        },
      'Exposure': 4966.961300075054,
      'MeanTime': 18497.190929234
      }
  }
}
```

Yowsers that's a lot to take in, but hopefully you can follow the structure. First, we had some information common
to all the spectra: the reference time and delta fitstat (discussed in a moment). Then the "rnames" list told us
that we have two spectra, "interval0" and "late_time". If you follow the indentation levels you will see that
the remaining two keys in this top-level `dict` were indeed "interval0" and "late_time". Within each of these
there was some information common to that spectral time-interval, and then "Modes", telling us for which modes
spectra were produced in this time interval. Then we have the keys "WT" and "PC" in the "interval0" spectrum, or just
"PC" for the "late_time" spectrum, and so on through the structure.

Honestly, that's probably (more than) enough to be going on with. You may want to glance at [When data are missing](#when-data-are-missing),
for completeness, but unless you're having trouble sleeping, you should only read on when you want more detail about a specific entry.
If you are having trouble sleeping, make sure you use a blue-light filter on the device you're reading with.

OK, let's go through the actual keys one at a time. Yay.

First, the top-level `dict`.

### T0

'T0' is a reference time for the spectrum in Swift Mission Elapsed Time. All other times are given relative
to this. Please do read [the notes on MET, above](#metwarn).

### DeltaFitStat

'DeltaFitStat' relates to the errors on the fitted parameters. These are determined by <code>xspec</code> by
stepping the parameter of interest and refitting until the fit statistic has increased 'DeltaFitStat'.
Ordinarily this is either 1 (or 1-&sigma; errors) or 2.706 (for 90% confidence errors), but in some  cases
you can set this to whatever you want.

### GalNH_unfitted

The 'GalNH_unfitted' value only appears for spectra where a Galactic absorber was not used. In these cases the expected
Galactic column along the line of sight to the source is given in the top level of the spectrum `dict`. It is given
purely for information - it was not used at all - and was taken from [Willingale et al.,
(2013)](https://ui.adsabs.harvard.edu/abs/2013MNRAS.431..394W/abstract).

### rnames

'rnames' is a list giving the labels applied to each time interval for which spectra were built. This essentially serves
as an index for the results. (NB 'rname' comes from 'region name', where a 'region' is a time region requested. Had I realised,
when writing the spectral code in 2008, that one day I was going to expose its workings via an API, I would have used
a better label).

That is it for the standard contents of the top level. There will still be one key for each entry in 'rnames',
containing the details of what was produced for that time interval. So, let's go through the contents of each of these now.

### DataFile

The 'DataFile' entry contains a URL pointing to a '.tar.gz' archive which contains all of the files for the
spectra for this time interval. This can be used by you to download the spectrum if you want to fit or manipulate it
yourself. It is also used by the [saveSpectra()](commonFunc.md#savespectra) function that appears throughout
the `swifttools.ukssdc` module.

### Start

The 'Start' entry contains the start time in seconds since 'T0' of the *requested* time interval. This does not necessarily
correspond to the time covered by any of the actual spectra, since that depends on the availability of data.

### Stop

The 'Stop' entry contains the stop time in seconds since 'T0' of the *requested* time interval. This does not necessarily
correspond to the time covered by any of the actual spectra, since that depends on the availability of data.

### NOSPEC

If no spectra could actually be created for this time interval, then the key 'NOSPEC' will exist, and the `dict` for this
time interval will terminate here.

### Modes

The 'Modes' key contains a list of the XRT modes for which spectra were created for this time interval.

And this is again, the end of the layer, the above defines the standard contents for each time interval.
But of course, there is now an entry for each of the modes (listed in 'Modes') for which we have a spectrum.
So, let's move on...

For each mode within each time interval, the `dict` will have these keys:

### MeanTime

The 'MeanTime' entry contains the mean time of the X-ray events in the spectrum for this time interval and mode.
It is in seconds since T0.

### Exposure

The 'Exposure' entry gives the exposure time, in seconds, in the spectrum for this time interval and mode.

### NOFIT

If, when requesting spectra be built, you also requested that they not be fitted automatically then there will
be the 'NOFIT' key at this level and (strangely enough) no further information, since all that remains pertains to the
automated fits.

### Models

The 'Models' key contains a list of the spectral models that were requested for fitting.

And we are now, finally, almost at an end. The only thing that remains at this level (time interval -> XRT Mode) is
one entry for each model that was requested for automatic fitting. These have keys given in the 'Models' entry just described,
and they are themselves `dict`s. The keys of these `dict`s depend upon the model, you can see from the example
earlier a typical example: for a blackbody or APEC fit "Gamma" will be replaced with "kT" and whether or not a redshift
accompanies the absorber depends on the request via which the spectrum was built.

Sometimes the automated spectral fit fails. In this case there will be a 'NOFIT' entry at this level.

There is also a key "Image" which gives the URL to an image of the spectrum and fitted model.

Phew. If you're stll awake, well done!

### When data are missing

One very last thing to note. Sometimes, things can be missing. Below I have listed what can happen,
and what the spectrum `dict` looks like in these cases.

No spectrum exists for the object requested.
: The top level of the `dict` contains the key "NoSpectrum". The other keys are absent.

The spectrum for a given time interval could not be produced.
: The [rname] `dict` for the given time interval contains the key "NOSPEC"; the "Modes" key is absent.

Automatic fitting was not requested for the spectrum.
: The [rname][mode] `dict` for each time interval and mode contains the key "NOFIT"; the "Models" key is absent.
You may wonder why this isn't just given at the top level: the reason is that an [rname][mode] tree
still exists and contains all of the information about the spectrum, so it seems logical to indicate
that there is no fit at this level, where you will be otherwise looking for the "Models" entry.

The automatic fit could not be produced.
: The [rname][mode][model] `dict` for the specific time interval, model and model contains the key "NOFIT"; the results
of the fit are (obviously) absent.

---
## The Burst analyser dict

The burst analyser `dict` is a nested `dict` with several layers, just like the structures above.
The overall structure is

* Instruments
  * BAT binning
    * Light curves

but things are slightly more complicated; the "BAT binning" layer is only present in one of the "Instrument" layers (the
BAT) and hardness ratio data move around a bit. The full schematic is below, and I have skipped some of the data
(especially all the actual light curves) and added some comments to make this more readable. For a walkthrough of the
contents, see the [`swifttools.ukssdc.data.GRB` page](data/GRB.md#burst-analyser)). The main point to note is that
this structure basically holds a lot of [light curve `dict`s](#the-light-curve-dict), organised by Swift instrument,
(by binning for BAT only), and by energy band. For BAT and XRT there is also a hardness ratio time series (which includes
the photon index and ECF inferred from the hardness ratio).


```python
{
  'Instruments': ['BAT', 'BAT_NoEvolution', 'XRT', 'UVOT'],
  'BAT': {
    'HRData': <a DataFrame containing the hardness ratio>,
    'Binning': [
      'SNR4',
      'SNR4_sinceT0',
      'SNR5',
      'SNR5_sinceT0',
      'SNR6',
      'SNR6_sinceT0',
      'SNR7',
      'SNR7_sinceT0',
      'TimeBins_4ms',
      'TimeBins_64ms',
      'TimeBins_1s',
      'TimeBins_10s'],
    'SNR4': {
      'Datasets': ['ObservedFlux', 'Density', 'XRTBand', 'BATBand'],
      'ObservedFlux': <a DataFrame containing the light curve>,
      'Density': <a DataFrame containing the light curve>,
      'XRTBand': <a DataFrame containing the light curve>,
      'BATBand':  <a DataFrame containing the light curve>
    }
    'SNR4_sinceT0': {
      'Datasets': ['ObservedFlux', 'Density', 'XRTBand', 'BATBand'],
      'ObservedFlux': <a DataFrame containing the light curve>,
      'Density': <a DataFrame containing the light curve>,
      'XRTBand': <a DataFrame containing the light curve>,
      'BATBand':  <a DataFrame containing the light curve>
    }
    ... more entries, as above, one for each entry in 'Binning'

  }, # End of ['BAT']
  'BAT_NoEvolution': {
    'ECFs': {
      'ObservedFlux': 0.00243424007095474,
      'Density': 0.00231776220799315,
      'XRTBand': 4.70354458026304e-08,
      'BATBand': 6.85253672780114e-07
    },
    'Binning': [
      'SNR4',
      'SNR4_sinceT0',
      'SNR5',
      'SNR5_sinceT0',
      'SNR6',
      'SNR6_sinceT0',
      'SNR7',
      'SNR7_sinceT0',
      'TimeBins_4ms',
      'TimeBins_64ms',
      'TimeBins_1s',
      'TimeBins_10s']
    'SNR4': {
      'Datasets': ['ObservedFlux', 'Density', 'XRTBand', 'BATBand'],
      'ObservedFlux': <a DataFrame containing the light curve>,
      'Density': <a DataFrame containing the light curve>,
      'XRTBand': <a DataFrame containing the light curve>,
      'BATBand':  <a DataFrame containing the light curve>
    }
    'SNR4_sinceT0': {
      'Datasets': ['ObservedFlux', 'Density', 'XRTBand', 'BATBand'],
      'ObservedFlux': <a DataFrame containing the light curve>,
      'Density': <a DataFrame containing the light curve>,
      'XRTBand': <a DataFrame containing the light curve>,
      'BATBand':  <a DataFrame containing the light curve>
    }
    ... more entries, as above, one for each entry in 'Binning'
  }, # End of ['BAT_NoEvolution']

  'XRT': {
    'HRData_PC': <a DataFrame containing the hardness ratio>
    'Datasets': [
      'ObservedFlux_PC_incbad',
      'Density_PC_incbad',
      'XRTBand_PC_incbad',
      'BATBand_PC_incbad'
    ],
    'ObservedFlux_PC_incbad': <a DataFrame containing the light curve>,
    'Density_PC_incbad': <a DataFrame containing the light curve>,
    'XRTBand_PC_incbad': <a DataFrame containing the light curve>,
  }, , # End of ['XRT']
  'UVOT': {
    'Datasets': ['white', 'b', 'u', 'v', 'uvw1', 'uvw2', 'uvm2']
    'white':  <a DataFrame containing the light curve>,
    'b': <a DataFrame containing the light curve>,
    'u': <a DataFrame containing the light curve>,
    'v': <a DataFrame containing the light curve>,
    'uvw1': <a DataFrame containing the light curve>,
    'uvw2': <a DataFrame containing the light curve>
  }
}
```
