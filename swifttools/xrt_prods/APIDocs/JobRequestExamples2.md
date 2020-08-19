# Example JSON structures

Following on from [the example JSON structures](JobRequestExamples1.md), this page lists some example JSON strings. The most basic way to execute a query is via `curl` with the JSON stored in a file. For example, if the first JSON example below was stored in the file `grb200416A_lc.json` then you could submit the job thus:

```bash
curl --data @grb200416A_lc.json --request POST https://www.swift.ac.uk/user_objects/run_userobject.php
```

Note that this will return a JSON structure; although JSON is readable by eye, it is probably preferable to submit the job from within a script which can then receive the JSON and parse it for you. For a brief tutorial covering submitting jobs, handling the returned JSON, and then checking job status, cancelling jobs or retrieving the products, see [the API tutorial](tutorial.md)

We are intending producing a Python module which will provide an easy-to-use interface for all steps: constructing the job request, submitting it, and handling the results. More details on that when I've done it and it's working.

-----

## Example 1: create a light curve of GRB 200416A

This structure will request a light curve of GRB 200416A, accepting all of the default parameters

```JSON
{
  "UserID":       "YOUR_EMAIL_HERE",  
  "name":         "GRB 200416A", 
  "targ":         "00966554",  
  "Tstart":       608713541,
  "RA":           335.6985,  
  "Dec":          -7.5179,  
  "cent":         1,
  "poserr":       1,   
  "lc":           1,
  "lctimetype":   "s",
  "binMeth":      "counts",
  "wtcounts":     30,
  "pccounts":     20,
  "wtbin":        0.5,
  "pcbin":        2.51,
  "dynamic":      1
}
```

## Example: build a spectrum of FO Aqr

This example would request a spectrum of FO Aqr, using all available data. The position, start time and targetIDs associated with Swift observations of FO Aqr are not supplied, instead we ask the system to work them out for us. This also calls the iterative centroid approach.

```JSON
{
  "UserID":       "YOUR_EMAIL_HERE",  
  "name":         "FO Aqr", 
  "getCoords":    1,
  "getTargs":     1,
  "getT0":        1,
  "cent":         1,
  "centMeth":     "iterative",   
  "poserr":       1,   
  "spec":         1,
  "specz":        0,
  "timeslice":    "single",
  "specobs":      "all",
  "specgrades":   "all"
}
```
