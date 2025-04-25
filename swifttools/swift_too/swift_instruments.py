# Lookup table for XRT modes
import re
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator

XRTMODES = {
    0: "Auto",
    1: "Null",
    2: "ShortIM",
    3: "LongIM",
    4: "PUPD",
    5: "LRPD",
    6: "WT",
    7: "PC",
    8: "Raw",
    9: "Bias",
    150: "PC_150",
    200: "PC_200",
    255: "Manual",
    None: "Unset",
}
MODESXRT = {
    "Auto": 0,
    "Null": 1,
    "ShortIM": 2,
    "LongIM": 3,
    "PUPD": 4,
    "LRPD": 5,
    "WT": 6,
    "PC": 7,
    "Raw": 8,
    "Bias": 9,
    "PC_150": 150,
    "PC_200": 200,
    "Manual": 255,
}


class TOOAPIInstruments(BaseModel):
    """Pydantic schema for XRT / UVOT / BAT mode display and capture"""

    uvot_mode: Optional[Any] = Field(default=None, description="UVOT mode, stored as int or str")
    xrt_mode: Optional[Any] = Field(default=None, description="XRT mode, stored as int or str")
    bat_mode: Optional[Any] = Field(default=None, description="BAT mode, stored as int or str")
    uvot_mode_approved: Optional[Any] = Field(default=None, description="Approved UVOT mode")
    xrt_mode_approved: Optional[Any] = Field(default=None, description="Approved XRT mode")

    @model_validator(mode="before")
    def convert_modes(cls, values):
        def uvot_mode_convert(mode):
            if isinstance(mode, str) and "0x" in mode:
                uvot_mode = re.match(r"0x([0-9a-fA-F]+)", mode)
                if uvot_mode is not None:
                    return int(uvot_mode.group(0), 16)
                try:
                    return int(mode.split(":")[0], 16)
                except Exception:
                    return mode
            elif isinstance(mode, str):
                try:
                    return int(mode)
                except (TypeError, ValueError):
                    return mode
            else:
                return mode

        def xrt_mode_convert(mode):
            if isinstance(mode, str):
                if mode in MODESXRT:
                    return MODESXRT[mode]
                else:
                    raise ValueError(f"Unknown mode ({mode}), should be PC, WT or Auto")
            elif mode is None:
                return mode
            else:
                if mode in XRTMODES:
                    return mode
                else:
                    raise ValueError(f"Unknown mode ({mode}), should be PC (7), WT (6) or Auto (0)")

        # Convert input values for each field
        if "uvot_mode" in values:
            values["uvot"] = uvot_mode_convert(values["uvot_mode"])
        if "bat_mode" in values:
            values["bat"] = uvot_mode_convert(values["bat"])
        if "uvot_mode_approved" in values:
            values["uvot_mode_approved"] = uvot_mode_convert(values["uvot_mode_approved"])
        if "xrt_mode" in values:
            values["xrt"] = xrt_mode_convert(values["xrt"])
        if "xrt_mode_approved" in values:
            values["xrt_mode_approved"] = xrt_mode_convert(values["xrt_mode_approved"])
        return values

    @property
    def xrt(self):
        """Return XRT mode as abbreviation string."""
        if self.xrt_mode is None:
            return "Unset"
        return XRTMODES[self.xrt_mode]

    @property
    def uvot(self):
        """Return UVOT mode as hex string if int, else as is."""
        if isinstance(self.uvot_mode, int):
            return f"0x{self.uvot_mode:04x}"
        return self.uvot_mode

    @property
    def bat(self):
        """Return BAT mode as hex string if int, else as is."""
        if isinstance(self.bat_mode, int):
            return f"0x{self.bat_mode:04x}"
        return self.bat_mode

    @property
    def uvot_mode_approved_str(self):
        """Return approved UVOT mode as hex string if int, else as is."""
        if isinstance(self.uvot_mode_approved, int):
            return f"0x{self.uvot_mode_approved:04x}"
        return self.uvot_mode_approved

    @property
    def xrt_mode_approved_str(self):
        """Return approved XRT mode as abbreviation string."""
        if self.xrt_mode_approved is None:
            return "Unset"
        return XRTMODES[self.xrt_mode_approved]
