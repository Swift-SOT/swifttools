# `swift_too` module

## Change history for `swift_too` module

### API version = 1.2, `swifttools` version 3.0

#### Author: Jamie A. Kennea (Penn State)

## `swifttools` 3.0.23` / `swift_too` 1.2.33

** Nov 13, 2024 **: Fix bug that caused crash when reading in UVOT modes in
`TOORequests` when `detail = True`.

## `swifttools` 3.0.21` / `swift_too` 1.2.32

** Feb 2, 2024 **: Add `triggertype` filter in `GUANO`

* Now with `GUANO` you can pass `triggertype` as an argument to filter on the
  type of trigger that you want. E.g. passing `triggertype = 'GBM GRB'` will
  return only triggers from Fermi/GBM. If you want to see examples of valid
  `triggertype` values, please visit here: https://www.swift.psu.edu/guano

## `swifttools` 3.0.20 / `swift_too` 1.2.31

** Nov 22, 2023**: Remove `requests` config that conflicted with another module.

* Configuration to use IPV4 only, required due to a networking issue at the server end, conflicts with some other Python module. This has now been removed.

## `swifttools` 3.0.18 / `swift_too` 1.2.30

**Oct 31, 2023**: Resolve issue with noisy warnings in `Data` even if `quiet=True`

* When downloading files using `Data` module, if those files already exist on disk a `warning` is now issued, instead of a printed warning. If `quiet=True` no warnings are issued.

## `swifttools` 3.0.17 / `swift_too` 1.2.29

**Oct 31, 2023**: Add AWS download support to `Data` class.

* Added option to download data from AWS instead of HEASARC. Add argument `aws=True` to `Data` class arguments to default to AWS downlink. For details of AWS data hosting, see [here](https://heasarc.gsfc.nasa.gov/docs/archive/cloud.html).

## `swifttools` 3.0.16 / `swift_too` 1.2.28

**March 22, 2023**: Warning about incorrectly formatted ISO8601 dates

* ISO8601 formatted dates without a timezone was assuming localtime, causing confusion. ISO8601 formatted dates should include a timezone specifier, e.g. '2022-01-01T00:00:00Z'. If no timezone is given, the code now issues a warning about this issue. Please use the "Z" for UTC times, as required for for the ISO8601 specification.

## `swifttools` 3.0.15 / `swift_too` 1.2.27

**March 17, 2023**: `TOORequests` fix

* Remove a print rogue print statement. Make sure status is cleared on `TOO` submission validation.

## `swifttools` 3.0.14 / `swift_too` 1.2.26

**March 17, 2023**: `TOORequests` fix

* Fixed a bug related to the last update, where `source_name` wasn't being set correctly.

## `swifttools` 3.0.13 / `swift_too` 1.2.25

**March 16, 2023**: `TOORequests` fix

* In a recent update, `TOORequests` was not correctly assigning the name of the TOO target name into `source_name`, this has been corrected.

## `swifttools` 3.0.12 / `swift_too` 1.2.24

**February 27, 2023**: GUANO update

* Each `GUANO_Entry` now has `uplinked` and `executed` flag, which indicate if the GUANO command has been uplinked to Swift, and executed onboard. If you set `successful=False` when executing a `GUANO` API call, it will load GUANO entries that have no data associated with them yet. This way, you can fetch recent GUANO commands that have not yet been fully processed by the Swift SDC.

## `swifttools` 3.0.11 / `swift_too` 1.2.23

**December 2, 2022**: Bug fix release

* Fix issue where trigger time in `GUANOEntry` did not get clock corrected.
* Fix issue where running `clock_correct()` on a zero length entry or an already corrected entry could cause a hang.

## `swifttools` 3.0.10 / `swift_too` 1.2.22

**November 30, 2022**: Update class names to new style. Add better support for date formats.

* Class names and aliases have been updated to be better PEP8 compliant across the board.
* Added support for accepting dates in ISO8601 format.
* Added support for accepting timezone aware `datetime`, they are converted to naive UTC `datetime` values internally.
* Extended `Swift_Calendar` to support searching for scheduling information. The Swift Scheduling Calendar is the long-term plan for Swift observations. Note that an entry into the Calendar does not guarantee that an observation will be scheduled, however it does mean that it is in the calendar to be scheduled for that day. You can now use `Calendar` class to query upcoming plans, by date range, coordinate, TOO ID and target ID.

## `swifttools` 3.0.8 / `swift_too` 1.2.21

**September 23rd, 2022**: Add `astropy` units support.

* Add `astropy` units support, so now for values like radius, lengths of time etc, you can add units using the standard `astropy.units` module. So for example, if you want to query the visibility of Sgr A* for the 2 weeks: `VisQuery(name='Sgr A*',length=2*u.week)`, or say query all observations within 30 arc-mins of the Vela Pulsar: `ObsQuery(name='Vela Pulsar',radius=30*u.arcmin)`.

* In preparation for a future update, many class aliases have been updated for better PEP8 compliance, and internal consistency. So for example, `UVOT_mode` becomes `UVOTMode` etc. The old class names still work, but will be deprecated upon moving to API version 1.3. Where necessary example Jupyter Notebooks are being updated for the new style class name.

## `swifttools` 3.0.6 / `swift_too` 1.2.20

**September 8nd, 2022**: Add `download` method

* Added `download` method for easy downloading of SDC data for any class with an associated observation id. See Jupyter notebook `UVOT_mode example notebook.ipynb` for examples of use.

## `swifttools` 3.0.4 / `swift_too` 1.2.19

**September 2nd, 2022**: Bug fix release

* Make error reporting for `UVOT_mode` consistent with other classes.

## `swifttools` 3.0.3 / `swift_too` 1.2.18

**September 2nd, 2022**: Add support for checking if UVOT mode is valid for a give coordinate

* Add mode checking to `UVOT_mode`. Now if you pass `ra` and `dec`, `skycoord` or use `name` to resolve a target name to coordinates, it will check if mode associated with `uvotmode` is valid for this position. This on the server side performs a bright star check, and if it fails for any reason, the request will be rejected with an error along the lines of 'The following UVOT filters are not allowed due to a bright star: White'.

## `swifttools` 2.4.9 / `swift_too` 1.2.17

**August 10th, 2022**: Subthreshold data support

* Add flag to `Swift_GUANO_Data` indicating if GUANO data are located in the "BAT Data For Subthreshold Triggers" section of the Swift SDC, rather than being associated with normal data. If this is true then `subthresh = True`, otherwise `subthresh = False`.
* Add support for downloading BAT subthreshold trigger data to `Swift_Data` (AKA `Data`). To download subthreshold trigger data, give the `obsid` and set argument `subthresh = True`. Data will be downloaded into a directory named after the obsid containing just the subthreshold trigger data.

## `swifttools` 2.4.8 / `swift_too` 1.2.16

**July 1st, 2022**: Bug fix release

* Revert default TOO_API submission to POST

## `swifttools` 2.4.7 / `swift_too` 1.2.15

**June 27th, 2022**: Bug fix release

* Fix issue where `quiet` option wasn't available in `Swift_Data` and only worked in Jupyter Notebooks.

## `swifttools` 2.4.6 / `swift_too` 1.2.14

**June 24th, 2022**: Bug fix and new feature release

* Fix issue in `Swift_Data` where `fetch` argument was not working.
* Add `match` argument to `Swift_Data` which allows user to filter on filenames using unix-style filename pattern matches. Multiple matches can be passed as a list, and files matching any of the matches will be downloaded.

## `swifttools` 2.4.5 / `swift_too` 1.2.13

**June 16th, 2022**: Bug fix release

* Fix issue with failing IPV6 access to API

## `swifttools` 2.4.4 / `swift_too` 1.2.12

**May 2nd, 2022**: Bug fix release.

* Minor bug fix.

## `swifttools` 2.4.3 / `swift_too` 1.2.11

**May 2nd, 2022**: Bug fix release.

* Fixed crash related to `keyring` module on macOS, where module was called non-interactively or over an ssh login.
* Other minor code cleanups.

## `swifttools` 2.4.2 / `swift_too` 1.2.10

**April 1st, 2022**: Added `Swift_SAA` method for calculating times when Swift is inside the South Atlantic Anomaly (SAA). Bug fix.

* `Swift_SAA` AKA `SAA` class added for calculating SAA passage times for the Spacecraft definition of SAA (default) or an estimate of the Burst Alert Telescope SAA passage times.
* Fix issue where running `clock_correct` multiple times could cause issues with times.

## `swifttools` 2.4.1 / `swift_too` 1.2.9

**March 29th, 2022**: Bug fix release

* Bug where `begin` and `end` properties of `GUANO` entries were not being set.

## `swifttools` 2.4 / `swift_too` 1.2.8

**March 28th, 2022**: Added clock correction through both `Swift_Clock` class and universal `clock_correct()` method.

* Add new class `Swift_Clock` that for a time in either Swift Time, UTC Time or Mission Elapsed Time (MET), will return an object containing all three, along with the Universal Time Correction Factor (UTCF) that is used to correct Swift Time to UTC. The UTCF corrects for both Swift's clock drift and for any leap seconds.
* Added `clock_correct()` method to classes that return dates. Using this you can add UTCF to any returned time, and thereofer MET, UTC and Swift Time using the `met`, `utc` and `swift` attributes.
* All times are now defined as `swiftdatetime` which is an extended version of datetime that is either based on Swift Time or UTC Time. `swiftdatetime` act like datetimes, except that you can now obtain MET, UTC, UTCF or Swift Time using the `met`, `utc`, `utc` or `swift` attributes. In additionthe `frommet` classmethod allows you to construct a `swiftdatetime` from an MET. `isutc` parameter defines if the basis of the `swiftdatetime` is UT time or Swift Time. Standard `datetime` arithmetic can be performed, however UTCF is not propogated.
* `GUANO` query results are now clock corrected by default, to avoid confusion.

## `swifttools` 2.3.1 / `swift_too` 1.2.7

**February 7th, 2022**: `swift_too` module updated to 1.2.7 with the following updates / fixes:

* Add option to `Swift_Data` to download from the Space Science Data Center in Italy. Set `itsdc = True` to download from Italian site, `uksdc = True` from the UK site. Default is to download from the HEASARC (US site).
* Bug fix in `Swift_GUANO` that could crash.

## `swifttools` 2.3 / `swift_too` 1.2.6

**February 3rd , 2022**: `swift_too` module updated to 1.2.5. Add new classes designed to make access to Swift SDC data easier, provide an API for accessing GUANO and universal name resolution. Here are the details of the upgrade

* *New class*: `Swift_GUANO`. This class and it's support classes allow for querying data generated by the *Gamma-Ray Urgent Archiver for Novel Opportunities* (GUANO).
* *New class*: `Swift_Data`. This class makes downloading of Swift data from the USA and UK Swift Data Centers easy.
* *New class*: `Swift_Resolve`. For a give source name, this returns the coordinates as resolved by various name resolvers.
* Automatic name resolution. Using the `Swift_Resolve` class, passing `name` parameter to classes that take coordinates (including `Swift_TOO`) will now automatically resolve the name to `ra`, `dec` and `skycoord` (if `astropy` is installed).
* Shortcut names for classes. Now instead of using class names like `Swift_ObsQuery` you can omit the `Swift_` and use the more simple `ObsQuery`.
* Better docstrings for all classes.
* Fix for crash when `shared_secret` is `None`, that can occur when `username != 'anonymous'`.
* Update how validation works for queries that don't use arguments.
* Various minor bug fixes and code updates.

## `swifttools` 2.2.2 / `swift_too` 1.2.4

**January 24th, 2022**: Bug fix release.

* Debug code was left in that was not compatible with earlier versions of python (e.g. 3.6). This has been removed.

## `swifttools` 2.2 / `swift_too` 1.2.3

**December 17th, 2021**: `swifttools` 2.2. Updates made in response to feedback from original release, and various quality of life improvements. Also new products can be fetched from the TOO API, details below.

* `keyring` support. If you have `keyring` installed and it works on your system, your `shared_secret` will be saved to it when you first pass it as an argument. On subsequent uses, you can give just your `username`.
* `SkyCoord` support. `astropy` `SkyCoord` objects can be returned instead of RA and Dec from any Class now, if `astropy` is installed. Note `astropy` will not be installed as a dependency of swifttools.
* Anonymous login by default: The default username for requests (except TOO requests) is now `anonymous`, meaning that requests can now be made without passing `username` and `shared_secret` at all.
* `Swift_TOO_Requests` support. This new request allows for the querying of approved Swift TOO requests sent to Swift by yourself and others. The approved XRT/BAT/UVOT modes and exposure time are reported. You can also choose to retrieve detailed information from the TOO Request, including justification texts. However, this detailed information is only available for TOOs you submitted.
* `Swift_Calendar` support. In this version you may retrieve calendar information for any TOO. These are automatically attached to entries in a `Swift_TOO_Requests` entry. The Calendar shows all planned observations for a TOO, along with an estimate of how much time was actually observed during the calendar window. Note that this is different from the Swift Plan, insofar as the Swift Calendar lists requested observations and can go much farther into the future. However, due to Swift's oversubscription, and other issues, even if an object is in the Calendar, that is not guarantee that Swift will observe it on that day, only that it is in the queue to be observed.
* `ra_point` and `dec_point` renamed to `ra_object` and `dec_object`. These attributes give the RA/Dec of the object that was the intended target of an observation. We note that the original choice of using ''point'' to indicate this is not consistent with other missions where ''point'' is used to indicate where the telescope pointed. For now, these new variables are simply aliases of `ra_point` and `dec_point`. These will be deprecated upon the release of the next API version (1.3), but not necessarily the next release of `swifttools`. API version will only be updated if compatibility of the API format needs to be broken, and every effort will be made to make API changes transparent to `swifttools` module users.
