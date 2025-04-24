from typing import Optional

from .swift_schemas import BaseSchema


class SwiftTOOStatusSchema(BaseSchema):
    """Simple class to describe the status of a submitted TOO API request

    Attributes
    ----------
    jobnumber : int
        TOO API job number
    status : str
        status of API request
    errors : list
        list of error strings associated with the request
    warnings : list
        list of warning strings associated with the request
    too_id : list
        For a TOO request, the TOO ID assigned to a new request
    """

    status: str = "Pending"
    too_id: Optional[int] = None
    jobnumber: Optional[int] = None
    errors: list = []
    warnings: list = []

    def __eq__(self, value):
        return value == self.status

    def __bool__(self):
        if self.status == "Accepted":
            return True
        else:
            return False

    def error(self, error):
        """Add an error to the list of errors"""
        if error not in self.errors:
            self.errors.append(error)

    def warning(self, warning):
        """Add a warning to the list of warnings"""
        if warning not in self.warnings:
            self.warnings.append(warning)

    def clear(self):
        """Reset status"""
        self.__init__()
