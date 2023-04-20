"""The `swift_too` module provides a Python API that gives you almost
everything you need to plan and submit Target of Opportunity (TOOs) requests to
the Neil Gehrels Swift Observatory (hereafter *Swift*).

The module is split into the following main classes:

1. Swift_TOO 

This allows Target of Opportunity requests to be constructed and submitted. This
includes basic validation before submission, and querying of the status of the
request. This is used in the case where you either don't want to have to deal
with manual web forms, or you wish to submit a TOO request to Swift based on an
automated trigger, for example, if your telescope detects a new transient, and
you want Swift to observe it ASAP, you can automate the process of TOO
submission using this class. A debug mode is provided to allow you to test the
process of submitting a TOO request to completion, without actually submitting a
TOO.

2. Swift_ObsQuery

This class allows you to query what observations Swift has already performed. It
allows you to search for observations by target ID (a unique identifier for a
target) or Observation ID (a unique identifier for a single observation). Also
it allows for searches around fixed celestial coordinates, the default inputs
for this are J2000 right ascension (RA), declination (dec) and radius in decimal
degrees, however we also support astropy's `SkyCoord` to allow for other
coordinate systems to be used for searches, e.g. Galactic Coordinates. In
addition you can narrow the search to specific date ranges.

3. Swift_VisQuery

J2000 RA/dec (given as a `SkyCoord` or `ra` and `dec` properties in decimal
degrees). Before submitting a TOO request it's important that you understand if
a target can actually be observed by Swift. Targets are typically not observable
by Swift if they are closer than 45 degrees to the Sun, 21 degrees and to the
Moon. However, targets that are close to +/-69 in declination can exhibit
periodic pole constraints also that can cause visibility issues for ~10 day
periods. High resolution visibility can be requested, which gives object
visiblity at 1 minute timescales, and includes Earth occultation and periods
inside the South Atlantic Anomaly. As these are computationally expensive to
calculate, we limit high resolution visibliity requests to 20 days in length.

4. Swift_PlanQuery

Similar to Swift_ObsQuery but in this case queries the Swift observing plan,
otherwise known as the pre-planned science timeline (PPST). This allows the user
to query what was planned to be observed by Swift, and what will be observed in
the future. Please note that due to Swift's quick planning turn around, the
amount of information on future plans will be limited to the next 1-3 days
typically.

5. QueryJob

In addition results of jobs can be fetched using the QueryJob module. This can
be used to fetch results of already processed jobs, or query the current status
of a job. Typically a job will have 4 status values, `Queued`, `Processing`,
`Accepted` or `Rejected`. `Accepted` in this case means that processing has
completed. `Queued` means that the job has been accepted, but not yet processed.
`Processing` means that the server is working on the results, but has not yet
completed. `Rejected` means that the server rejected the job for any number of
reasons, that are reported by in `Swift_TOOStatus` class.

6. UVOT_mode

UVOT modes are typically given as hex modes. This class allows the user to look
up the meaning of a given hex code, which is typically a table of UVOT filters
associated with that mode, along with any configuration parameters, such as the
size of the field of view, whether the data will be taken in event mode, etc.

7. Swift_TOORequests

This class allows querying of TOO Requests submitted to Swift. By default this
will give detail on the most recent 10 TOO requests submitted to Swift.
Alternatively, TOOs info can be fetched by year, ID, RA/Dec/Radius, or within a
set time period. In addition if the `detail` parameter is set to `True`, then
this retrieves all information about a TOO request, including non-public
information, for TOO requests that you submitted, if you supply your `username`
and `shared_secret`. The class essentially is a container for a number of
`Swift_TOORequest` objects. In the case where targets are scheduled in the
Swift planning calendar, a `Swift_Calendar` object will be attached which lists
the scheduled windows, and shows how much exposure was obtained during those
windows.

8. Swift_Calendar

`Swift_Calendar` class allows for querying calendar entries for a given TOO. The
Calendar shows all planned observations for a TOO, along with an estimate of how
much time was actually observed during the calendar window. Note that this is
different from the Swift Plan, insofar as the Swift Calendar lists requested
observations and can go much farther into the future. However, due to Swift's
oversubscription, and other issues, even if an object is in the Calendar, that
is not guarantee that Swift will observe it on that day, only that it is in the
queue to be observed.

9. Swift_GUANO

`Swift_GUANO` provides API access to data obtained by the *Gamma-Ray Urgent
Archiver for Novel Opportunities* (GUANO). GUANO proactively dumps BAT event
data, which would otherwise be lost, based on external triggers. These triggers
include Fast Radio Bursts, Gamma-Ray Bursts from other missions, Gravitational
Wave triggers and Neutrino triggers. `Swift_GUANO` allows to query these dumps
and gives you metadata about the dump.

10. Swift_Data

`Swift_Data` provides an easy interface to download archival or quick-look data
from the Swift Science Data Centers in the USA or UK. 

11. Swift_Resolve

`Swift_Resolve` provides an simple interface to resolve target names into
coordinates, leveraging several name resolvers. This class is also called by
other classes when you pass the `name` parameter instead of giving an `ra`,
`dec` or `skycoord`.

12. Swift_Clock

For a given `utctime`, `mettime` or `swifttime` return a `swiftdatetime` object
or objects, with clock correction applied. Primarily used internally as part of
the `clock_correct` method, which applies clock correction to all times in a
given class.

13. Swift_SAA

Fetches times when Swift is passing through the South Atlantic Anomaly (SAA) for
a given time period.

Note that all module names have an alias that excludes the `Swift_` part, so for
example, `Swift_VisQuery` becomes `VisQuery`.

The Swift TOO API is built around a client/server model, in which API
information is exchanged between the client's machine with the Swift API server
in JSON format. Requests are submitted using a signed JWT (e.g. https://jwt.io)
format, and API users are required to register with Swift to use the API
(https://www.swift.psu.edu/toop) to submit TOO requests. JWT are not encrypted,
but they are signed with a "shared secret" to ensure that the requests are
coming from the user they say they are. Note that for all requests that are not
submitting a TOO, the username can be set to `anonymous`. In fact this is the
default if no username is given.

Queries are constructed using Python classes provided by this module, and
submitted to a queue system in which they are processed in a first come, first
served basis. Typically processing requests takes a 10-20 seconds. Status of
requests can be queried, and errors are reported back.
"""
from .version import version as __version__
from .swift_toorequest import Swift_TOO, TOO, TOORequest, Swift_TOO_Request
from .swift_obsquery import Swift_ObsQuery, ObsQuery
from .swift_visquery import Swift_VisQuery, VisQuery
from .query_job import QueryJob
from .swift_planquery import Swift_PlanQuery, PlanQuery
from .swift_uvot import UVOT_mode, UVOTMode, Swift_UVOTMode
from .swift_requests import Swift_TOO_Requests, TOORequests, Swift_TOORequests
from .swift_calendar import Swift_Calendar, Calendar
from .swift_guano import Swift_GUANO, GUANO
from .swift_data import Swift_Data, Data
from .api_resolve import Swift_Resolve, Resolve
from .swift_clock import Swift_Clock, Clock
from .swift_saa import Swift_SAA, SAA
