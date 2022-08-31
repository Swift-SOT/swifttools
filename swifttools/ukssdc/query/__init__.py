"""ukssdc.query module, providing API interface to UKSSDC services.

This module provices an interface to various services offered by the
UK Swift Science Data Centre, which have traditionally been provided 
via the website https://www.swift.ac.uk.

This README will be updated later.
"""

__all__ = ["ObsQuery", "SXPSQuery", "GRBQuery"]
from .dataquery_base import dataQuery # noqa
from .obsData import ObsQuery # noqa
from .SXPS import SXPSQuery # noqa
from .GRB import GRBQuery # noqa
