# prodPythonParsToJSONPars manages any parameters where I'm using a
# different label in python than the JSON needs, this gives a look up -
# Python key : JSON value
prodPythonParsToJSONPars = {
    "lc": {
        "useObs": "uselcobs",
        "whichData": "lcobs",
        "allowBayes": "allowB",
        "timeType": "lctimetype",
        "timeFormat": "lctimetype",
        "minEnergy": "minen",
        "maxEnergy": "maxen",
        "softLo": "soft1",
        "softHi": "soft2",
        "hardLo": "hard1",
        "hardHi": "hard2",
        "minSig": "sigmin",
        "bintime": "wtbin",
        "minCounts": "mincmin",
        "matchHR": "hrbin",
        "wtHRBinTime": "wthrbin",
        "pcHRBinTime": "pchrbin",
        "minFracExp": "femin",
        "rateFact": "ratefact",
        "binFact": "binfact",
        "pcCounts": "pccounts",
        "wtCounts": "wtcounts",
        "pcBinTime": "pcbin",
        "wtBinTime": "wtbin",
        "minSNR": "minsnr",
        "wtMaxGap": "wtmaxgap",
        "pcMaxGap": "pcmaxgap",
    },
    "spec": {
        "hasRedshift": "specz",
        "redshift": "zval",
        "useObs": "usespecobs",
        "whichData": "specobs",
        "grades": "specgrades",
        "incHours": "specobstime",
        "specStem": "specstem",
        "deltaFitStat": "dchi"
    },
    "psf": {
        "whichData": "posobs",
        "useObs": "useposobs",
        "incHours": "posobstime",
        "detOrCent": "detornot",
        "centMeth": "detMeth",
    },
    "enh": {
        "whichData": "posobs",
        "useObs": "useposobs",
        "incHours": "posobstime",
        "detOrCent": "detornot",
        "centMeth": "detMeth",
    },
    "xastrom": {
        "useAllObs": "allxastrom",
        "whichData": "posobs",
        "useObs": "useposobs",
        "incHours": "posobstime",
        "detOrCent": "detornot",
        "centMeth": "detMeth",
    },
    "image": {
        "energies": "imen",
        "useObs": "useimobs",
        "whichData": "imobs"
    },
    "sourceDet": {
        "whichData": "detobs",
        "useObs": "usedetobs",
        "whichBands": "detbands"
    }
}

deprecatedPars = {
    "lc": {
        "timeType": "timeFormat",
    },
    "spec": {
    },
    "psf": {
    },
    "enh": {
    },
    "xastrom": {
    },
    "image": {
    },
    "sourceDet": {
    }
}

# prodNeedGlobals lists any global parameters which are required by a
# specific product
prodNeedGlobals = {
    "lc": ("centroid",),
    "spec": ("centroid",),
    "psf": (),
    "enh": (),
    "xastrom": (),
    "image": (),
    "sourceDet": ()
}
# prodUseGlobals shows any parameters that are shared between products,
# so will be handled as globals by this API, even though the user sets
# them for a specific product.
prodUseGlobals = {
    "lc": (),
    "spec": (),
    "psf": ("whichData", "incHours", "posRadius", "useObs", "detOrCent", "centMeth"),
    "enh": ("whichData", "incHours", "posRadius", "useObs", "detOrCent", "centMeth"),
    "xastrom": (
        "whichData",
        "incHours",
        "posRadius",
        "useObs",
        "detOrCent",
        "centMeth",
    ),
    "image": (),
    "sourceDet": ()
}

# prodNeedPars lists any parameters which are mandatory for the specific
# product
prodNeedPars = {
    "lc": ("binMeth",),
    "spec": ("hasRedshift", "deltaFitStat"),
    "psf": (),
    "enh": (),
    "xastrom": (),
    "image": (),
    "sourceDet": ("whichData",)
}

prodDefaults = {
    "lc": {},
    "spec": {"deltaFitStat": 2.706,},
    "psf": {},
    "enh": {},
    "xastrom": {},
    "image": {},
    "sourceDet": {}
}

# prodParTypes lists all possible parameters for each product, along
# with the type it should be This will be used as the check of whether a
# parameter is permitted, and whether it's OK
prodParTypes = {
    "lc": {
        "binMeth": (str,),
        "softLo": (float, int),
        "softHi": (float, int),
        "hardLo": (float, int),
        "hardHi": (float, int),
        "minSig": (float, int),
        "minEnergy": (float, int),
        "maxEnergy": (float, int),
        "grades": (str,),
        "allowUL": (str,),
        "allowBayes": (str,),
        "bayesCounts": (float, int),
        "bayesSNR": (float, int),
        "timeType": (str,),
        "timeFormat": (str,),
        "useObs": (str,),
        "pcCounts": (int,),
        "wtCounts": (int,),
        "pcBinTime": (float, int),
        "wtBinTime": (float, int),
        "dynamic": (bool,),
        "rateFact": (float, int),
        "binFact": (float, int),
        "minCounts": (int,),
        "minSNR": (float, int),
        "wtmaxGap": (float, int),
        "pcmaxGap": (float, int),
        "matchHR": (float, int),
        "wtHRBinTime": (float, int),
        "pcHRBinTime": (float, int),
        "minFracExp": (float, int),
        "whichData": (str,),
    },
    "spec": {
        "hasRedshift": (bool,),
        "redshift": (float,),
        "whichData": (str,),
        "useObs": (str,),
        "incHours": (float, int,),
        "timeslice": (str,),
        "grades": (str,),
        "rname1": (str,),
        "gti1": (str,),
        "rname2": (str,),
        "gti2": (str,),
        "rname3": (str,),
        "gti3": (str,),
        "rname4": (str,),
        "gti4": (str,),
        "specStem": (str,),
        "doNotFit": (bool,),
        "galactic": (bool,),
        "models": (list, tuple),
        "deltaFitStat": (float,)
    },
    "psf": {},
    "enh": {},
    "xastrom": {
        "useAllObs": (bool,)
    },
    "image": {
        "energies": (str,),
        "whichData": (str,),
        "useObs": (str,)
    },
    "sourceDet": {
        "useObs": (str,),
        "whichData": (str,),
        "whichBands": (str,),
        "fitStrayLight": (bool,)
    }
}


# prodSpecificParValues contains any parameters which can only be one of
# a subset of values, giving what that subset is
prodSpecificParValues = {
    "lc": {
        "binMeth": ("counts", "time", "snapshot", "obsid"),
        "allowUL": ("no", "pc", "wt", "both"),
        "allowBayes": ("no", "pc", "wt", "both"),
        "timeType": ("m", "s", "mjd", "sec"),
        "timeFormat": ("m", "s", "mjd", "sec"),
        "whichData": ("all", "user"),
        "grades": ("0", "all", "4")
    },
    "spec": {
        "whichData": ("all", "user", "hours"),
        "timeslice": ("single", "user", "snapshot", "obsid"),
        "grades": ("0", "all", "4")
    },
    "psf": {},
    "enh": {},
    "xastrom": {},
    "image": {
        "whichData": ("all", "user")
    },
    "sourceDet": {
        "whichData": ("all", "user"),
        "whichBands": ("total", "all")
    },
}

# prodParDeps lists any parameter dependencies, i.e. where parameter b
# is mandatory if parameter a is set, or set to a specific value.  For
# each product we have a dictionary with keys being the parameter a, and
# values being dictionaries again this time where the key is the value
# of parameter a, and the value is a tuple of the parameter bs, i.e.
# parameters needed if parameter a has this value.  parameters that are
# needed when parameter a is set, regardless of the value of parameter
# a, are stored with key 'ANY'
prodParDeps = {
    "lc": {
        "binMeth": {
            "too": ("pcBinTime", "wtBinTime"),
            "counts": ("pcCounts", "wtCounts", "dynamic"),
        },
        "whichData": {"user": ("useObs",)},
    },
    "spec": {
        "whichData": {"user": ("useObs",), "hours": ("incHours",)},
        "hasRedshift": {"True": ("redshift",), },
    },
    "psf": {},
    "enh": {},
    "xastrom": {},
    "image": {
        "whichData": {"user": ("useObs",)}
    },
    "sourceDet": {
        "whichData": {"user": ("useObs",)}
    },
}

# prodParTriggers lists cases where setting parameter a to some value
# causes parameter b to also take on a value So, for example below, if
# the 'redshift' parmeter is given any value then hasRedshift gets set
# to true
prodParTriggers = {
    "lc": {
        "useObs": {"ANY": {"whichData": "user"}},
        "whichData": {"all": {"useObs": None}}
    },
    "spec": {
        "redshift": {"ANY": {"hasRedshift": True, "galactic": True}, "NONE": {"hasRedshift": False}},
        "hasRedshift": {True: {"galactic": True}},
        "useObs": {"ANY": {"whichData": "user"}},
        "whichData": {"all": {"useObs": None}},
        "doNotFit": {True: {"hasRedshift": False}}
    },
    "psf": {
        "useObs": {"ANY": {"whichData": "user"}},
        "whichData": {"all": {"useObs": None}}
    },
    "enh": {
        "useObs": {"ANY": {"whichData": "user"}},
        "whichData": {"all": {"useObs": None}}
    },
    "xastrom": {
        "useObs": {"ANY": {"whichData": "user"}},
        "whichData": {"all": {"useObs": None}}
    },
    "image": {
        "useObs": {"ANY": {"whichData": "user"}},
        "whichData": {"all": {"useObs": None}}
    },
    "sourceDet": {
        "useObs": {"ANY": {"whichData": "user"}},
        "whichData": {"all": {"useObs": None}}
    },
}

# globalParTriggers lists cases where setting a global parameter to some
# value causes another global to also be changed.
globalParTriggers = {
    "useposobs": {"ANY": {"posobs": "user"}},
    "posobs": {"all": {"useposobs": None}},
    "T0": {"ANY": {"getT0": False}},
    "targ": {"ANY": {"getTargs": False}},
}

prodDownloadStem = {
    "lc": "lc",
    "spec": "spec",
    "psf": "psf",
    "enh": "enh",
    "xastrom": "xastrom",
    "image": "image",
    "sourceDet": "sourceDet"
}

skipGlobals = {
    "sourceDet": ("RA", "Dec", "centroid", "useSXPS"),
}
