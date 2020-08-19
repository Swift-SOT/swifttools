# Example JSON return from a job

When you submit a job then you should receive a JSON object. The structure of this object depends on whether your request was successfully processed, not. A description of the format is given in [the job submission API description](RequestJob.md); below we give two example JSON structures returned, one for a successful job, and one an unsuccessful one.

## A successful job

The example below shows the result of submitting the example GK Per spectrum request, [the second example here](JobRequestExamples2.md). Some comments have been added to the example below for clarity. In this example, Tstart, the targetIDs and the object coordinates were not provided in our job request, instead we used the `getT0`, `getTargs` and `getCoords` directives. We can find out what the values deduced and used by the system were from the relevant entries in the `jobPars` entry of the string.


```JSON
    {
    	"OK": 1,  // The job was submitted OK
    	"URL": "https://www.swift.ac.uk/user_objects/tprods/USERPROD_14",  // This is where the products are
			"JobID": "14",  // This will be needed for any other API functions related to this job.
			"APIVersion": 0.1,
    	"jobPars": { // This lists all of the parameters supplied, derived, or taken from the defaults.
    		"UserID": "pae9@leicester.ac.uk",
    		"name": "GK Per",
    		"getCoords": 1,
    		"getTargs": 1,
    		"getT0": 1,
    		"cent": 1,
    		"centMeth": "3",
    		"poserr": 60,
    		"spec": 1,
    		"specz": 0,
    		"timeslice": 1,
    		"specobs": 1,
    		"specgrades": "all",
    		"whatSXPS": "2SXPS",
    		"useSXPS": "2SXPS",
    		"lc": 0,
    		"image": 0,
    		"sss": "0",
    		"sinceT0": 0,
    		"lcobs": 0,
    		"hrbin": 0,
    		"dopsf": 0,
    		"doenh": 0,
    		"doxastrom": 0,
    		"allxastrom": 0,
    		"do3col": 0,
    		"enh": 0,
    		"outdir": "USERPROD_14",
    		"wtpuprate": 150,
    		"pcpuprate": 0.6,
    		"maxCentTries": "10",
    		"specobstime": 12,
    		"RA": "52.8000",
    		"Dec": "43.9043",
    		"targ": "{00010873,00010907,00010944,00030842,00031653,00045767,00010502,00060130,00060134,00060136,00060138,00060140,00060142,00060144,00060146,00060148,00060150,00060152,00060156,00060158,00060160,00067244,00069549,00069616,00074701}",
    		"Tstart": 124048802.40058
    	}
    }
```

## A failed job

Here is an example of the JSON returned for a job that could not be processed. As described on [the job submission page](RequestJob.md), the `ERROR` key will always be present and gives an overall error message. The `listErr` key is optional, but if present it is a nested structure comprising an array of errors, each of which has some explanatory 'label' followed by a list of related issues.

In the example below, `ERROR` tells us that the errors are related to the parameters we uploaded. `listErr` has two entries, so there are two sets of errors related to the parameters. The first is that the parameters "Dec" and "cent" were not supplied but are mandatory. The second is that the "poserr" parameter had an invalid value.

```JSON
    {
    	"OK": 0,
    	"ERROR": "There were problems with the parameters you supplied.",
    	"APIVersion": 0.1,
    	"listErr": [{
    		"label": "The following parameters are needed, but were not supplied:",
    		"list": ["Dec", "cent"]
    	}, {
    		"label": "The following parameters have invalid values:",
    		"list": ["poserr is 0.01, but must be between 1 and 6"]
    	}]
    }
```

