# Change history for the `swifttools.ukssdc.xrt_prods` module

Changes made to this module after its original release will be documented here.

* 2024 May 29: xrt_prods v1.12 with `swifttools` v3.0.22
  * This release adds a new `srcrad` parameter to light curves and spectra, which sets the maximum size the source
  radius can extend to. This is only useful for rare, exteremly piled up sources where the annulus to exclude
  needs to be larger than the default 30-pixel maximum radius.
* 2022 August 31. xrt_prods v1.10 released, with swifttools 3.0.
  * This release contains many changes **including deprecating some old behaviour**. Full details
  are given in the [release notes](ReleaseNotes_v110.md).
* 2022 February 10, xrt_prods v 1.9 released, as part of swifttools 2.3.2 **users are encouraged to update ASAP**
  * This version adds the hardness ratios to the data downloaded by the retrieveLC() function.
  * It also changes the way that function works to support a back-end change. The old back end will be withdrawn at some point, breaking xrt_prods v1.8 and earlier.
* 2021 March 10, xrt_prods v1.8 released - adds better product download support.
  * New function `retrieveLightCurve()` to return the actual light curve data
  * New function `plotLC()` will generate a plot of the downloaded light curve.
  * New function `retrieveSpectalFits()` to download the automated spectal fit results.
* 2020 November 16, Python module v1.7 released **users are encouraged to update ASAP**
  * This version requires you to have python distutils/setuptools installed.
  * Edited the version check to support micro-releases (e.g. 1.6.1); future updates to the API
     may cause errors when using versions <1.7.
  * Added distutils as a dependency.
  * Various bug fixes
  * If you set the `useObs` parameter for any product, then `whichData` is automatically set to "user".
  * If you set the `whichData` parameter for any product to "all" then `useObs` is set to `None`.
  * NB, v 1.6 skipped due to upload error
* 2020 November 12, Python module v1.5 released - adds support for source detection.
* 2020 October 09, Python module v1.4 released  - minor bug fixes.
  * `wtHRBinTime` parameter spelling correcrted (WT was incorrectly upper case before).
  * Setting `pcBinTime` and `wtBinTime` did not work before, now fixed.
  * An error occured when using `retrieveStandardPos` or `retrieveAstromPos` for products where the position was not produced.
