from .common import TOOAPI_Baseclass
from .too_status import Swift_TOO_Status
from tabulate import tabulate

class UVOT_mode_entry(TOOAPI_Baseclass):
    def __init__(self):
        TOOAPI_Baseclass.__init__(self)
        self.filter_name = None
        self.rows = ['uvotmode','filter_num','min_exposure','filter_name','filter_pos','filter_seqid','eventmode','field_of_view','binning','max_exposure','weight','special','comment']
        # Lazy variable init
        for row in self.rows:
            setattr(self,row,None)

    def __str__(self):
        return self.filter_name
class UVOT_mode(TOOAPI_Baseclass):
    def __init__(self,username=None,shared_secret=None,uvotmode=None):
        TOOAPI_Baseclass.__init__(self)
        self.rows = ['username','uvotmode','entries']
        self.extrarows = ['status']
        self.username = username
        self.shared_secret = shared_secret
        self.uvotmode = uvotmode
        self.entries = None
        self.status = Swift_TOO_Status()
        self.subclasses = [UVOT_mode_entry,Swift_TOO_Status]
        if uvotmode and self.validate():
            self.submit()

    def __getitem__(self,index):
        return self.entries[index]
    
    def __len__(self):
        return len(self.entries)

    def __str__(self):
        '''Display UVOT mode table'''
        if self.entries != None:
            table_cols = ['filter_name','eventmode','field_of_view','binning','max_exposure','weight','comment']
            table_rows = list()
            table_rows.append(['Filter','Event FOV','Image FOV','Bin Size','Max. Exp. Time','Weighting','Comments'])
            for entry in self.entries:
                table_rows.append([getattr(entry,col) for col in table_cols])

            table = f"UVOT Mode: 0x{self.uvotmode:04x}\n"
            table += "The following table summarizes this mode, ordered by the filter sequence:\n"
            table += tabulate(table_rows,tablefmt='pretty')
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
        if self.entries != None:
            html = f"<h2>UVOT Mode: 0x{self.uvotmode:04x}</h2>"
            html += "<p>The following table summarizes this mode, ordered by the filter sequence:</p>"

            html += '<table id="modelist" cellpadding=4 cellspacing=0>'
            html += '<tr>'# style="background-color:#08f; color:#fff;">'
            html += '<th>Filter</th>'
            html += '<th>Event FOV</th>'
            html += '<th>Image FOV</th>'
            html += '<th>Bin Size</th>'
            html += '<th>Max. Exp. Time</th>'
            html += '<th>Weighting</th>'
            html += '<th>Comments</th>'
            html += '</tr>'

            table_cols = ['filter_name','eventmode','field_of_view','binning','max_exposure','weight','comment']
            i=0
            for entry in self.entries:
                if i%2: 
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
            return f"No data"

    def validate(self):
        # Check username and shared_secret are set
        if not self.username or not self.shared_secret:
            print(f"{self.__class__.__name__} ERROR: username and shared_secret parameters need to be supplied.")
            self.status.error('username and shared_secret parameters need to be supplied.')
            return None
        if type(self.uvotmode) != int:
            try:
                # See if it's a hex string
                self.uvotmode = int(self.uvotmode,16)
            except:
                print(f"{self.__class__.__name__} ERROR: Invalid UVOT mode: {self.uvotmode}.")
                self.status.error(f'Invalid UVOT mode: {self.uvotmode}.')
                return None
        return True