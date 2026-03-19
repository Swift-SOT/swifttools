import warnings
from typing import Any


class TOOAPIBackCompat:
    """Mixin to provide backward compatibility for some property names."""

    @property
    def targname(self) -> Any:
        if hasattr(self, "target_name"):
            return self.target_name
        return None

    @property
    def source_name(self) -> Any:
        if hasattr(self, "target_name"):
            warnings.warn(
                "source_name is deprecated, please use target_name instead.", DeprecationWarning, stacklevel=2
            )
            return self.target_name

        return None

    @source_name.setter
    def source_name(self, value: Any) -> None:
        if hasattr(self, "target_name"):
            warnings.warn(
                "source_name is deprecated, please use target_name instead.", DeprecationWarning, stacklevel=2
            )
            self.target_name = value

    @property
    def source_type(self) -> Any:
        if hasattr(self, "target_type"):
            return self.target_type
        return None

    @source_type.setter
    def source_type(self, value: Any) -> None:
        if hasattr(self, "target_type"):
            warnings.warn(
                "source_type is deprecated, please use target_type instead.", DeprecationWarning, stacklevel=2
            )
            self.target_type = value

    @property
    def obsid(self) -> Any:
        if hasattr(self, "obs_id"):
            return self.obs_id
        return None

    @property
    def obsnum(self) -> Any:
        if hasattr(self, "obs_id"):
            return self.obs_id
        return None

    @property
    def uvotmode(self) -> Any:
        if hasattr(self, "uvot_mode"):
            return self.uvot_mode
        return None

    @property
    def xrtmode(self) -> Any:
        if hasattr(self, "xrt_mode"):
            return self.xrt_mode
        return None

    @property
    def batmode(self) -> Any:
        if hasattr(self, "bat_mode"):
            return self.bat_mode
        return None

    @property
    def xrt(self) -> Any:
        if hasattr(self, "xrt_mode"):
            return self.xrt_mode
        return None

    @property
    def uvot(self) -> Any:
        if hasattr(self, "uvot_mode"):
            return self.uvot_mode
        return None

    @property
    def bat(self) -> Any:
        if hasattr(self, "bat_mode"):
            return self.bat_mode
        return None

    @property
    def seg(self) -> Any:
        if hasattr(self, "segment"):
            return self.segment
        return None

    @property
    def ra_point(self) -> Any:
        if hasattr(self, "ra_object"):
            warnings.warn("ra_point is deprecated, please use ra_object instead.", DeprecationWarning, stacklevel=2)
            return self.ra_object
        return None

    @property
    def dec_point(self) -> Any:
        if hasattr(self, "dec_object"):
            warnings.warn("dec_point is deprecated, please use dec_object instead.", DeprecationWarning, stacklevel=2)
            return self.dec_object
        return None
