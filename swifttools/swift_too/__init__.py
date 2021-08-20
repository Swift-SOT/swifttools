'''The `swift_too` module provides a Python API that gives you almost 
everything you need to plan and submit Target of Opportunity (TOOs) 
requests to the Neil Gehrels Swift Observatory (hereafter *Swift*).

The module is split into four main classes:

1. Swift_TOO

This allows Target of Opportunity requests to be constructed and 
submitted. This includes basic validation before submission, and querying 
of the status of the request. This is used in the case where you either 
don't want to have to deal with manual web forms, or you wish to submit a 
TOO request to Swift based on an automated trigger, for example, if your 
telescope detects a new transient, and you want Swift to observe it ASAP, 
you can automate the process of TOO submission using this class. A debug 
mode is provided to allow you to test the process of submitting a TOO 
request to completion, without actually submitting a TOO.

2. Swift_ObsQuery

identifier for a target) or Observation ID (a unique identifier for a 
single observation). Also it allows for searches around fixed celestial 
coordinates, the default inputs for this are J2000 right ascension (RA), 
declination (dec) and radius in decimal degrees, however we also support 
astropy's `SkyCoord` to allow for other coordinate systems to be used for 
searches, e.g. Galactic Coordinates. In addition you can narrow the search 
to specific date ranges.

3. Swift_VisQuery

This class enables requesting of visibility information for a particular 
J2000 RA/dec (given as a `SkyCoord` or `ra` and `dec` properties in decimal
degrees). Before submitting a TOO request it's important that you understand 
if a target can actually be observed by Swift. Targets  are typically not 
observable by Swift if they are closer than 45 degrees to the Sun, 21 
degrees and to the Moon. However, targets that are close to +/-69 
in declination can exhibit periodic pole constraints also that can cause 
visibility issues for ~10 day periods. High resolution visibility can be 
requested, which gives object visiblity at 1 minute timescales, and 
includes Earth occultation and periods inside the South Atlantic Anomaly. 
As these are computationally expensive to calculate, we limit high 
resolution visibliity requests to 20 days in length.

4. Swift_PlanQuery

Similar to Swift_ObsQuery but in this case queries the Swift observing plan,
otherwise known as the pre-planned science timeline (PPST). This allows the
user to query what was planned to be observed by Swift, and what will be 
observed in the future. Please note that due to Swift's quick planning turn 
around, the amount of information on future plans will be limited to the next
1-3 days typically.

5. QueryJob

In  addition results of jobs can be fetched using the QueryJob module. 
This can be used to fetch results of already processed jobs, or query
the current status of a job. Typically a job will have 4 status values,
`Queued`, `Processing`, `Accepted` or `Rejected`. `Accepted` in this case
means that processing has completed. `Queued` means that the job has been
accepted, but not yet processed. `Processing` means that the server is 
working on the results, but has not yet completed. `Rejected` means that
the server rejected the job for any number of reasons, that are reported
by in `Swift_TOO_Status` class.

6. UVOT_mode

UVOT modes are typically given as hex modes. This class allows the user to look up
the meaning of a given hex code, which is typically a table of UVOT filters
associated with that mode, along with any configuration parameters, such as the size
of the field of view, whether the data will be taken in event mode, etc.

The Swift TOO API is built around a client/server model, in which API 
information is exchanged between the client's machine with the Swift API 
server in JSON format. Requests are submitted using a signed JWT 
(e.g. https://jwt.io) format, and API users are required to register with Swift 
to use the API (https://www.swift.psu.edu/toop). JWT are not encrypted, 
but they are signed with a "shared secret" to ensure that the requests are 
coming from the user they say they are. 

Queries are constructed using Python classes provided by this module, and 
submitted to a queue system in which they are processed in a first come, 
first served basis. Typically processing requests takes a 10-20 seconds. 
Status of requests can be queried, and errors are reported back. 


'''
from .version import __version__
from .too_client import Swift_TOO
from .swift_obsquery import Swift_ObsQuery
from .swift_visquery import Swift_VisQuery
from .query_job import QueryJob
from .swift_planquery import Swift_PlanQuery
from .swift_uvot import UVOT_mode
