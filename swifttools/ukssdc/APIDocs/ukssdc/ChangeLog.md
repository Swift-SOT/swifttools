# Change history for the `swifttools.ukssdc` module

Changes made to this module after its original release will be documented here.

* 2024 May 29: v1.0.5 released as part of `swifttools` v3.0.22
  * `swifttools.ukssdc.xrt_prods` v1.12 released: adds a `srcrad` parameter for light curves and spectra.
* 2023 May 24: Modification to the back end, light curve `dict` now includes an "Exposure" column in the hard/soft/ratio datasets.
* 2022 September 06. v1.0.3 relased as part of `swifttools` v3.0.5
  * Further minor bugfixes in `mergeUpperLimits()`.
  * Fixed an issue only affecting Python >=3.9: the `math.factorial()` function now requires the argument
  to be an integer, it does not accept floats such as "3.0". This caused en error in `bayesRate()` as called
  by `mergeUpperLimits()` and `mergeLightCurveBins()`.
* 2022 September 01. v1.0.2 relased as part of `swifttools` v3.0.2
  * Minor bugfixes in `mergeUpperLimits()`
