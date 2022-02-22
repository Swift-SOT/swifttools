"""ukssdc.data module, providing API interface to UKSSDC services.

This module provices an interface to various services offered by the
UK Swift Science Data Centre, which have traditionally been provided 
via the website https://www.swift.ac.uk.

This README will be updated later.
"""

__all__ = ["allowedConeRadiusUnits", "dataRequest"]
from .static import allowedConeRadiusUnits
# from .datarequest_base import dataRequest
from .obsData import obsDataRequest # noqa
from .SXPS import SXPSDataRequest # noqa
