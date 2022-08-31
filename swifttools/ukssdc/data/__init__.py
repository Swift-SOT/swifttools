"""This module provides API interface to UKSSDC services.

The ukssdc.data module provices an interface to various services
offered by the UK Swift Science Data Centre, which have traditionally
been provided via the website https://www.swift.ac.uk.

The following functions are provided:

* downloadObsData() - download actual Swift observation data.
* getSXPSSourceInfo() - get extended information about an SXPS source.
* getSXPSLightCurves() - download lightcurve(s) of an SXPS source.
* saveSXPSLightCurves() - save SXPS lightcurve(s) to disk.
* getSXPSUpperLimit() - find an SXPS upper limit at a position.

"""

from .download import downloadObsData, downloadObsDataByTarget  # noqa

