# The `swifttools.ukssdc.xrt_prods` module

**Latest version v1.10, released in swifttools v3.0** ([Release notes](xrt_prods/ReleaseNotes_v110.md))

The `swifttools.ukssdc.xrt_prods` module provides the means to build Swift-XRT data products for point sources,
and is based on the [online tools](https://www.swift.ac.uk/user_objects). You will need to be [registered](https://www.swift.ac.uk/user_objects/register.php) to use this service.

This documentation describes how to use the Python interface. We assume that you are already familiar with the tools
themselves, and do not here describe their operation, allowable data formats (e.g. time systems supported) or the
detailed meanings of the various parameters. For this, please [read the product generator
documentation](https://www.swift.ac.uk/user_objects/docs.php).

**We still have a finite capacity, so please do not submit large numbers of jobs en masse**; instead you can use the API
to submit all of your jobs, but a few at a time, waiting until the requested jobs have completed before submitting the next tranche
([examples](xrt_prods/advanced.md#scripting-large-numbers-of-jobs)).

## Important notes for v1.10

The release of `swifttools` v3.0, including the new [`swifttools.ukssdc`](https://www.swift.ac.uk/API/ukssdc) module
necessitated a few changes to the `xrt_prods` module, in order to ensure homogeneous behaviour and formatting. These
are documented in the [version 1.10 release notes](xrt_prods/ReleaseNotes_v110.md). The key points to note are:

* To use the old behaviour, add the line `XRTProductRequest.useDeprecate = True` at the start of your scripts.
* The `swifttools.xrt_prods` module is now `swifttools.ukssdc.xrt_prods`; however `swifttools.xrt_prods` continues to serve
as a wrapper to this.
* We have [defined module-wide data models](https://www.swift.ac.uk/API/ukssdc/structures.md) for products such as light curves
and spectra, which are slightly different (more generic) than the previous version.
* There are new options for spectra: you can select different (or no) models to automatically fit.

In addition, due to the increased complexity of the system, we are no longer supporting (or documenting) the raw API,
but only the Python module. No-one has used the raw API since November 2020, and I think that was just me, testing, so we
don't expect this to inconvenience anyone.

## Documentation Contents:

* [Introduction / quickstart](xrt_prods/README.md)
* [How to request products](xrt_prods/RequestJob.md).
* [Examining your submitted job](xrt_prods/ReturnData.md).
* [How to cancel requested jobs](xrt_prods/CancelJob.md).
* [How to query the status of a job](xrt_prods/JobStatus.md).
* [How to retrieve the completed products](xrt_prods/RetrieveProducts.md).
* [A simple end-to-end tutorial](xrt_prods/tutorial.md).
* [Miscellaneous methods and advanced usage](xrt_prods/advanced.md).
* [ChangeLog](xrt_prods/ChangeLog.md)
