from .swift_calendar import Swift_Calendar
from .api_common import TOOAPI_Baseclass
from .swift_instruments import TOOAPI_Instruments
from .api_status import TOOStatus
from .swift_obsid import TOOAPI_ObsID
from .api_skycoord import TOOAPI_SkyCoord
from .api_daterange import TOOAPI_Daterange, TOOAPI_TriggerTime
from .api_resolve import TOOAPI_AutoResolve

HAS_ASTROPY = False
try:
    import astropy.units as u

    HAS_ASTROPY = True
except ImportError:
    pass


class Swift_TOORequest(
    TOOAPI_Baseclass,
    TOOAPI_SkyCoord,
    TOOAPI_ObsID,
    TOOAPI_Instruments,
    TOOAPI_Daterange,
    TOOAPI_AutoResolve,
    TOOAPI_TriggerTime,
):
    """Class to construct a TOO for submission to Swift MOC. Class provides
    internal validation of TOO, based on simple criteria. Submission is handled
    by creating an signed JSON file, using "shared secret" to ensure that the
    TOO is from the registered party, and uploading via a HTTP POST to the Swift
    website. Verification of the success or failure of submission is reported
    into the TOOStatus class, which is populated using parameters
    reported by the  Swift TOO website upon submission.

    Attributes
    ----------
    l_name : str
        Proposers last name (default None)
    date_begin : datetime
        Date observations are scheduled to begin (default None)
    date_end : datetime
        Date observations are scheduled to end (default None)
    decision : str
        Decision on TOO (default None)
    xrt_mode_approved : int
        Approved XRT mode (default None)
    uvot_mode_approved : int
        Approved UVOT mode (default None)
    exp_time_per_visit_approved : int
        Exposure time per visit approved (default None)
    num_of_visits_approved : int
        Number of visits approved (default None)
    total_exp_time_approved : int
        Total approved exposure time in seconds (default None)
    target_id : int
        Target ID (default None)
    done : boolean
        Is the TOO considered to be complete (default None)
    status : TOOStatus
        status of request
    """

    # Name the class
    api_name = "Swift_TOO_Request"
    # Paramaters that get submitted as part of the JSON
    _parameters = [
        "username",
        "source_name",
        "source_type",
        "ra",
        "dec",
        "poserr",
        "instrument",
        "urgency",
        "opt_mag",
        "opt_filt",
        "xrt_countrate",
        "bat_countrate",
        "other_brightness",
        "grb_detector",
        "immediate_objective",
        "science_just",
        "exposure",
        "exp_time_just",
        "exp_time_per_visit",
        "num_of_visits",
        "monitoring_freq",
        "proposal",
        "proposal_id",
        "proposal_trigger_just",
        "proposal_pi",
        "xrt_mode",
        "uvot_mode",
        "uvot_just",
        "slew_in_place",
        "tiling",
        "number_of_tiles",
        "exposure_time_per_tile",
        "tiling_justification",
        "obs_n",
        "obs_type",
        "grb_triggertime",
        "debug",
        "validate_only",
        "quiet",
    ]
    # Alias parameter names
    _local = ["skycoord", "shared_secret", "xrt", "uvot"]
    # Attributes that may get returned
    _attributes = [
        "too_id",
        "timestamp",
        "decision",
        "done",
        "target_id",
        "date_begin",
        "date_end",
        "l_name",
        "xrt_mode_approved",
        "uvot_mode_approved",
        "calendar",
        "total_exp_time_approved",
        "num_of_visits_approved",
        "exp_time_per_visit_approved",
    ]
    # The three instruments on Swift
    instruments = ["XRT", "BAT", "UVOT"]
    # Common missions that that trigger detections
    mission_names = [
        "Fermi/LAT",
        "Swift/BAT",
        "INTEGRAL",
        "MAXI",
        "IPN",
        "Fermi/GBM",
        "IceCube",
        "LVC",
        "ANTARES",
        "ZTF",
        "ASAS-SN",
    ]
    # Valid units for monitoring frequency. Can add a "s" to each one if you like, so "3 orbits" is good.
    monitoring_units = [
        "second",
        "minute",
        "hour",
        "day",
        "week",
        "month",
        "year",
        "orbit",
    ]

    # English Descriptions of all the variables
    varnames = {
        "decision": "Decision",
        "done": "Done",
        "date_begin": "Begin date",
        "date_end": "End date",
        "calendar": "Calendar",
        "slew_in_place": "Slew in Place",
        "grb_triggertime": "GRB Trigger Time (UT)",
        "exp_time_per_visit_approved": "Exposure Time per Visit (s)",
        "total_exp_time_approved": "Total Exposure (s)",
        "num_of_visits_approved": "Number of Visits",
        "l_name": "Requester",
        "username": "Requester",
        "too_id": "ToO ID",
        "timestamp": "Time Submitted",
        "target_id": "Primary Target ID",
        "sourceinfo": "Object Information",
        "ra": "Right Ascenscion (J2000)",
        "dec": "Declination (J2000)",
        "source_name": "Object Name",
        "resolve": "Resolve coordinates",
        "position_err": "Position Error",
        "poserr": "Position Error (90% confidence - arcminutes)",
        "obs_type": "What is Driving the Exposure Time?",
        "source_type": "Type or Classification",
        "tiling": "Tiling",
        "immediate_objective": "Immediate Objective",
        "proposal": "GI Program",
        "proposal_details": "GI Proposal Details",
        "instrument": "Instrument",
        "tiling_type": "Tiling Type",
        "number_of_tiles": "Number of Tiles",
        "exposure_time_per_tile": "Exposure Time per Tile",
        "tiling_justification": "Tiling Justification",
        "instruments": "Instrument Most Critical to your Science Goals",
        "urgency": "Urgency",
        "proposal_id": "GI Proposal ID",
        "proposal_pi": "GI Proposal PI",
        "proposal_trigger_just": "GI Trigger Justification",
        "source_brightness": "Object Brightness",
        "opt_mag": "Optical Magnitude",
        "opt_filt": "Optical Filter",
        "xrt_countrate": "XRT Estimated Rate (c/s)",
        "bat_countrate": "BAT Countrate (c/s)",
        "other_brightness": "Other Brightness",
        "science_just": "Science Justification",
        "monitoring": "Observation Campaign",
        "obs_n": "Observation Strategy",
        "num_of_visits": "Number of Visits",
        "exp_time_per_visit": "Exposure Time per Visit (seconds)",
        "monitoring_freq": "Monitoring Cadence",
        "monitoring_freq_approved": "Monitoring Cadence",
        "monitoring_details": "Monitoring Details",
        "exposure": "Exposure Time (seconds)",
        "exp_time_just": "Exposure Time Justification",
        "xrt_mode": "XRT Mode",
        "xrt_mode_approved": "XRT Mode (Approved)",
        "uvot_mode": "UVOT Mode",
        "uvot_mode_approved": "UVOT Mode (Approved)",
        "uvot_just": "UVOT Mode Justification",
        "trigger_date": "GRB Trigger Date (YYYY/MM/DD)",
        "trigger_time": "GRB Trigger Time (HH:MM:SS)",
        "grb_detector": "GRB Discovery Instrument",
        "grbinfo": "GRB Details",
        "debug": "Debug mode",
        "validate_only": "Validate only",
        "quiet": "Quiet mode",
    }

    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        username : string
            Swift TOO username (default None)
        too_id : int
            TOO ID assigned by server on acceptance (default None)
        timestamp : datetime
            Timestamp that TOO was accepted (default None)
        source_name : string
            Name of the object we're requesting a TOO for (default None)
        source_type : string
            Type of object (e.g. "Supernova", "LMXB", "BL Lac")  (default None)
        ra : float
            RA(J2000) Degrees decimal (default None)
        dec : float
            declination (J2000) Degrees decimal (default None)
        poserr : float
            Position error in arc-minutes (default 0.0)
        instrument : string
            Choices "XRT","UVOT","BAT" (default "XRT")
        urgency : int
            TOO Urgency 1 = Within 4 hours, 2 = within 24 hours, 3 = Days to a
            week, 4 = week - month. (default 3)
        obs_type : str
            Select from obs_types one of four options, e.g. obs_types[1] ==
            'Light Curve'
        opt_mag : float
            UVOT optical magnitude (default None)
        opt_filt : string
            What filter was this measured in (can be non-UVOT filters) (default
            None)
        xrt_countrate : float
            XRT estimated counts/s (default None)
        bat_countrate : float
            BAT estimated counts/s (default None)
        other_brightness : float
            Any other brightness info (default None)
        grb_detector : str
            What detected this GRB (or other) trigger? Should be
            "Mission/Detector" (e.g "Swift/BAT, Fermi/LAT")
        grb_triggertime : datetime
            GRB trigger date/time (default None)
        immediate_objective : string
            One sentence explaination of TOO (default None)
        science_just : string
            this is the Science Justification (default None)
        exposure : int
            this is the user requested exposure in seconds
        exp_time_just : string
            Justification of monitoring exposure (default None)
        exp_time_per_visit : integer
            Exposure per visit in seconds (default None)
        num_of_visits : integer
            Number of visits (default 1)
        monitoring_freq : string / astropy.units
            Formatted text to describe monitoring cadence. E.g. "2 days", "3
            orbits", "1 week". See monitoring_units for valid units (default
            None)
        proposal : boolean
            Is this a GI proposal? (default False)
        proposal_id : string or integer
            What is the GI proposal ID (default None)
        proposal_trigger_just : string
            Note this is the GI Program Trigger Criteria Justification (default
            None)
        proposal_pi : string
            Proposal PI name (default None)
        xrt_mode : int
            XRT instrument mode. 7 = Photon Counting, 6 = Windowed Timing, 0 =
            Auto (self select). PC is default. (default 7)
        uvot_mode : int
            Hex mode for requested UVOT filter. Default FOTD. See Cheat Sheet or
            https://www.swift.psu.edu/operations/mode_lookup.php for codes.
            (default 0x9999)
        uvot_just : str
            Text justification of UVOT filter (default None)
        slew_in_place : boolean
            Perform a slew-in-place? Typically used for GRISM observation.
            Allows the source to be placed more accurately on the detector.
            (default None)
        tiling : boolean
            Is this a tiling request (default False)
        number_of_tiles : int
            Set this if you want a fixed number of tiles. Traditional tiling
            patterns are 4,7,19,37 "circular" tilings. If you don't set this
            we'll calculate based on error radius. (default None)
        exposure_time_per_tile : int
            exposure time per tile in seconds, otherwise it'll just be exposure
            / number_of_tiles (default None)
        tiling_justification : str
            Text description of why tiling is justified (default None)
        debug : boolean
            Debug mode (default None)
        """
        # User chooseable values
        self.username = None  # Swift TOO username (string)
        # Swift TOO shared secret. Log in to Swift TOO page to find out / change your shared secret
        self.shared_secret = None

        # These next two are assigned by the server, so don't set them
        self.too_id = None  # TOO ID assigned by server on acceptance (int)
        self.timestamp = None  # Timestamp that TOO was accepted (datetime)
        # Source name, type, location, position_error
        self.source_name = (
            None  # Name of the object we're requesting a TOO for (string)
        )
        # Type of object (e.g. "Supernova", "LMXB", "BL Lac")  (string)
        self.source_type = None
        self.ra = None  # RA(J2000) Degrees decimal (float)
        self.dec = None  # declination (J2000) Degrees decimal (float)
        self.poserr = 0.0  # Position error in arc-minutes (float)

        # Request details
        self.instrument = "XRT"  # Choices "XRT","UVOT","BAT" (string)
        # 1 = Within 4 hours, 2 = within 24 hours, 3 = Days to a week, 4 = week - month. (int)
        self.urgency = 3

        # Observation Type - primary goal of observation
        self.obs_types = ["Spectroscopy", "Light Curve", "Position", "Timing"]
        # Select from self.obs_types one of four options, e.g. self.obs_types[1] == 'Light Curve'
        self.obs_type = None

        # Description of the source brightness for various instruments
        self.opt_mag = None  # UVOT optical magnitude (float)
        # What filter was this measured in (can be non-UVOT filters) (string)
        self.opt_filt = None

        self.xrt_countrate = None  # XRT estimated counts/s (float)
        self.bat_countrate = None  # BAT estimated counts/s (float)
        self.other_brightness = None  # Any other brightness info (float)

        # GRB stuff
        # Should be "Mission/Detection" (e.g "Swift/BAT, Fermi/LAT") (string)
        self.grb_detector = None
        self.grb_triggertime = None  # GRB trigger date/time (datetime)

        # Science Justification
        # One sentence explaination of TOO (string)
        self.immediate_objective = None
        # Note this is the Science Justification (string)
        self.science_just = None

        # Exposure requested time (total)
        self._exposure = None  # Note this is the user requested exposure

        # Monitoring request
        # Justification of monitoring exposure (string)
        self.exp_time_just = None
        # Exposure per visit in seconds (integer)
        self.exp_time_per_visit = None
        self.num_of_visits = 1  # Number of visits (integer)
        # Formatted text to describe monitoring cadence. E.g. "2 days", "3 orbits", "1 week". See self.monitoring_units for valid units (string)
        self.monitoring_freq = None
        # GI stuff
        self.proposal = None  # Is this a GI proposal? (boolean)
        # What is the GI proposal ID (string or integer)
        self.proposal_id = None
        # Note this is the GI Program Trigger Criteria Justification (string)
        self.proposal_trigger_just = None
        self.proposal_pi = None  # Proposal PI name (string)

        # Instrument mode
        # 7 = Photon Counting, 6 = Windowed Timing, 0 = Auto (self select). PC is default (int)
        self._xrt = 7
        # Hex mode for requested UVOT filter. Default FOTD. See Cheat Sheet or https://www.swift.psu.edu/operations/mode_lookup.php for codes. (int)
        self._uvot = 0x9999
        self.uvot_just = None  # Text justification of UVOT filter (str)
        # Perform a slew-in-place? Typically used for GRISM observation. Allows the source to be placed more accurately on the detector. (boolean)
        self.slew_in_place = None

        # Tiling request
        self.tiling = None  # Is this a tiling request (boolean)
        # Set this if you want a fixed number of tiles. Traditional tiling
        # patterns are 4,7,19,37 "circular" tilings. If you don't set this we'll
        # calculate based on error radius. (int)
        self.number_of_tiles = None
        # Set this if you want to have a fixed tile exposure, otherwise it'll just be exposure / number_of_tiles (int)
        self.exposure_time_per_tile = None
        # Text description of why tiling is justified (str)
        self.tiling_justification = None

        # Calendar
        self._calendar = None

        # More parameters that are assigned server side
        self.l_name = None  # Proposers last name (str)
        # Date observations are scheduled to begin (datetime)
        self.date_begin = None
        # Date observations are scheduled to end (datetime)
        self.date_end = None
        self.decision = None  # Decision on TOO (str)
        self._xrt_mode_approved = None  # Approved XRT mode (int)
        self._uvot_mode_approved = None  # Approved UVOT mode (int)
        # Exposure time per visit approved (int)
        self.exp_time_per_visit_approved = None
        self.num_of_visits_approved = None  # Number of visits approved (int)
        # Total approved exposure time in seconds (int)
        self.total_exp_time_approved = None
        self.target_id = None  # Target ID (int)
        self.done = None  # Is the TOO considered to be complete (boolean)

        # Debug parameter - if this is set, sending a TOO won't actually submit it. Good for testing.
        self.debug = None  # Debug mode (boolean)
        self.quiet = False

        # Status of request
        self.status = TOOStatus()

        # Do a server side validation instead of submit?
        self.validate_only = None

        # Things that can be a subclass of this class
        self._subclasses = [Swift_Calendar]
        self.ignorekeys = True

        # Parse argument keywords
        self._parseargs(*args, **kwargs)

    @property
    def calendar(self):
        """If no calendar data exists for this TOO, fetch it."""
        if self.too_id is not None:
            if self._calendar.too_id is None:
                self._calendar.too_id = self.too_id
                self._calendar.submit()
        return self._calendar

    @calendar.setter
    def calendar(self, cal):
        self._calendar = cal

    @property
    def obs_n(self):
        """Is this a request for a single observation or multiple?"""
        if self.num_of_visits != "" and self.num_of_visits > 1:
            return "multiple"
        else:
            return "single"

    @obs_n.setter
    def obs_n(self, value):
        """Just ignore attempts to set this property"""
        pass

    def validate(self):
        """Validate API submission before submit

        Returns
        -------
        bool
            Was validation successful?
        """
        # Required arguments for a valid TOO
        requirements = [
            "ra",
            "dec",
            "num_of_visits",
            "exp_time_just",
            "source_type",
            "source_name",
            "science_just",
            "username",
            "obs_type",
        ]

        # Check that the minimum requirements are met
        for req in requirements:
            if self.__getattribute__(req) is None:
                self.status.error(f"Missing key: {req}")
                return False

        if self.obs_type not in self.obs_types:
            self.status.error(
                f"Observation Type needs to be one of the following: {self.obs_types}"
            )
            return False

        if self.instrument not in self.instruments:
            self.status.error(f"Instrument name ({self.instrument}) not valid")
            return False

        # If this is monitoring, we need time between exposures
        if self.num_of_visits > 1:
            if self.monitoring_freq is None or self.monitoring_freq == "":
                self.status.error("Need monitoring cadence.")
                return False

            if not self.exp_time_per_visit:
                self.exp_time_per_visit = int(self.exposure / self.num_of_visits)
            else:
                if self.exp_time_per_visit * self.num_of_visits != self.exposure:
                    self.status.warning(
                        "INFO: Total exposure time does not match total of individuals. Corrected."
                    )
                    self.exposure = self.exp_time_per_visit * self.num_of_visits
        else:
            if not self.exposure:
                self.exposure = self.exp_time_per_visit

        # Check monitoring frequency is correct
        if self.monitoring_freq is not None:
            if HAS_ASTROPY and type(self.monitoring_freq) is u.quantity.Quantity:
                if self.monitoring_freq.to(u.day).value >= (1 * u.day).value:
                    self.monitoring_freq = (
                        f"{self.monitoring_freq.to(u.day).value} days"
                    )
                else:
                    self.monitoring_freq = (
                        f"{self.monitoring_freq.to(u.hour).value} hours"
                    )

            _, unit = self.monitoring_freq.strip().split()
            if unit[-1] == "s":
                unit = unit[0:-1]
            if unit not in self.monitoring_units:
                self.status.error(f"Monitoring unit ({unit}) not valid")
                return False

        # Check validity of GI requests
        gi_requirements = ["proposal_id", "proposal_pi", "proposal_trigger_just"]
        if self.proposal:
            for req in gi_requirements:
                if getattr(self, req) is None:
                    self.status.error(f"Missing key: {req}")
                    return False

        # Check trigger requirements
        grb_requirements = ["grb_triggertime", "grb_detector"]
        if self.source_type == "GRB":
            for req in grb_requirements:
                if getattr(self, req) is None:
                    self.status.error(f"Missing key: {req}")
                    return False

        return True

    def server_validate(self):
        """Validate the TOO request with the TOO API server."""
        # Perform a _local validation first
        self.validate()
        # Do a server side validation
        if len(self.status.errors) == 0:
            # Preserve existing warnings
            warnings = self.status.warnings
            self.validate_only = True
            self.submit()
            self.validate_only = False
            self.status.warnings += warnings
            if len(self.status.errors) == 0:
                return True
            else:
                return False
        else:
            return False

    @property
    def _table(self):
        tab = list()
        if self.decision is not None:
            _parameters = [
                "too_id",
                "l_name",
                "timestamp",
                "urgency",
                "source_name",
                "source_type",
                "grb_triggertime",
                "grb_detector",
                "ra",
                "dec",
                "proposal_pi",
                "proposal_id",
                "proposal_trigger_just",
                "poserr",
                "science_just",
                "opt_mag",
                "opt_filt",
                "xrt_countrate",
                "other_brightness",
                "bat_countrate",
                "exp_time_per_visit_approved",
                "num_of_visits_approved",
                "total_exp_time_approved",
                "monitoring_freq",
                "immediate_objective",
                "exp_time_just",
                "instrument",
                "obs_type",
                "xrt_mode_approved",
                "uvot_mode_approved",
                "uvot_just",
                "target_id",
            ]
        else:
            _parameters = self._parameters
        for row in _parameters:
            val = getattr(self, row)
            if val is not None and val != "":
                tab.append([self.varnames[row], val])
        if len(tab) > 0:
            header = ["Parameter", "Value"]
        else:
            header = []
        return header, tab


# Aliases for class
Swift_TOO = Swift_TOORequest
TOO = Swift_TOORequest
TOORequest = Swift_TOORequest
Swift_TOO_Request = Swift_TOORequest
