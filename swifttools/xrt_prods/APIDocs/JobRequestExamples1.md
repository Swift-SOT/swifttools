# Example JSON structures

Here are some example JSON structures that can be use to build products, broken up into the various sections, with some accompanying
notes. For the descriptions of these parameters, please see [the job submission API description](RequestJob.md).

**Note** none of these on their own can be submitted, these are all parts of the final JSON array which are separated off here
for ease of presentation and explanation.  The final submission should be a single JSON object, i.e. the different sections below should be merged (see [this second example set](JobRequestExamples2.md) for some examples). all into the same array.

Also do note that the comments (marked with `// comments`) should be removed for submission; they are just here to make
this documentation easier to read.

## Basic parameters

These are the parameters that must always be supplied. First, the mandatory ones.

```JSON
{
  "UserID":       "somone@somewhere.com",  // This must be the email address you registered with
  "name":         "GRB 200416A", // Unless you are using the name resolver (below), this is purely for plot titles
  "targ":         "",  // Can be omitted if getTargs is set (see below)
  "RA":           335.6985,  // Can be omitted if getCoords is set (see below)
  "Dec":          -7.5179,  // Can be omitted if getCoords is set (see below)
  "cent":         1,
  "centMeth":     2,   // This is only needed if cent = 1
  "maxCentTries": 10,  // This is only needed if cent = 1
  "poserr":       1,   // Arcminutes
}
```

### Optional extras for the basic parameters.

There are various optional parameters among the mandatory ones, given in the example below.
The options starting `get` will instruct the system to determine parameters from the name or target IDs as described in
[the job submission API description](RequestJob.md) if it can. This will override any values you set for these above.

```JSON
{
"Tstart":    608713541, // Given here in MET but many time systems are supported
"sinceT0":   0,
"getCoords": 1, // i.e. try to resolve the "name" parameter to work out the RA/Dec, overriding RA/Dec if they were supplied
"getTargs",  1, // Automatically select all targetIDs matching the coordinates
"getT0":     0, // Set T0 automatically to the start of the first observation matching the targetID.
"sss":       0,
"wtpuprate": 150,
"pcpuprate": 0.6,
"useSXPS":   1,
"notify":    1  
}
```

-----

## Light curve parameters

To request a light curve you must first set the `lc` parameter to `1`, and specify the binning method to be employed. There are various other options you 
can also specify if you want to override the defaults.  Some of the binning methods also have parameters you must set.

### Standard (global) light curve parameters

The only mandatory parameters to build a light curve are `lc` which should be `1` (i.e. to request the light curve), and `binMeth` which specifies which binning method to use. There are then several parameters controlling the light curve which are required regardless of binning method, all of which have default values. The example below shows setting all of these; the `binMeth` parameter is missing because it is included with the specific binning method examples.

```JSON
{
  "lc":          1,
  "sigmin":      3,
  "allowUL":     "both",
  "allowBayes":  "both",
  "bayesCounts": 15,
  "bayesSNR":    2.4,
  "lctimetype":  "s",
  "grades":      "all",
  "minen":       0.3,
  "maxen":       10,
  "soft1":       0.3,
  "soft2":       1.5,
  "hard1":       1.5,
  "hard2":       10,
  "femin":       0,
  "lcobs":       "all"
}
```

### Parameters for time binning.

For time binning there are a few parameters you can set, as below. The bin size (`wtbin`, `pcbin`) parameters are mandatory, but their HR counterparts are only needed if `hrbin` is 0, otherwise the hardness ratios match the binning from the main light curve.

```JSON
{
  "binMeth":     "time",
  "wtbin":        10,
  "pcbin":        100,
  "hrbin":        0,
  "wthrbin":      20,
  "pchrbin":      200
}
```

### Parameters for counts binning.

To build a light curve with bins based on the number of counts accumulated, you must set `binMeth` to `counts`. In this case the number of counts per bin is mandatory, but there are several optional parameters you can specify. **Note that dynamic binning is ON by default**.

```JSON
{
  "binMeth":   "counts",
  "wtcounts":  30,
  "pccounts":  20,
  "wtbin":     0.5,
  "pcbin":     2.51,
  "dynamic":   1,
  "ratefact":  10,
  "binfact":   1.5,
  "mincmin":   15,
  "minsnr":    1.5,
  "wtmaxgap":  100000000,
  "pcmaxgap":  100000000,
  "sigmin":    3
}
```


### Parameters for obsID / snapshot binning.

There are no special parameters to create one light curve bin per obsid or snapshot, just the `binMeth` parameter, i.e:

```JSON
{
  "binMeth":     "snapshot"
}
```

or

```JSON
{
  "binMeth":     "obsid"
}
```

-----

## Spectrum parameters

To request a spectrum you must set the `spec` parameter to `1`. There are various other options you can also specify if you want to override the defaults. In this example we are going to create a spectrum in which all obsIDs are used, but the spectrum
only covers a specific time range (corresponding to T0+0-1000 s).

```JSON
{
  "spec":        1,
  "specz":       1,
  "zval":        0.123,
  "specobs":     "all",
  "specgrades":  "all",
  "timeslice":   "user",
  "rname1":      "Early",
  "gti1":        "608713541-608714541" // If "sinceT0" was set to 1 above we could have this as "0-1000"
}
```


-----

## Position parameters

To request that a position be determined you must set `dopsf`, `doenh` or `doxastrom` to `1` to create a standard, enhanced or X-ray astrometrically corrected position respectively. Note that if `doxastrom=1` then `dopsf` is also set to 1, since a standard position is required to make an astrometrically-corrected one.

The example below requests all 3 positions: the standard and enhanced ones use only the data taken within 12 hours of the first observation (this is the normal setting for GRBs, since the object normally fades rapidly); for the astrometric position all data  are requested.

```JSON
{
  "posRadius":       20,
  "posobs":       "hours",
  "posobstime":   12,
  "detornot":     1,
  "detMeth":      0,
  "dopsf":        1,
  "doenh":        1,
  "doxastrom":    1,    
  "allxastrom":   1,
}
```

