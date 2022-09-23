import re


class TOOAPI_ObsID:
    """Mixin for handling target ID / Observation ID with various aliases"""

    _target_id = None
    _seg = None

    def convert_obsnum(self, obsnum):
        """Convert various formats for obsnum (SDC and Spacecraft) into one format (Spacecraft)"""
        if type(obsnum) == str:
            if re.match("^[0-9]{11}?$", obsnum) is None:
                raise ValueError("obsnum string format incorrect")
            else:
                targetid = int(obsnum[0:8])
                segment = int(obsnum[8:12])
                return targetid + (segment << 24)
        elif type(obsnum) == int:
            return obsnum
        elif obsnum is None:
            return None
        else:
            raise ValueError("obsnum in wrong format.")

    @property
    def target_id(self):
        return self._target_id

    @target_id.setter
    def target_id(self, tid):
        if type(tid) == str:
            self._target_id = int(tid)
        else:
            self._target_id = tid

    @property
    def seg(self):
        return self._seg

    @seg.setter
    def seg(self, segment):
        self._seg = segment

    @property
    def obsnum(self):
        """Return the obsnum in SDC format"""
        if self._target_id is None or self._seg is None:
            return None
        elif type(self._target_id) == list:
            return [
                f"{self.target_id[i]:08d}{self.seg[i]:03d}"
                for i in range(len(self._target_id))
            ]
        else:
            return f"{self.target_id:08d}{self.seg:03d}"

    @obsnum.setter
    def obsnum(self, obsnum):
        """Set the obsnum value, by figuring out what the two formats are."""
        # Deal with lists of obsnumbers
        if type(obsnum) == list and len(obsnum) > 0:
            self._target_id = list()
            self._seg = list()
            for on in obsnum:
                onsc = self.convert_obsnum(on)
                self._target_id.append(onsc & 0xFFFFFF)
                self._seg.append(onsc >> 24)

        elif obsnum is not None and obsnum != []:
            obsnum = self.convert_obsnum(obsnum)
            self._target_id = obsnum & 0xFFFFFF
            self._seg = obsnum >> 24

    @property
    def obsnumsc(self):
        """Return the obsnum in spacecraft format"""
        if type(self._target_id) == list:
            return [
                self._target_id[i] + (self._seg[i] << 24)
                for i in range(len(self._target_id))
            ]
        return self._target_id + (self._seg << 24)

    # Aliases
    targetid = target_id
    targid = target_id
    segment = seg
    obsid = obsnum
    obsidsc = obsnumsc
