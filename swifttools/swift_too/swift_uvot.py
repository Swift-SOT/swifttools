from tabulate import tabulate

from .api_common import TOOAPI_Baseclass
from .api_resolve import TOOAPIAutoResolve
from .swift_instruments import TOOAPI_Instruments
from .swift_schemas import SwiftUVOTModeSchema


class SwiftUVOTModeEntry(TOOAPI_Baseclass):
    """Class describing a single entry in the UVOT Mode table

    Attributes
    ----------
    uvotmode : int
        UVOT mode
    filter_num : int
        filter number
    min_exposure : int
        minumum exposure for entry
    filter_name : str
        filter name
    filter_pos : int
        position of filter in filter wheel
    filter_seqid : int
        Sequence ID of filter
    eventmode : boolean
        Is filter entry taken in event mode
    field_of_view : int
        Filter of view in arcminutes
    binning : int
        Binning of entry
    max_exposure : int
        maximum exposure time for filter
    weight: boolean
        Is observation for this filter weighted for the total exposure time
    special: str
        comment on special modes
    """

    api_name: str = "UVOT_mode_entry"

    def __init__(self):
        # Lazy variable init
        for row in self._parameters:
            setattr(self, row, None)

    def __str__(self):
        return self.filter_name


class SwiftUVOTMode(TOOAPI_Baseclass, TOOAPI_Instruments, SwiftUVOTModeSchema, TOOAPIAutoResolve):
    """Class to fetch information about a given UVOT mode. Specifically this is
    useful for understanding for a given UVOT hex mode (e.g. 0x30ed), which
    filters and configuration are used by UVOT.

    Attributes
    ----------
    uvotmode : int / str
        UVOT mode to fetch information about (can be hex string or integer)
    username : str
        username for TOO API (default 'anonymous')
    shared_secret : str
        shared secret for TOO API (default 'anonymous')
    status : TOOStatus
        TOO API submission status
    entries : list
        entries (`UVOT_mode_entry`) in UVOT mode table
    """

    # Core API definitions
    api_name: str = "UVOT_mode"
    _schema = SwiftUVOTModeSchema
    _get_schema = SwiftUVOTModeSchema
    _endpoint = "/swift/uvotmode"

    def __getitem__(self, index):
        return self.entries[index]

    def __len__(self):
        return len(self.entries)

    def __str__(self):
        """Display UVOT mode table"""
        if hasattr(self, "status") and self.status == "Rejected" and self.status.__class__.__name__ == "TOOStatus":
            return "Rejected with the following error(s): " + " ".join(self.status.errors)
        elif self.entries is not None:
            table_cols = [
                "filter_name",
                "eventmode",
                "field_of_view",
                "binning",
                "max_exposure",
                "weight",
                "comment",
            ]
            table_columns = list()
            table_columns.append(
                [
                    "Filter",
                    "Event FOV",
                    "Image FOV",
                    "Bin Size",
                    "Max. Exp. Time",
                    "Weighting",
                    "Comments",
                ]
            )
            for entry in self.entries:
                table_columns.append([getattr(entry, col) for col in table_cols])

            table = f"UVOT Mode: {self.uvotmode}\n"
            table += "The following table summarizes this mode, ordered by the filter sequence:\n"
            table += tabulate(table_columns, tablefmt="pretty")
            table += "\nFilter: The particular filter in the sequence.\n"
            table += "Event FOV: The size of the FOV (in arc-minutes) for UVOT event data.\n"
            table += "Image FOV: The size of the FOV (in arc-minutes) for UVOT image data.\n"
            table += "Max. Exp. Time: The maximum amount of time the snapshot will spend on the particular filter in the sequence.\n"
            table += "Weighting: Ratio of time spent on the particular filter in the sequence.\n"
            table += "Comments: Additional notes that may be useful to know.\n"
            return table
        else:
            return "No data"

    def _repr_html_(self):
        """Jupyter Notebook friendly display of UVOT mode table"""
        if hasattr(self, "status") and self.status == "Rejected" and self.status.__class__.__name__ == "TOOStatus":
            return "<b>Rejected with the following error(s): </b>" + " ".join(self.status.errors)
        elif self.entries is not None:
            html = f"<h2>UVOT Mode: {self.uvotmode}</h2>"
            html += "<p>The following table summarizes this mode, ordered by the filter sequence:</p>"

            html += '<table id="modelist" cellpadding=4 cellspacing=0>'
            html += "<tr>"  # style="background-color:#08f; color:#fff;">'
            html += "<th>Filter</th>"
            html += "<th>Event FOV</th>"
            html += "<th>Image FOV</th>"
            html += "<th>Bin Size</th>"
            html += "<th>Max. Exp. Time</th>"
            html += "<th>Weighting</th>"
            html += "<th>Comments</th>"
            html += "</tr>"

            table_cols = [
                "filter_name",
                "eventmode",
                "field_of_view",
                "binning",
                "max_exposure",
                "weight",
                "comment",
            ]
            i = 0
            for entry in self.entries:
                if i % 2:
                    html += '<tr style="background-color:#eee;">'
                else:
                    html += '<tr">'
                for col in table_cols:
                    html += "<td>"
                    html += f"{getattr(entry, col)}"
                    html += "</td>"

                html += "</tr>"
            html += "</table>"
            html += '<p id="terms">'
            html += "<small><b>Filter: </b>The particular filter in the sequence.<br>"
            html += "<b>Event FOV: </b>The size of the FOV (in arc-minutes) for UVOT event data.<br>"
            html += "<b>Image FOV: </b>The size of the FOV (in arc-minutes) for UVOT image data.<br>"
            html += "<b>Max. Exp. Time: </b>The maximum amount of time the snapshot will spend on the particular filter in the sequence.<br>"
            html += "<b>Weighting: </b>Ratio of time spent on the particular filter in the sequence.<br>"
            html += "<b>Comments: </b>Additional notes that may be useful to know.<br></small>"
            html += "</p>"
            return html
        else:
            return "No data"


# Aliases that are more PEP8 compliant
UVOTMode = SwiftUVOTMode
UVOTModeEntry = SwiftUVOTModeEntry
# Backwards compatibility names
UVOT_mode_entry = SwiftUVOTModeEntry
UVOT_mode = SwiftUVOTMode
Swift_UVOTMode = SwiftUVOTMode
Swift_UVOTModeEntry = SwiftUVOTModeEntry
