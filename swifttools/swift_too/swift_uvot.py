from .common import TOOAPI_Baseclass, TOOAPI_Instruments
from .too_status import Swift_TOO_Status
from tabulate import tabulate


class UVOT_mode_entry(TOOAPI_Baseclass):
    '''Class describing a single entry in the UVOT Mode table

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
    '''
    # Core API definitions
    _parameters = ['uvotmode', 'filter_num', 'min_exposure', 'filter_name', 'filter_pos', 'filter_seqid',
                   'eventmode', 'field_of_view', 'binning', 'max_exposure', 'weight', 'special', 'comment']
    _attributes = []
    api_name = 'UVOT_mode_entry'

    def __init__(self):
        # Lazy variable init
        for row in self._parameters:
            setattr(self, row, None)

    def __str__(self):
        return self.filter_name


class UVOT_mode(TOOAPI_Baseclass, TOOAPI_Instruments):
    '''Class to fetch information about a given UVOT mode. Specifically this is
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
    status : Swift_TOO_Status
        TOO API submission status
    entries : list
        entries (`UVOT_mode_entry`) in UVOT mode table
    '''

    # Core API definitions
    _parameters = ['username', 'uvotmode']
    _attributes = ['status', 'entries']
    _subclasses = [UVOT_mode_entry, Swift_TOO_Status]
    api_name = 'UVOT_mode'
    # Alias for uvotmode
    uvotmode = TOOAPI_Instruments.uvot

    def __init__(self, *args, **kwargs):
        '''
        Parameters
        ----------
        uvotmode : int / str
            UVOT mode to fetch information about (can be hex string or integer)
        username : str
            username for TOO API (default 'anonymous')
        shared_secret : str
            shared secret for TOO API (default 'anonymous')
        '''
        # Set up username
        self.username = 'anonymous'
        # Set up uvotmode
        self.uvotmode = None
        # Here is where the data go
        self.entries = None
        # TOO API status
        self.status = Swift_TOO_Status()
        # Parse argument keywords
        self._parseargs(*args, **kwargs)

        # See if we pass validation from the constructor, but don't record
        # errors if we don't
        if self.validate():
            self.submit()
        else:
            self.status.clear()

    def __getitem__(self, index):
        return self.entries[index]

    def __len__(self):
        return len(self.entries)

    def __str__(self):
        '''Display UVOT mode table'''
        if self.entries is not None:
            table_cols = ['filter_name', 'eventmode', 'field_of_view',
                          'binning', 'max_exposure', 'weight', 'comment']
            table_columns = list()
            table_columns.append(['Filter', 'Event FOV', 'Image FOV',
                                  'Bin Size', 'Max. Exp. Time', 'Weighting', 'Comments'])
            for entry in self.entries:
                table_columns.append([getattr(entry, col) for col in table_cols])

            table = f"UVOT Mode: {self.uvotmode}\n"
            table += "The following table summarizes this mode, ordered by the filter sequence:\n"
            table += tabulate(table_columns, tablefmt='pretty')
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
        '''Jupyter Notebook friendly display of UVOT mode table'''
        if self.entries is not None:
            html = f"<h2>UVOT Mode: {self.uvotmode}</h2>"
            html += "<p>The following table summarizes this mode, ordered by the filter sequence:</p>"

            html += '<table id="modelist" cellpadding=4 cellspacing=0>'
            html += '<tr>'  # style="background-color:#08f; color:#fff;">'
            html += '<th>Filter</th>'
            html += '<th>Event FOV</th>'
            html += '<th>Image FOV</th>'
            html += '<th>Bin Size</th>'
            html += '<th>Max. Exp. Time</th>'
            html += '<th>Weighting</th>'
            html += '<th>Comments</th>'
            html += '</tr>'

            table_cols = ['filter_name', 'eventmode', 'field_of_view',
                          'binning', 'max_exposure', 'weight', 'comment']
            i = 0
            for entry in self.entries:
                if i % 2:
                    html += '<tr style="background-color:#eee;">'
                else:
                    html += '<tr">'
                for col in table_cols:
                    html += "<td>"
                    html += f"{getattr(entry,col)}"
                    html += "</td>"

                html += '</tr>'
            html += '</table>'
            html += '<p id="terms">'
            html += '<small><b>Filter: </b>The particular filter in the sequence.<br>'
            html += '<b>Event FOV: </b>The size of the FOV (in arc-minutes) for UVOT event data.<br>'
            html += '<b>Image FOV: </b>The size of the FOV (in arc-minutes) for UVOT image data.<br>'
            html += '<b>Max. Exp. Time: </b>The maximum amount of time the snapshot will spend on the particular filter in the sequence.<br>'
            html += '<b>Weighting: </b>Ratio of time spent on the particular filter in the sequence.<br>'
            html += '<b>Comments: </b>Additional notes that may be useful to know.<br></small>'
            html += '</p>'
            return html
        else:
            return "No data"

    def validate(self):
        # Check username and shared_secret are set
        if self.uvotmode is None:
            return False
        if not self.username or not self.shared_secret:
            print(
                f"{self.__class__.__name__} ERROR: username and shared_secret parameters need to be supplied.")
            self.status.error(
                'username and shared_secret parameters need to be supplied.')
            return None
        if type(self._uvot) != int:
            try:
                # See if it's a hex string
                self.uvotmode = int(self.uvotmode, 16)
            except ValueError:
                print(
                    f"{self.__class__.__name__} ERROR: Invalid UVOT mode: {self.uvotmode}.")
                self.status.error(f'Invalid UVOT mode: {self.uvotmode}.')
                return None
        return True
