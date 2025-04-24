from typing import Optional

from pydantic import model_validator

from .api_common import TOOAPIBaseclass
from .swift_schemas import BaseSchema, OptionalCoordinateSchema


class SwiftResolveGetSchema(BaseSchema):
    name: str


class SwiftResolveSchema(OptionalCoordinateSchema):
    name: Optional[str] = None
    resolver: Optional[str] = None


class SwiftResolve(TOOAPIBaseclass, SwiftResolveSchema):
    """
    SwiftResolve class

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
        """If you set a name, use `SwiftResolve` to retrieve it's `ra` and
        `dec`."""

        if hasattr(self, "source_name"):
            self.name = self.source_name

        if self.name is not None and isinstance(self.name, str):
            r = SwiftResolve(name=self.name)
            if r.status.status == "Accepted":
                self.ra = r.ra
                self.dec = r.dec
        return self


# Shorthand alias for class
Swift_Resolve = SwiftResolve
Resolve = SwiftResolve
