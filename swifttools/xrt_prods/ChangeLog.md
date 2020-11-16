# Change history for the xrt_prods module.

Changes made to this module after its original release will be documented here.

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

