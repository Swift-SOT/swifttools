"""xrt_prods module, providing an API to create Swift-XRT products.

This module provices an interface to request XRT products be
constructed on the UKSSDC servers, via the interface at
https://www.swift.ac.uk/user_objects. This module provides an
easy-to-use front-end to the API. For full details of the underlying API
access to the XRT Products tool, see the APIDocs/README.md file in this
project, or https://www.swift.ac.uk/user_objects/API

To use this API you must register for the service, at:
https://www.swift.ac.uk/user_objects/register.php


This module exports a single class: XRTProductRequest. 

There is a second class within the module - the ProductRequest, 
which contains individual products (LightCurve, Spectrum) etc. 
This is not intended exported, as it is not intended for public
use, however if you retrieve a specific product for passing between
requests then it will be an instance of this class.

A very brief example follows, for more details see pyDocs/API.md in
this project, or https://www.swift.ac.uk/user_objects/API/docs/Python.md
The project has complete docstrings as well, so the python `help` command
should give useful information.

Brief example
-------------

::

    # The email address supplied must be registered for API usage
    myRequest = XRTProductRequest('your_email_address') 
    myRequest.addLightCurve( .. some arguments ..)
    myRequest.addStandardPosition( .. some arguments ..)
    if myRequest.submit():
       done=myRequest.complete
       while !done:
           time.sleep(60)
           done=myRequest.complete
       myRequest.downloadProducts('/path/to/somewhere', what='all)
    else:
        print ("The request was not submitted/processed succesfully: "
                +myRequest.submitError)


"""

from .prod_request import XRTProductRequest
from .prod_request import listOldJobs,countActiveJobs
from .version import __version__, _apiVersion
