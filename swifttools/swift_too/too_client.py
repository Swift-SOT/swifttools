from .common import TOOAPI_Baseclass,xrtmodes,modesxrt
from .too_status import Swift_TOO_Status

class Swift_TOO(TOOAPI_Baseclass):
    '''Class to construct a TOO for submission to Swift MOC. Class provides internal validation of TOO, 
    based on simple criteria. Submission is handled by creating an signed JSON file, using "shared secret" 
    to ensure that the TOO is from the registered party, and uploading via a HTTP POST to the Swift website. 
    Verification of the success or failure of submission is reported into the Swift_TOO_Status class, which 
    is populated using parameters reported by the  Swift TOO website upon submission.'''
    def __init__(self):
        TOOAPI_Baseclass.__init__(self)
        # Name the class
        self.api_name = "Swift_TOO_Request"
        # User chooseable values
        self.username = None # Swift TOO username (string)
        self.shared_secret = None # Swift TOO shared secret. Log in to Swift TOO page to find out / change your shared secret

        # These next two are assigned by the server, so don't set them
        self.too_id = None
        self.timestamp = None
        # Source name, type, location, position_error
        self.source_name = None # Name of the object we're requesting a TOO for (string)
        self.source_type = None # Type of object (e.g. "Supernova", "LMXB", "BL Lac")  (string)
        self.ra = None  # RA(J2000) Degrees decimal (float)
        self.dec = None # declination (J2000) Degrees decimal (float)
        self._skycoord = None # In case the user wants to use a Astropy SkyCoord to give us the coordinates (SkyCoord)
        self.poserr = 0.0    # Position error in arc-minutes (float)
                
        # Request details
        self.instrument = "XRT" # Choices "XRT","UVOT","BAT" (string)
        self.urgency = 3 # 1 = Within 4 hours, 2 = within 24 hours, 3 = Days to a week, 4 = week - month. (int)
        
        # Observation Type - primary goal of observation
        self.obs_types = ["Spectroscopy","Light Curve","Position","Timing"]
        self.obs_type = None # Select from self.obs_types one of four options, e.g. self.obs_types[1] == 'Light Curve'
        
        # Description of the source brightness for various instruments
        self.opt_mag = None  # UVOT optical magnitude (float)
        self.opt_filt = None # What filter was this measured in (can be non-UVOT filters) (string)

        self.xrt_countrate = None      # XRT estimated counts/s (float)
        self.bat_countrate = None # BAT estimated counts/s (float)
        self.other_brightness = None     # Any other brightness info (float)
        
        # GRB stuff
        self.grb_detector= None # Should be "Mission/Detection" (e.g "Swift/BAT, Fermi/LAT") (string)
        self.grb_triggertime = None # GRB trigger date/time (datetime)

        # Science Justification        
        self.immediate_objective = None # One sentence explaination of TOO (string)
        self.science_just = None # Note this is the Science Justification (string) 
        
        # Exposure requested time (total)
        self.exposure = None # Note this is the user requested exposure 
        
        # Monitoring request
        self.exp_time_just = None      # Justification of monitoring exposure (string)
        self.exp_time_per_visit = None # Exposure per visit (integer seconds)
        self.num_of_visits = 1         # Number of visits (integer)
        self.monitoring_freq = None # Formatted text to describe monitoring cadence. E.g. "2 days", "3 orbits", "1 week". See self.monitoring_units for valid units (string)
        # GI stuff
        self.proposal = None # Is this a GI proposal? True / False
        self.proposal_id = None # What is the GI proposal ID (string or integer)
        self.proposal_trigger_just = None # Note this is the GI Program Trigger Criteria Justification (string)
        self.proposal_pi = None # Proposal PI name (string)

        # Instrument mode
        self._xrt_mode = 7 # 7 = Photon Counting, 6 = Windowed Timing, 0 = Auto (self select). PC is default
        self._uvot_mode = 0x9999 #  Hex mode for requested UVOT filter. Default FOTD. See Cheat Sheet or https://www.swift.psu.edu/operations/mode_lookup.php for codes.
        self.uvot_just = None # Text justification of UVOT filter
        self.slew_in_place = None # Perform a slew-in-place? Typically used for GRISM observation. Allows the source to be placed more accurately on the detector.

        # Tiling request
        self.tiling = None
        self.number_of_tiles = None # Set this if you want a fixed number of tiles. Traditional tiling patterns are 4,7,19,37 "circular" tilings. If you don't set this we'll calculate based on error radius.
        self.max_number_of_tiles = None # If covering a probability region, set a maximum number of tiles to observe # NEW
        self.tiling_instrument = "XRT" # NEW What is the primary instrument for tiling? ["XRT"|"UVOT"] As instrument FOVs are different, affects packing 
        self.tiling_packing = 0 # NEW Tile packing. 0 = completeness 1 = coverage. 0 will overlap fields to ensure no gaps, 1 will tile edge-to-edge with small gaps, but covering a larger sky area per tile.
        self.exposure_time_per_tile = None # Set this if you want to have a fixed tile exposure, otherwise it'll just be exposure / number_of_tiles
        self.tiling_justification = None # Text description of why tiling is justified

        # # New stuff - Parameters that we should have as part of a TOO request, but can't be handled by our current system
        # # Parameters about coordination
        # self.coordinated = None # Is this a coordinated observation
        # self.coordinated_with = "" # Observatory for which coordination is occuring
        # self.coordinated_strictness = 0 # How strictly coordinated should we be? 0 = not at all, 1 = within window, 2 = same day as window
        # self.coordinated_prioirty = 0 # How high priority is the coordination 0 = not at all (Fermi), 1 = Ground Based, 2 = HST
        # # Stuff about the source
        # self.transient_age = None # Estimated age of the transient, e.g. if a Supernova, how long since it exploded?
        # self.source_trigger = None # Name the trigger that is associated with this source. E.g. if this is a ZTF counterpart of a LVC trigger, give the LVC trigger name
        # Calendar
        self.calendar = None

        # Debug parameter - if this is set, sending a TOO won't actually submit it. Good for testing.
        self.debug = None

        # Paramaters that get submitted as part of the JSON
        self.rows = ['username', 'source_name', 'source_type', 'ra', 'dec', 'poserr', 'instrument', 'urgency', 'opt_mag', 'opt_filt', 'xrt_countrate', 'bat_countrate', 'other_brightness', 'grb_detector', 'immediate_objective', 'science_just', 'exposure', 'exp_time_just', 'exp_time_per_visit', 'num_of_visits', 'monitoring_freq', 'proposal', 'proposal_id', 'proposal_trigger_just', 'proposal_pi', 'xrt_mode', 'uvot_mode', 'uvot_just', 'slew_in_place', 'tiling', 'number_of_tiles', 'exposure_time_per_tile', 'tiling_justification', 'obs_n', 'obs_type', 'calendar','debug','validate_only','grb_triggertime']

        # Optional parameters that may get returned
        self.extrarows = ['too_id','timestamp']
        # Internal values to check
        # The three instruments on Swift
        self.instruments = ['XRT','BAT','UVOT']
        # Common missions that that trigger detections
        self.mission_names = ['Fermi/LAT','Swift/BAT','INTEGRAL','MAXI','IPN','Fermi/GBM','IceCube','LVC','ANTARES','ZTF','ASAS-SN']

        # Valid units for monitoring frequency. Can add a "s" to each one if you like, so "3 orbits" is good.
        self.monitoring_units = ['second','minute','hour','day','week','month','year','orbit']

        # Status of request
        self.status = Swift_TOO_Status()

        # Do a server side validation instead of submit?
        self.validate_only = False

        # Things that can be a subclass of this class
        self.subclasses = []
        self.ignorekeys = True

    @property
    def uvot_mode(self):
        '''Return UVOT as a hex string. Stored as a number internally'''
        if type(self._uvot_mode) == int:
            return f"0x{self._uvot_mode:04x}"
        else:
            return self._uvot_mode
    
    @uvot_mode.setter
    def uvot_mode(self,mode):
        self._uvot_mode = mode

    @property
    def xrt_mode(self):
        '''Return XRT mode as abbreviation string. Internally stored as a number.'''
        return xrtmodes[self._xrt_mode]

    @xrt_mode.setter
    def xrt_mode(self,mode):
        '''Allow XRT mode to be set either as a string (e.g. "WT") or as a number (0, 6 or 7).'''
        if type(mode) == str:
            if mode in modesxrt.keys():
                self._xrt_mode = modesxrt[mode]
            else:
                raise NameError("Unknown mode, should be PC, WT or Auto")
        else:
            if mode in xrtmodes.keys():
                self._xrt_mode = mode
            else:
                raise ValueError("Unknown mode, should be PC (7), WT (6) or Auto (0)")

    @property 
    def skycoord(self):
        '''Allow TOO requesters to give an astropy SkyCoord object instead of RA/Dec. Handy if you want to do things like submit 1950 coordinates or Galactic Coordinates.'''
        # Check if the RA/Dec match the SkyCoord, and if they don't modify the skycoord
        if type(self._skycoord).__module__ == 'astropy.coordinates.sky_coordinate':
            if self.ra != self._skycoord.fk5.ra.deg or self.dec != self._skycoord.fk5.dec.deg:
                self._skycoord = self._skycoord.__class__(self.ra,self.dec,unit="deg",frame="fk5")
        return self._skycoord

    @skycoord.setter
    def skycoord(self,sc):
        '''Convert the SkyCoord into RA/Dec (J2000) when set.'''
        if type(sc).__module__ == 'astropy.coordinates.sky_coordinate':
            self._skycoord = sc
            self.ra = sc.fk5.ra.deg
            self.dec = sc.fk5.dec.deg
        else:
            raise Exception("Needs to be assigned an Astropy SkyCoord")

    @property
    def obs_n(self):
        '''Is this a request for a single observation or multiple?'''
        if self.num_of_visits != "" and self.num_of_visits > 1:
            return "multiple"
        else:
            return "single"

    @obs_n.setter
    def obs_n(self,value):
        '''Just ignore attempts to set this property'''
        pass
    
    def validate(self):
        '''Check that the TOO fits the minimum requirements for submission'''
        requirements = ['ra','dec','num_of_visits','exp_time_just','source_type','source_name','science_just',
                       'username','obs_type']
            
        # Check that the minimum requirements are met 
        for req in requirements:
            if self.__getattribute__(req) == None:
                print(f"ERROR: Missing key: {req}")
                return False

        if self.obs_type not in self.obs_types:
            print(f"ERROR: Observation Type needs to be one of the following: {self.obs_types}")
            return False

        if self.instrument not in self.instruments:
            print(f"ERROR: Instrument name ({self.instrument}) not valid")
            return False
            
        # If this is monitoring, we need time between exposures
        if self.num_of_visits > 1:
            if self.monitoring_freq == None or self.monitoring_freq == "":
                print("ERROR: Need monitoring cadence.")
                return False
            
            if not self.exp_time_per_visit:
                self.exp_time_per_visit = int(self.exposure / self.num_of_visits)
            else:
                if self.exp_time_per_visit * self.num_of_visits != self.exposure:
                    print("INFO: Total exposure time does not match total of individuals. Correcting.")
                    self.exposure = self.exp_time_per_visit * self.num_of_visits
        else:
            if not self.exposure:
                self.exposure = self.exp_time_per_visit

        # Check monitoring frequency is correct
        if self.monitoring_freq:
            _,unit = self.monitoring_freq.strip().split()
            if unit[-1] == 's':
                unit = unit[0:-1]
            if unit not in self.monitoring_units:
                print(f"ERROR: Monitoring unit ({unit}) not valid")
                return False
        
                    
        # Check validity of GI requests
        gi_requirements = ['proposal_id','proposal_pi','proposal_trigger_just']
        if self.proposal:
            for req in gi_requirements:
                if getattr(self,req) == None:
                    print(f"ERROR: Missing key: {req}")
                    return False
                
        # Check trigger requirements
        grb_requirements = ['grb_triggertime','grb_detector']
        if self.source_type == "GRB":
            for req in grb_requirements:
                if getattr(self,req) == None:
                    print(f"ERROR: Missing key: {req}")
                    return False

        return True

    def server_validate(self):
        # Perform a local validation first
        self.validate()
        # Do a server side validation
        if len(self.status.errors) == 0:
            # Preserve existing warnings
            warnings = self.status.warnings
            self.validate_only = True
            self.submit()
            self.validate_only = False
            for error in self.status.errors:
                print(f"ERROR: {error}")
            for warning in self.status.warnings:
                print(f"Warning: {warning}")
            self.status.warnings += warnings
            if len(self.status.errors) == 0:
                return True
            else:
                return False
        else:
            return False
        
