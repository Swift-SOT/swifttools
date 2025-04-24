from typing import Optional

from pydantic import model_validator

from .api_common import TOOAPI_Baseclass
from .swift_schemas import BaseSchema, OptionalCoordinateSchema, SwiftResolveGetSchema, SwiftResolveSchema


class SwiftTOOStatusSchema(BaseSchema):
    status: str = "Pending"
    too_id: Optional[int] = None
    jobnumber: Optional[int] = None
    errors: list = []
    warnings: list = []

    def error(self, error):
        """Add an error to the list of errors"""
        if error not in self.errors:
            self.errors.append(error)

    def warning(self, warning):
        """Add a warning to the list of warnings"""
        if warning not in self.warnings:
            self.warnings.append(warning)


class SwiftResolve(TOOAPI_Baseclass, SwiftResolveSchema):
    """Swift_Resolve class

    Performs name resolution using Simbad, TNS or MARS. Simply give the name of
    the source, and it will return `ra` and `dec` in decimal degrees, or a
    astropy SkyCoord (`skycoord`).

    Attributes
    ----------
    name : str
        name of the object to have coordinates resolved.
    username: str
        Swift TOO API username (default 'anonymous')
    shared_secret: str
        TOO API shared secret (default 'anonymous')
    ra : float
        Right Ascension of resolved target in J2000 (decimal degrees)
    dec : float
        Declination of resolved target in J2000 (decimal degrees)
    resolver : str
        Name of name resolving service used
    skycoord : SkyCoord
        SkyCoord version of RA/Dec if astropy is installed
    status : str
        status of API request
    """

    api_name: str = "Swift_Resolve"
    _endpoint: str = "/resolve"
    _schema = SwiftResolveSchema
    _get_schema = SwiftResolveGetSchema

    def validate(self):
        """Validate API submission before submit

        Returns
        -------
        bool
            Was validation successful?
        """
        if not self._get_schema.model_validate(self):
            self.status.error("Validation failed.")
            return False
        return True

    @property
    def _table(self):
        """Displays values in class as a table"""
        if self.ra is not None:
            header = ["Name", "RA (J2000)", "Dec (J2000)", "Resolver"]
            table = [[self.name, f"{self.ra:.5f}", f"{self.dec:.5f}", self.resolver]]
            return header, table
        else:
            return [], []


class TOOAPIAutoResolve(OptionalCoordinateSchema):
    name: Optional[str] = None

    @model_validator(mode="after")
    def validate_name(self) -> "TOOAPIAutoResolve":
        """If you set a name, use `SwiftResolve` to retrieve it's `ra` and `dec`."""
        if self.name is not None and isinstance(self.name, str):
            r = SwiftResolve(name=self.name)
            if r.status.status == "Accepted":
                self.ra = r.ra
                self.dec = r.dec
        return self


class TOOAPI_AutoResolve:
    """Mixin to automatically any given `name` into RA/Dec coordinates using
    `Swift_Resolve`"""

    _name = None
    _source_name = None
    resolve = None

    def __name_setter(self, sourcename):
        """If you set a name, use `Swift_Resolve` to retrieve it's `ra` and `dec`."""
        if self._name != sourcename:
            self._name = sourcename
            self._source_name = sourcename
            self.resolve = Swift_Resolve(name=sourcename)
            if self.resolve.ra is not None:
                self.ra = self.resolve.ra
                self.dec = self.resolve.dec
            else:
                self.status.error("Could not resolve name.")

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, sourcename):
        self.__name_setter(sourcename)

    @property
    def source_name(self):
        return self._source_name

    @source_name.setter
    def source_name(self, sourcename):
        self.__name_setter(sourcename)


# Shorthand alias for class
Swift_Resolve = SwiftResolve
Resolve = SwiftResolve
