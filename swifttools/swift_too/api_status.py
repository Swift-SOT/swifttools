from .swift_schemas import SwiftTOOStatusSchema

# from swifttools.swift_too.api_resolve import SwiftTOOStatusSchema

# from .api_common import TOOAPI_Baseclass


# class SwiftTOOStatus(TOOAPI_Baseclass, SwiftTOOStatusSchema):
#     """Simple class to describe the status of a submitted TOO API request

#     Attributes
#     ----------
#     jobnumber : int
#         TOO API job number
#     username : str
#         username for TOO API (default 'anonymous')
#     shared_secret : str
#         shared secret for TOO API (default 'anonymous')
#     status : str
#         status of API request
#     timestamp : datetime
#         time request was submitted
#     began : datetime
#         time request began processing
#     completed : datetime
#         time request finished processing
#     errors : list
#         list of error strings assoicated with the request
#     warnings : list
#         list of warning strings associated with the request
#     too_id : list
#         For a TOO request, the TOO ID assigned to a new request
#     """

#     # Core API definitions
#     api_name: str = "Swift_TOO_Status"
#     _schema = SwiftTOOStatusSchema
#     _get_schema = SwiftTOOStatusSchema
#     _endpoint = "status"

#     def __eq__(self, value):
#         return value == self.status

#     def __bool__(self):
#         if self.status == "Accepted":
#             return True
#         else:
#             return False

#     def error(self, error):
#         """Add an error to the list of errors"""
#         if error not in self.errors:
#             self.errors.append(error)

#     def warning(self, warning):
#         """Add a warning to the list of warnings"""
#         if warning not in self.warnings:
#             self.warnings.append(warning)

#     def clear(self):
#         """Reset status"""
#         self.__init__()


# # Aliases for better PEP8 compliance, and future API updates
# Swift_TOOStatus = SwiftTOOStatus
# Swift_TOO_Status = SwiftTOOStatus
# TOOStatus = Swift_TOOStatus


Swift_TOO_Status = SwiftTOOStatusSchema
Swift_TOOStatus = SwiftTOOStatusSchema
SwiftTOOStatus = SwiftTOOStatusSchema
TOOStatus = SwiftTOOStatusSchema
