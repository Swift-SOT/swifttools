from typing import Optional

from pydantic import ConfigDict, computed_field, model_validator

from ..base.common import TOOAPIBaseclass
from ..base.schemas import BaseSchema, OptionalCoordinateSchema
from ..base.status import TOOStatus


class SwiftResolveGetSchema(BaseSchema):
    name: str
    model_config = ConfigDict(extra="ignore")


class SwiftResolveSchema(OptionalCoordinateSchema):
    name: Optional[str] = None
    resolver: Optional[str] = None
    status: TOOStatus = TOOStatus()


class SwiftResolve(TOOAPIBaseclass, SwiftResolveSchema):
    """
    SwiftResolve class.

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

    _endpoint: str = "/resolve"
    _schema = SwiftResolveSchema
    _get_schema = SwiftResolveGetSchema

    def validate(self):
        """
        Validate API submission before submit

        Returns
        -------
        bool
            Was validation successful?
        """
        return self.validate_get()

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
    """
    TOOAPIAutoResolve schema for automatic coordinate resolution based on
    source name. If a `name` (or `target_name`) is provided, attempts to
    resolve its right ascension (`ra`) and declination (`dec`) using the
    `SwiftResolve` service. If resolution is successful, the coordinates are
    set in the schema. If resolution fails, the status is set to "Rejected"
    with an appropriate error message.

    Attributes
    ----------
    name : Optional[str]
        The name of the astronomical source to resolve. If provided,
        coordinates will be automatically retrieved.

    Methods
    -------
    validate_name(values)
        Validates and resolves the source name to coordinates. If resolution
        fails, updates the status accordingly.
    """

    _name: Optional[str] = None
    resolve: Optional[SwiftResolve] = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def name(self) -> Optional[str]:
        """Name of the astronomical source to resolve."""
        return self._name

    @name.setter
    def name(self, value: Optional[str]):
        """Set the name of the astronomical source."""
        self._name = value
        self.resolve = SwiftResolve(name=value)
        if self.resolve.status.status == "Accepted":
            self.ra = self.resolve.ra
            self.dec = self.resolve.dec
            self.skycoord = self.resolve.skycoord
            # self.resolver = resolve.resolver
        # else:
        #     # If resolving fails, set status to rejected
        #     status = SwiftTOOStatus(status="Rejected", errors=[f"Unable to resolve {value}"]).model_dump()
        #     self.status = status

    # name: Optional[str] = None

    @model_validator(mode="before")
    def validate_name(cls, values):
        """If you set a name, use `SwiftResolve` to retrieve its `ra` and `dec`."""

        name = values.get("name")
        target_name = values.get("target_name")
        if target_name is not None:
            values["name"] = target_name
            name = target_name

        if name is not None and isinstance(name, str):
            r = SwiftResolve(name=name)
            if len(r.status.warnings) == 0 and len(r.status.errors) == 0:
                values["ra"] = float(r.ra)
                values["dec"] = float(r.dec)
        return values


# Shorthand alias for class
Swift_Resolve = SwiftResolve
Resolve = SwiftResolve
