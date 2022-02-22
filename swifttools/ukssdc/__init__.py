"""ukssdc module, providing API interface to UKSSDC services.

This module provices an interface to various services offered by the
UK Swift Science Data Centre, which have traditionally been provided 
via the website https://www.swift.ac.uk.

This README will be updated later.
"""

__all__ = ["APIURL"]

from .main import APIURL
from .version import __version__, _apiVersion