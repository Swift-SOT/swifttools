from enum import Enum


class XRTModeEnum(int, Enum):
    """Enum for the XRT mode of a TOO request"""

    AUTO = 0
    PHOTON_COUNTING = 7
    WINDOWED_TIMING = 6


class UrgencyEnum(int, Enum):
    """Enum for the urgency of a TOO request"""

    URGENT = 0
    HIGHEST = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class ObsType(str, Enum):
    """Enum for the observation type of a TOO request"""

    SPECTROSCOPY = "Spectroscopy"
    LIGHT_CURVE = "Light Curve"
    POSITION = "Position"
    TIMING = "Timing"
