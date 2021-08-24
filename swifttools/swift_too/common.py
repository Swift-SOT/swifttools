import json
from datetime import datetime,timedelta,date
from os import isatty
import re
from jose import jwt
import requests
from time import sleep
from .version import api_version
from tabulate import tabulate
import textwrap

# Convert degrees to radians
dtor = 0.017453292519943295
# Lookup table for XRT modes
xrtmodes = {0: "Auto", 1: "Null", 2: "ShortIM", 3: "LongIM", 4: "PUPD", 5: "LRPD", 6: "WT", 7: "PC", 8: "Raw", 9: "Bias"}
modesxrt = {"Auto": 0, "Null": 1, "ShortIM": 2, "LongIM": 3, "PUPD":4, "LRPD": 5 , "WT": 6, "PC": 7, "Raw": 8, "Bias": 9}

# Submission URL
API_URL = "https://www.swift.psu.edu/toop/submit_json.php"

class TOOAPI_Baseclass:
    '''Mixin for TOO API Classes. Most of these are to do with reading and writing classes out as JSON/dicts.'''
    def __init__(self):
        self.api_name = self.__class__.__name__
        self.api_version = api_version
        self.rows = list()      # Key values in the class
        self.extrarows = list() # Additional values in the class
        self.entries = list() # If this is a container class
        # List of acceptable subclasses 
        self.subclasses = list()
        # Ignore any keys you don't understand
        self.ignorekeys = False


        # Regex for matching date, time and datetime strings
        self.date_regex = r"^[0-2]\d{3}-(0?[1-9]|1[012])-([0][1-9]|[1-2][0-9]|3[0-1])+(\.\d+)?$"
        self.time_regex = r"^([0-9]:|[0-1][0-9]:|2[0-3]:)[0-5][0-9]:[0-5][0-9]+(\.\d+)?$"
        self.datetime_regex = r"^[0-2]\d{3}-(0?[1-9]|1[012])-([0][1-9]|[1-2][0-9]|3[0-1]) ([0-9]:|[0-1][0-9]:|2[0-3]:)[0-5][0-9]:[0-5][0-9]+(\.\d+)?$"
        # Submission timeout
        self.timeout = 120 # 2 mins

    @property
    def table(self):
        '''Table of TOO details'''
        rows = self.extrarows + self.rows
        table = [[row,"\n".join(textwrap.wrap(f"{getattr(self,row)}"))] for row in rows if getattr(self,row) != None and getattr(self,row) != ""]
        return table

    def __str__(self):
        return tabulate(self.table,['Parameter','Value'],tablefmt='pretty',stralign='left')

    def _repr_html_(self):
        html = tabulate(self.table,['Parameter','Value'],tablefmt='html',stralign='right')
        # Workaround because `tabulate` assumes that left alignment is default but in Jupyter it is not
        html = html.replace('right','left') 
        return html

    @property
    def json_dict(self):
        '''Dictionary version of TOO API object'''
        json_dict = dict()
        json_dict["api_name"] = self.api_name
        json_dict["api_version"] = self.api_version
        json_dict['api_data'] = self.api_data
        return json_dict

    @property
    def api_data(self):
        '''Convert class parameters and data into a dictionary'''
        data = dict()
        for param in self.rows:
            value = getattr(self,param)
            if value != None:
                if 'api_data' in dir(value):
                    data[param] = value.json_dict
                elif type(value) == list:
                    conv = lambda x: x if type(x) == str else x.json_dict
                    data[param] = [conv(entry) for entry in value]   
                elif type(value) == datetime or type(value) == date or type(value) == timedelta:
                    data[param] = f"{value}"
                elif type(value).__module__ == 'astropy.time.core': # Detect and convert astropy Time
                    data[param] = f"{value.datetime}"
                else:
                    data[param] = value
        return data

    @property
    def json(self):
        '''JSON version of TOO API Object'''
        return json.dumps(self.json_dict)

    @property 
    def jwt(self):
        '''JWT version of TOO API Object'''
        return jwt.encode(self.json_dict, self.shared_secret, algorithm='HS256')
    
    def convert_dict_entry(self,entry):
        '''Parse data entry from a dictionary (usualy originating as a JSON) to convert into Python data types.
        Danger! Danger Will Robinson! Recursion! Recursion!'''
        # Parse a JSON entry
        if type(entry) == dict and 'api_name' in entry.keys():
            index = [s().api_name for s in self.subclasses].index(entry['api_name'])
            val = self.subclasses[index]()
            val.read_dict(entry['api_data'])
        # Parse a list of items
        elif type(entry) == list:
            # Parse a list of jsons
            val = list()
            for subvalue in entry:
                # Hey, we must have some handy function for parsing values, right?
                val.append(self.convert_dict_entry(subvalue))
        # Parse all other values
        else: 
            val = False
            if entry:
                # Check if these are dates, datetimes or times by regex matching
                match = re.match(self.time_regex,str(entry))
                if match != None:
                    hours,mins,secs = match[0].split(":")
                    hours = int(hours)
                    mins = int(mins)
                    secs = int(secs) 
                    millisecs = int(1000.0*secs%1)
                    val = timedelta(hours=hours,minutes=mins,seconds=secs,milliseconds=millisecs)

                # Parse dates into a datetime.date
                match = re.match(self.date_regex,str(entry))
                if match != None:
                    val = datetime.strptime(match[0], '%Y-%m-%d').date()

                # Parse a date/time into a datetime.datetime
                match = re.match(self.datetime_regex,str(entry))
                if match != None:
                    if "." in match[0]:
                        val = datetime.strptime(match[0], '%Y-%m-%d %H:%M:%S.%f')
                    else:
                        val = datetime.strptime(match[0], '%Y-%m-%d %H:%M:%S')

                # If it's a float, convert it
                try:
                    val = float(val)
                except:
                    pass

            # None of the above? It is what it is.
            if val == False:
                val = entry

        return val

    def set_status(self,newstatus):
        if type(self.status) == str:
            print(newstatus)
        else:
            self.set_status(newstatus)

    def set_error(self,newerror):
        if hasattr(self,'status'):
            if type(self.status) == str:
                self.error(newerror)
            else:
                self.status.error(newerror)
        else:
            print(f"ERROR: {newerror}")

    def set_warning(self,warning):
        if hasattr(self,'status'):
            if type(self.status) == str:
                self.warning(warning)
            else:
                self.status.warning(warning)
        else:
            print(f"Warning: {warning}")

    def read_dict(self,data_dict):
        '''Read from a dictionary values for the class'''
        for key in data_dict.keys():
            if key in self.rows or key in self.extrarows:
                val = self.convert_dict_entry(data_dict[key])
                if val != None: # If value is set to None, then don't change the value
                    setattr(self,key,val)
            else:
                if not self.ignorekeys: # If keys exist in JSON we don't understand, fail out
                    self.set_error(f"Unknown key in JSON file: {key}")
                    return False
        return True # No errors

    @property
    def submit_url(self):
        '''Generate a URL that submits the TOO API request'''
        url = f"{API_URL}?jwt={self.jwt}"
        return url

    def queue(self,post=True):
        '''Queue a job up, don't wait for it to be processed'''
        return self.submit(post=post,timeout=0)

    @property
    def complete(self,post=True):
        '''Check if a queued job is completed'''
        if self.submit_jwt(post=post):
            if self.status != "Queued" and self.status != "Processing":
                return True
        return False

    def submit_jwt(self,post=True):
        '''Submit JWT request to server. Note that submitting the request multiple times will return the status of the request.'''
        # Don't submit an accepted or rejected request more than once
        if self.status == "Accepted":
            return True
        elif self.status == "Rejected":
            return False

        # Which way will we fetch the data?
        if post:
            r = self.submit_post()
        else:
            r = self.submit_get()

        # See how sucessful we were
        if r.status_code == 200:
            # True to decode the returned JSON. Return an error if it doesn't work.
            try:
                json_dict = json.loads(r.text)
                self.jsd = json_dict
            except:
                self.set_error(f"Failed to decode JSON. Please check that your shared secret is correct.")
                return False

            # Determine that we are running the correct API version
            if json_dict['api_version'] != self.api_version:
                self.set_error(f"API version mismatch. Remote version {json_dict['api_version']} vs local version {self.api_version}. Ensure you're running the latest API code.")
                return False

            # Determine if the returned JSON is the full result or just a status message
            if json_dict['api_name'] == self.api_name:
                self.read_dict(json_dict['api_data'])
            elif json_dict['api_name'] == "Swift_TOO_Status":
                self.status.read_dict(json_dict['api_data'])
        else:
            self.set_error(f"HTTP Submit failed with error code {r.status_code}")
            self.set_status("Rejected")
            return False
        return True

    def submit(self,timeout=None,post=True):
        '''Submit request using URL encoded JWT data. First validates submission, and then checks if the the request 
        has already been processed. Note submission of new job and checking the status are essentially the same 
        process. Default behaviour is to keep checking if the submission has been processed by the TOO_API server 
        every 2 seconds until the timeout (default 120s) has been reached.'''
        # Update timeout value from default if passed
        if timeout != None:
            self.timeout = timeout

        # Make sure it passes validation checks
        if not self.validate():
            self.set_error(f"Swift TOO API submission did not pass internal validation checks.")
            return False
        
        utime = datetime.now().timestamp()

        # For Swift_ObsQuery If end is set as the future, just set it to now as this can cause confusion with caching.
        if self.api_name == 'Swift_AFST' and self.end != None and self.end > datetime.utcnow():
            self.end = datetime.utcnow()

        # Keep requesting the submission until it either responds that it's accepted or rejected, some error occurs, or the timeout time is reached.
        while(datetime.now().timestamp()-utime < self.timeout or self.timeout == 0):
            # Submit the request in JWT form to the server
            if not self.submit_jwt(post=post):
                return False

            # If the job is Accepted, exit and return True
            if self.status == "Accepted":
                return True
            # If the job is queued, sleep for 2 s if a self.timeout value > 0 is specified
            elif self.status == "Queued" or self.status == "Processing":
                if self.timeout > 0:
                    sleep(2)
                else:
                    return True
            # If the job isn't Accepted or Queued, it must be rejected
            else:
                return False

        # If we got here, then presumably the requested job is not yet processed
        self.set_error(f"Queued job timed out.")
        return False


    def submit_get(self):
        '''Submit the request through the web based API, as a JWT through GET (essentially a URL)'''
        return requests.get(self.submit_url)

    def submit_post(self):
        '''Submit the request through the web based API, as a JWT through POST'''
        return requests.post(url = API_URL, verify=True, data = {'jwt': self.jwt})
