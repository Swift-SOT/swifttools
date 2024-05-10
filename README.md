# Swifttools python package

This module presents tools to enable access from Python to some of the web-based
tools supporting the Swift satellite.

In the this release there are a two modules available: [ukssdc](swifttools/ukssdc/APIDocs/ukssdc/README.md) and
[swift_too](swifttools/swift_too/README.md).

`ukssdc` provides a Python interface to various services from the  [UK Swift Science Data
Centre](https://www.swift.ac.uk). This includes the [tools to build XRT data products](https://www.swift.ac.uk/user_objects),
interfaces to query catalogues such as [the LSXPS catalogue](https://www.swift.ac.uk/LSXPS) and tools to download
data, including [XRT GRB data products](https://www.swift.ac.uk/xrt_products) or [Swift obs data](https://www.swift.ac.uk/swift_live).

`swift_too` provides a Python interface for submitting Swift Target of Opportunity Requests, calculating visibility of
targets to Swift, querying observations that Swift has performed and will perform, and other Swift related tools.
Documentation for the `swift_too` module can be found here:
[https://www.swift.psu.edu/too_api/index.php](https://www.swift.psu.edu/too_api/index.php).
