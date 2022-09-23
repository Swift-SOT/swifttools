# Lookup table for XRT modes
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


class TOOAPI_Instruments:
    """Mixin for XRT / UVOT / BAT mode display and capture"""

    _uvot = None
    _xrt = None
    _bat = None  # For now, bat mode is just an integer

    def uvot_mode_setter(self, attr, mode):
        if type(mode) == str and "0x" in mode:
            """Convert hex string to int"""
            setattr(self, f"_{attr}", int(mode.split(":")[0], 16))
        elif type(mode) == str:
            """Convert decimal string to int"""
            try:
                setattr(self, f"_{attr}", int(mode))
            except (TypeError, ValueError):
                setattr(self, f"_{attr}", mode)
        else:
            """Pass through anything else"""
            setattr(self, f"_{attr}", mode)

    def xrt_mode_setter(self, attr, mode):
        if type(mode) == str:
            if mode in MODESXRT.keys():
                setattr(self, f"_{attr}", MODESXRT[mode])
            else:
                raise NameError(f"Unknown mode ({mode}), should be PC, WT or Auto")
        elif mode is None:
            setattr(self, f"_{attr}", mode)
        else:
            if mode in XRTMODES.keys():
                setattr(self, f"_{attr}", mode)
            else:
                raise ValueError(
                    f"Unknown mode ({mode}), should be PC (7), WT (6) or Auto (0)"
                )

    @property
    def xrt(self):
        """Given a XRT mode number returns a string containing the name of the
        mode"""
        return XRTMODES[self._xrt]

    @xrt.setter
    def xrt(self, mode):
        self.xrt_mode_setter("xrt", mode)

    @property
    def uvot(self):
        """Given a UVOT mode number returns a string containing the name of the
        mode"""
        if type(self._uvot) == int:
            return f"0x{self._uvot:04x}"
        else:
            return self._uvot

    @uvot.setter
    def uvot(self, mode):
        self.uvot_mode_setter("uvot", mode)

    @property
    def bat(self):
        """Given a BAT mode number returns a string containing the name of the
        mode"""
        if type(self._bat) == int:
            return f"0x{self._bat:04x}"
        else:
            return self._bat

    @bat.setter
    def bat(self, mode):
        self.uvot_mode_setter("bat", mode)

    @property
    def uvot_mode_approved(self):
        """Return UVOT as a hex string. Stored as a number internally"""
        if type(self._uvot_mode_approved) == int:
            return f"0x{self._uvot_mode_approved:04x}"
        else:
            return self._uvot_mode_approved

    @uvot_mode_approved.setter
    def uvot_mode_approved(self, mode):
        self.uvot_mode_setter("uvot_mode_approved", mode)

    # Next for approved XRT / UVOT modes from TOORequests
    @property
    def xrt_mode_approved(self):
        """Return XRT mode as abbreviation string. Internally stored as a number."""
        if self._xrt_mode_approved is None:
            return "Unset"
        else:
            return XRTMODES[self._xrt_mode_approved]

    @xrt_mode_approved.setter
    def xrt_mode_approved(self, mode):
        """Allow XRT mode to be set either as a string (e.g. "WT") or as a number (0, 6 or 7)."""
        self.xrt_mode_setter("xrt_mode_approved", mode)

    # Aliases
    xrt_mode = xrt
    uvot_mode = uvot
    bat_mode = bat
