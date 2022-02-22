"""ukssdc module, providing API interface to UKSSDC services.

This module provices an interface to various services offered by the
UK Swift Science Data Centre, which have traditionally been provided 
via the website https://www.swift.ac.uk.

This README will be updated later.
"""

from .download import downloadObsData # noqa
from .SXPS import getSourceInfo as getSXPSSourceInfo # noqa
from .SXPS import getSourceLightCurve as getSXPSLightCurve # noqa
from .SXPS import saveLightCurves as saveSXPSSourceLightCurves # noqa
from .SXPS import getUpperLimit as getSXPSUpperLimit # noqa
from .SXPS import SXPS_LC_BINNING,SXPS_LC_TIMEFORMAT # noqa
# from .download import getFileList # noqa