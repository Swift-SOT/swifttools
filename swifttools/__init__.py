"""
Module for astronomers using the Neil Gehrels Swift Observatory.

The `swifttools` module provides various features and functionality
designed to support users of the Swift satellite. The top-level 
module has no contents, instead you will need to use one of the 
sub-modules:

  * swifttools.swift_too -- Tools for submitting ToOs, and getting 
    visibility and observing history.
  * xrt_prods -- Tools for the automated analysis of XRT Data.
"""

from .version import __version__
