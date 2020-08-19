# Sending a request for products via the API

You should send a single JSON array, the keys of which are described below. Some are mandatory, some optional, and some are only needed if certain products are selected, as described below. For many parameters, defaults are listed which will be assigned if the parameters are not specified.

For parameters with a binary option yes/no (e.g. `cent`) the value should be 1 (meaning yes) or 0 (meaning no).

We have provided some [example JSON objects](JobRequestExamples1.md) which you can use as templates if you wish. 

Most fields are self-explanatory. Times can be entered in any of the [formats specified in the XRT Products documentation](https://www.swift.ac.uk/user_objects/docs.php#timeformat). the `useObs` fields can contain either a list of Swift obsIDs, or a comma-separated list of *start-stop* values, where start/stop are times in the formats just described. 

### Global parameters:

<dl title='Parameters related to all products'>
  <dt style='font-weight: bold;'>UserID [MANDATORY]</dt>
  <dd>The userID (=email address) with which you registered for this service.</dd>
  <dt style='font-weight: bold;'>name [MANDATORY]</dt>
  <dd>The name of the object (for cosmetic reasons).</dd>
  <dt style='font-weight: bold;'>targ</dt>
  <dd>The list of targetIDs to be used <strong>Mandatory unless <code>getTarg</code> is set</strong>.</dd>
  <dt style='font-weight: bold;'>Tstart</dt>
  <dd>The T0 point to use as a reference.</dd>
  <dt style='font-weight: bold;'>SinceT0</dt>
  <dd>Whether to assume all other time variables are relative to T0. Must be 0 or 1 (default: 0).</dd>
  <dt style='font-weight: bold;'>RA</dt>
  <dd>Object RA in decimal degrees <strong>Mandatory unless <code>getCoords</code> is set</strong>.</dd>
  <dt style='font-weight: bold;'>Dec</dt>
  <dd>Object dec in decimal degrees <strong>Mandatory unless <code>getCoords</code> is set</strong>.</dd>
  <dt style='font-weight: bold;'>cent [MANDATORY if a spectrum or light curve is created]</dt>
  <dd>Whether or not to try to centroid, must be 0 or 1.</dd>
  <dt style='font-weight: bold;'>centMeth</dt>
  <dd>How to centroid, must be one of {"simple", "iterative"} <strong>mandatory if cent == 1</strong> (default: "simple").</dd>
  <dt style='font-weight: bold;'>maxCentTries</dt>
  <dd>How many obsIDs to try centroiding on before giving up <strong>mandatory if cent == 1</strong> (default: 10).</dd>
  <dt style='font-weight: bold;'>posErr</dt>
  <dd>The distance from the input position the source can be <strong>mandatory if cent == 1</strong>.</dd>
  <dt style='font-weight: bold;'>sss</dt>
  <dd>Whether the source is super-soft, must be 0 or 1 (default: 0).</dd>
  <dt style='font-weight: bold;'>useSXPS</dt>
  <dd>Whether to use SXPS source lists where possible, must be 0 or 1 (default: 0).</dd>
  <dt style='font-weight: bold;'>wtpuprate</dt>
  <dd>The rate above which WT data are tested for pile up (default: 150).</dd>
  <dt style='font-weight: bold;'>pcpuprate</dt>
  <dd>The rate above which PC data are tested for pile up (default: 0.6).</dd>
  <dt style='font-weight: bold;'>notify</dt>
  <dd>Whether you wnt to be emailed when the products are complete, must be 0 or 1 (default: 0).</dd>
  <dt style='font-weight: bold;'>lc</dt>
  <dd>Whether to build a light curve, must be 0 or 1 (default: 0).</dd>
  <dt style='font-weight: bold;'>spec</dt>
  <dd>Whether to build a spectrum, must be 0 or 1 (default: 0).</dd>
  <dt style='font-weight: bold;'>image</dt>
  <dd>Whether to create an image, must be 0 or 1 (default: 0).</dd>
</dl>

There are extra options to determine some of the above for you. If these are set the automatically
calculated results will override any set above; if they cannot be calculated an error will be returned.
If successful, the calculated variables will be set in the JSON parameter string returned.

<dl title='Parameters requesting the system to determine some properties'>
  <dt style='font-weight: bold;'>getCoords</dt>
  <dd>Whether to resolve the name to get the coordinates, must be 0 or 1 (default: 0)</dd>
  <dt style='font-weight: bold;'>getT0</dt>
  <dd>Whether to try to get T0, must be 0 or 1 (default: 0)</dd>
  <dt style='font-weight: bold;'>getTargs</dt>
  <dd>Whether to try to getTarg, must be 0 or 1 (default: 0)s</dd>
</dl>

---

### Light curve parameters

To build a light curve the parameter `lc` must be set to `1` and then certain paramters specified.
`binMeth` is mandatory, to define how the data should be binned: as fixed-duration bins, bins based on the number of counts measured, or one bin per spacecraft snapshot or observation.

Some of the light curve parameters are relevant for all binning methods, some only for specific ones.

#### For all LC types

<dl title='Parameters related to light curve generation'>
  <dt style='font-weight: bold;'>binMeth [MANDATORY]</dt>
  <dd>What binning method to use. Must be one of {"counts", "time", "snapshot", "obsid"}.</dd>
  <dt style='font-weight: bold;'>minen</dt>
  <dd>Lower energy bound of the total band, in keV (default: 0.3).</dd>
  <dt style='font-weight: bold;'>maxen</dt>
  <dd>Upper energy bound of the total band, in keV (default: 10).</dd>
  <dt style='font-weight: bold;'>soft1</dt>
  <dd>Lower energy bound of the soft band, in keV, <strong>must be &geq;minen</strong> (default: 0.3).</dd>
  <dt style='font-weight: bold;'>soft2</dt>
  <dd>Upper energy bound of the soft band, in keV <strong>must be &;eq;maxen</strong> (default: 1.5).</dd>
  <dt style='font-weight: bold;'>hard1</dt>
  <dd>Lower energy bound of the hard band, in keV <strong>must be &geq;minen</strong> (default: 1.5).</dd>
  <dt style='font-weight: bold;'>hard2</dt>
  <dd>Upper energy bound of the hard band, in keV <strong>must be &leq;maxen</strong> (default: 10).</dd>
  <dt style='font-weight: bold;'>sigmin</dt>
  <dd>Minimum significance (in Gaussian &sigma;) for a point to be considered a detection (default: 3).</dd>
  <dt style='font-weight: bold;'>grades</dt>
  <dd>What event grades to include. Can be 'all' or '0' (default: all).</dd>
  <dt style='font-weight: bold;'>allowUL</dt>
  <dd>Whether upper limits are allowed. Must be one of {"no" "pc", "wt", "both"}, default: "both".</dd>
  <dt style='font-weight: bold;'>allowBayes</dt>
  <dd>Whether Bayesian bins are allowed. Must be one of {"no" "pc", "wt", "both"}, default: "both".</dd>
  <dt style='font-weight: bold;'>bayesCounts</dt>
  <dd>Threshold for counts in a bin, below which to use Bayesian statistics (default: 15).</dd>
  <dt style='font-weight: bold;'>bayesSNR</dt>
  <dd>Threshold for S/N in a bin, below which to use Bayesian statistics to measure count rate and error (default: 2.4).</dd>
  <dt style='font-weight: bold;'>lctimetype</dt>
  <dd>The units to use on the time axis. Must be one of {"s"(=seconds), "m"(=MJD)}, default: s</dd>
  <dt style='font-weight: bold;'>lcobs</dt>
  <dd>Whether to use specific observations. Must be one of {"all", "user"}, default: "all".</dd>
  <dt style='font-weight: bold;'>uselcobs</dt>
  <dd>Which observations to use for the LC  <strong>mandatory if lcobs=="user"</strong>.</dd>
</dl>

#### For &lsquo;counts&rsquo; binning

&lsquo;Counts&rsquo; binning is where a bin requires a certain number of counts to be considered complete (unless it spans the maximum inter-observation gap). This is the binning method by the [XRT GRB light curve repository](https://www.swift.ac.uk/xrt_curves).

<dl title='Parameters related to light curve fixed-counts binning'>
  <dt style='font-weight: bold;'>pccounts [MANDATORY]</dt>
  <dd>Minimum counts in a PC bin for it to be full (at 1 ct/sec if dynamic binning is on)</dd>
  <dt style='font-weight: bold;'>wtcounts [MANDATORY]</dt>
  <dd>Minimum counts in a WT bin for it to be full (at 1 ct/sec if dynamic binning is on)</dd>
  <dt style='font-weight: bold;'>pcbin</dt>
  <dd>Minimum bin duration in PC mode in seconds (default: 2.51).</dd>
  <dt style='font-weight: bold;'>wtbin</dt>
  <dd>Minimum bin duration in WT mode in seconds (default: 0.5).</dd>
  <dt style='font-weight: bold;'>dynamic [MANDATORY]</dt>
  <dd>Whether dynamc binning is on or off, must be 1 or 0.</dd>
  <dt style='font-weight: bold;'>ratefact</dt>
  <dd>Rate factor for dynamic binning (default: 10).</dd>
  <dt style='font-weight: bold;'>binfact</dt>
  <dd>Binning factor for dynamic binning (default: 1.5).</dd>
  <dt style='font-weight: bold;'>mincmin</dt>
  <dd>The absolute minimum counts/bin that dynamic binning can't fall below, unless the maxgap parameters below force truncation (default: 15).</dd>
  <dt style='font-weight: bold;'>minsnr</dt>
  <dd>The minimum S/N a bin must have to be considered full, unless the maxgap parameters below force truncation (default: 2.4)</dd>
  <!-- <dt style='font-weight: bold;'>wtmaxbin [MANDATORY]</dt>
  <dd>The maximum duration a WT mode bin can have - even if not 'full' it will be stopped at this length. <strong>Note - this is fixed (hidden input) on the HTML form</strong></dd>
  <dt style='font-weight: bold;'>pcmaxbin [MANDATORY]</dt>
  <dd>The maximum duration a PC mode bin can have - even if not 'full' it will be stopped at this length. <strong>Note - this is fixed (hidden input) on the HTML form</strong></dd> -->
  <dt style='font-weight: bold;'>wtmaxgap</dt>
  <dd>The maximum observing gap a WT mode bin can straddle - even if not 'full' it will be stopped at this length (default: 10<sup>8</sup> s).</dd>
  <dt style='font-weight: bold;'>pcmaxgap</dt>
  <dd>The maximum observing gap a PC mode bin can straddle - even if not 'full' it will be stopped at this length (default: 10<sup>8</sup> s).</dd>
</dl>

#### For fixed-time binning

In this method you specify the duration of the bins; e.g. 10-s per bin. Bins will not straddle observation gaps, and bin boundaries are reset to the start of an observation.

<dl title='Parameters related to light curve fixed-time binning'>
  <dt style='font-weight: bold;'>pcbin [MANDATORY]</dt>
  <dd>Bin duration in PC mode</dd>
  <dt style='font-weight: bold;'>wtbin [MANDATORY]</dt>
  <dd>Bin duration in WT mode</dd>
  <dt style='font-weight: bold;'>hrbin</dt>
  <dd>Whether the HR bin sizes should just be as for the main curve, must be 0 or 1 (default: 1).</dd>
  <dt style='font-weight: bold;'>wthrbin</dt>
  <dd>Bin duration for the HR in WT mode, <strong>mandatory if <code>hrbin</code> is not set</strong>.</dd>
  <dt style='font-weight: bold;'>pchrbin</dt>
  <dd>Bin duration for the HR in PC mode, <strong>mandatory if <code>hrbin</code> is not set</strong>.</dd>
  <dt style='font-weight: bold;'>femin</dt>
  <dd>Minimum fractional exposure a bin can have, bins with a lower fractional exposure are discarded (default: 0).</dd>
</dl>

---

### Spectrum parameters

#### For all spectra

<dl title='Parameters related to spectrum generation'>
  <dt style='font-weight: bold;'>specz [MANDATORY]</dt>
  <dd>Whether to include a redshift in the fit, must be 0 or 1</dd>
  <dt style='font-weight: bold;'>zval</dt>
  <dd>The redshift to apply, <strong>mandatory if specz==1</strong>.</dd>
  <dt style='font-weight: bold;'>specobs </dt>
  <dd>Which datasets to include in the spectrum. Must be one of {"all", "user", "hours"} (default: "hours").</dd>
  <dt style='font-weight: bold;'>usespecobs</dt>
  <dd>Time specification for user-specified observations for the spectrum, <strong>mandatory if specobs=="user"</strong>.</dd>
  <dt style='font-weight: bold;'>specobstime</dt>
  <dd>Observations within this many hours of the first one selected will be included in the spectrum, <strong>mandatory if specobs=="hours"</strong> (default: 12).</dd>
  <dt style='font-weight: bold;'>timeslice</dt>
  <dd>What spectra to create, must be one of {"single", "user", "snapshot", "obsid"} (default: "single").</dd>
  <dt style='font-weight: bold;'>specgrades</dt>
  <dd>What event grades to include. Can be "all" or "0" (default: all).</dd>
</dl>

#### If defining specific sub-spectra

If timeslice=="user" then you must define the spectra you wish to create, giving each one a label (alphanumeric characters only) and a GTI interval, as defined in [the product generator documentation](https://www.swift.ac.uk/user_objects/docs.php). You can specify between 1 and 4 spectra, using these parameters:

<dl title='Parameters related to spectral timeslice definition'>
  <dt style='font-weight: bold;'>rname1</dt>
  <dd>Name of the first spectrum</dd>
  <dt style='font-weight: bold;'>gti1</dt>
  <dd>GTI for the first spectrum</dd>
  <dt style='font-weight: bold;'>rname2</dt>
  <dd>Name of the second spectrum</dd>
  <dt style='font-weight: bold;'>gti2</dt>
  <dd>GTI for the second spectrum</dd>
  <dt style='font-weight: bold;'>rname3</dt>
  <dd>Name of the third spectrum</dd>
  <dt style='font-weight: bold;'>gti3</dt>
  <dd>GTI for the third spectrum</dd>
  <dt style='font-weight: bold;'>rname4</dt>
  <dd>Name of the fourth spectrum</dd>
  <dt style='font-weight: bold;'>gti4</dt>
  <dd>GTI for the fourth spectrum</dd>
</dl>

---

### Position parameters

<dl title='Parameters related to position generation'>
  <dt style='font-weight: bold;'>posRadius</dt>
  <dd>How far the source can be from the input position in arcsec (default: 20).</dd>
  <dt style='font-weight: bold;'>posobs</dt>
  <dd>Which datasets to use to get the position. Must be one of {"all", "user", "hours"} (default: "hours")</dd>
  <dt style='font-weight: bold;'>useposobs</dt>
  <dd>Time specification for user-specified observations for the position, <strong>mandatory if posobs="user"</strong>.</dd>
  <dt style='font-weight: bold;'>posobstime</dt>
  <dd>Observations within this many hours of the first one selected will be included in the position, <strong>mandatory if specobs=="hours"</strong> (default: 12).</dd>
  <dt style='font-weight: bold;'>detornot</dt>
  <dd>Whether to simply centroid around the specified position without checking that a source exists, or to carry out source detection first. Must be one of {"centroid", "detect"}. (default: "detect").</dd>
  <dt style='font-weight: bold;'>detMeth</dt>
  <dd>Whether to run a simple search, or the full SXPS approach. Must be one of {"simple", "iterative"}. <strong>mandatory if detornot=="detect"</strong>  (default: "simple").</dd>
  <dt style='font-weight: bold;'>doenh</dt>
  <dd>Whether to generate an enhanced position</dd>
  <dt style='font-weight: bold;'>dopsf</dt>
  <dd>Whether to generate a normal position (will be automatically enabled if xastrom is st)</dd>
  <dt style='font-weight: bold;'>doxastrom</dt>
  <dd>Whether to create an x-ray astrometrically improved position</dd>
  <dt style='font-weight: bold;'>allxastrom</dt>
  <dd>Whether to force the use of all available observations for the astrometric pos, even though they are not all used for the other positions (default: 0).</dd>
</dl>

---

### Image parameters

<dl title='Parameters related to image generation'>
  <dt style='font-weight: bold;'>imen</dt>
  <dd>A comma-separated list of energy bands for which to build images (default: "0.3-10,0.3-1.5,1.51-10").</dd>
  <dt style='font-weight: bold;'>imobs</dt>
  <dd>Which datasets to use to get the position. Must be one of {"all", "user"} (default: "all")</dd>
  <dt style='font-weight: bold;'>useimobs</dt>
  <dd>Time specification for user-specified observations for the image, <strong>mandatory if imobs="user"</strong>.</dd>
</dl>
