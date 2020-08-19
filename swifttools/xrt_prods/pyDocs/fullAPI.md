# Full API description

Here we give the full description of the ``xrt_prods`` module, describing all public functions
and variables. Following Python convention, functions or variables intended only for internal
use within the class (i.e. those which we would declare as ``private`` in C++) have names which
begin with a single underscore character. These are not described below.

## Contents

* [Module-level functions](#module-level-functions)
  * [countActiveJobs()](#countactivejobs)
  * [listOldJobs()](#listoldjobs)
* [The XRTProductRequest class](#the-xrtproductrequest-class)
  * [Methods](#xrtproductrequest-methods)
  * [Variables](#xrtproductrequest-variables)

---

## Module level functions


### `countActiveJobs()`

**Definition:** `xrt_prods.countActiveJobs(userID)`

Count how many active jobs you have in the queue.

This asks the server how many jobs are currently in the queue -
either running or awaiting execution - with your username.


**Parameters**

**userID** (*str*)
: Your username.



**Returns**

: The number of jobs.



**Return type**

: int



**Raises**

**RuntimeError**
: If the server does not return the expected data.


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `listOldJobs()`

**Definition:** `xrt_prods.listOldJobs(userID)`

List all of the jobs you have submitted.

This asks the server to return a list of all of the jobs you have
ever submitted using your registered email address (userID).

It returns list of dictionaries, where each entry has the following
keys:


* JobID : int - the jobID
* Name : str - the name you gave to the object
* DateSubmitted : str - the date you submitted the job (UTC)
* LightCurve : bool - Whether you requested a light curve
* Spectrum : bool - Whether you requested a spectrum
* StandardPos : bool - Whether you requested a standard position
* EnhancedPos : bool - Whether you requested an enhanced position
* AstromPos : bool - Whether you requested an astrometric position
* Image : bool - Whether you requested an image
* hasProd : bool - Whether the products are still available on the server

**Parameters**

**userID** (*str*)
: Your username.



**Returns**

: The list of your previous jobs, described above, most recent
first.



**Return type**

: list



**Raises**

**RuntimeError**
: If the server does not return the expected data.



---

## The XRTProductRequest class

**Definition:** `xrt_prods.XRTProductRequest(user, JSONVals=None, fromServer=False, silent=True)`



---

### XRTProductRequest Methods


### `addAstromPos()`

**Definition:** `addAstromPos(clobber=False, **xastromArgs)`

Add an astrometric position to the current request.

A wrapper to addProduct(“xastrom”, clobber, \*\*xastromArgs).


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `addEnhancedPos()`

**Definition:** `addEnhancedPos(clobber=False, **enhArgs)`

Add a enhanced position to the current request.

A wrapper to addProduct(“enh”, clobber, \*\*enhArgs).


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `addImage()`

**Definition:** `addImage(clobber=False, **imageArgs)`

Add an image to the current request.

A wrapper to addProduct(“image”, clobber, \*\*imageArgs).


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `addLightCurve()`

**Definition:** `addLightCurve(clobber=False, **lcArgs)`

Add a light curve to the current request.

A wrapper to addProduct(“lc”, clobber, \*\*lcArgs).


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `addProduct()`

**Definition:** `addProduct(what, clobber=False, **prodArgs)`

Add a specific product to the request.

The product is defined by ‘what’. If such a product has already
been added, this will raise a RuntimeError, unless the ‘clobber’
argument is set to True, in which case the existing product will
be deleted and a new one added.

If the product type is not recognised a ValueError will be
raised.

Any other arguments will be passed to the product constructor.


**Parameters**


**what** (*string*)
: The product to add (lc, spec, psf etc)


**prodArgs** (*kwargs* (optional))
: Arguments to pass to the product constructor.



**Raises**

**RuntimeError**
: If the request has already been submitted, or if the product
being added already exists, and you have not specified
clobber=True.


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `addSpectrum()`

**Definition:** `addSpectrum(clobber=False, **specArgs)`

Add a spectrum to the current request.

A wrapper to addProduct(“spec”, clobber, \*\*specArgs).


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `addStandardPos()`

**Definition:** `addStandardPos(clobber=False, **psfArgs)`

Add a standard position to the current request.

A wrapper to addProduct(“psf”, clobber, \*\*psfArgs).


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `cancelProducts()`

**Definition:** `cancelProducts(what='all')`

Cancel some requested products.

This function can only be called one the request has been
submitted successfully. It asks the UKSSDC servers to cancel
one more more of the requested products.

The return value is a tuple of (status,cancelStatus), defined
thus:

status : int - a status code:
: -1 = HTTP/other error
:  0 = error in cancellation
:  1 = success
:  2 = partial success, not all jobs were cancelled.
cancelStatus: dict.

The nature of the cancelStatus dictionary depends on the success
status. If the job was unsuccessful (code &lt;=0) then this contains a
single entry: ERROR, describing the problem.

Otherwise, it contains an entry for each product you
requested to cancel, each of which is also a dictionary with
entries “code” and “text”. The latter describes the status
of the attempt to cancel the job, the former gives a numeric
code defined in the main API documentation.


**Parameters**

**what** (*string / list*)
: Either the string “all” (the default) or a list of products
to cancel (default: “all”).



**Returns**

: Defined above.



**Return type**

: tuple



**Raises**

**RuntimeError**
: If the request has not been submitted, or the job is no
longer running.


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `checkProductStatus()`

**Definition:** `checkProductStatus(what='all')`

Check the status of your submitted job.

This can only be called once your request has been successfully
submitted. It checks the status of the products specified in
what (default: ‘all’), and returns a dictionary with one entry
per product, giving the progress.

If called with ‘all’ then this will update the ‘complete’
variable.

The dictionary returned has the following entries:

statusCode
:A code indicating the status of the job - see the API
documentation for a description. A code of -10 indicates
that the status was not reported by the server.

statusText
:A textual description of the job status.

progress
:A dictionary describing the details of the progress -
see the API documentation for a description.

progressText
:A human-readable string describing the details of the
progress, formatted as a list, deduced from the ‘progress’
entry.


**Parameters**

**what** (*string / list*)
: Either the string “all” (the default) or a list of products
to check (default: all)



**Returns**

: Described above - or with the entry “ERROR” if an error
occurred.



**Return type**

: dict



**Raises**

**RuntimeError**
: If the request has not been submitted, or the job is no
longer running.


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `copyOldJob()`

**Definition:** `copyOldJob(oldJobID, becomeThis=False)`

Set your request to match an old job.

This will completely destroy your request, and replace it with
the a duplicate of the job matching the ID supplied - provided
you were the user requesting that job.


**Parameters**


**oldJob** (*int*)
: The ID of the job you want to duplocate.


**becomeThis** (*bool** (**optional**)*)
: Whether this XRTProductRequest should ‘become’ the old
request. This will mean that you cannot submit the job, but
you can retrieve the products (if available).



**Raises**

**RuntimeError**
: If the job cannot be copied.


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `copyProd()`

**Definition:** `copyProd(what, copyFrom)`

Copy a product from one request to another.


**Parameters**


**what** (*string*)
: The product type


**copyFrom**
: The product you wish to copy. Must be of the correct type.
i.e. if ‘what’ is ‘lc’ then ‘copyFrom’ must be a
light curve.



**Raises**

**ValueError**
: If the specified product doesn’t exist, or doesn’t match,
e.g. if you try to copy a spectrum to a light curve.


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `countActiveJobs()`

**Definition:** `countActiveJobs()`

Count how many jobs the user has actively in the queue.

This asks the server how many jobs are currently in the queue -
either running or awaiting execution - with your username.
Just a wrapper to call xrt_prods.countActiveJobs().


**Parameters**

No parameters



**Returns**

: The number of jobs.



**Return type**

: int


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `downloadProducts()`

**Definition:** `downloadProducts(dir, what='all', silent=True, format='tar.gz', stem=None, clobber=False)`

Retrieve completed products.

This downloads the data for completed products into the
specified directory.  If ‘what’ is ‘all’ it will only try to
download products which are complete.  If ‘what’ is a list of
specific products this will raise a ValueError if you request a
product which is not complete.


**Parameters**


**dir** (*str*)
: The  directory into which the products will be downloaded.


**what** (*string / list*)
: Either the string “all” (the default) or a list of products
to check (default: all).


**format** (*str*)
: The format to download the file in; see API documentation
for options (default: tar.gz).


**silent** (*bool*)
: Whether to suppress status output to STDOUT (default: False)


**clobber** (*bool*)
: Whether the downloaded files can overwrite existing ones
(default: False).


**stem** (*str*)
: An optional string to prepend to the downloaded filenames
(default: None)



**Returns**

: A dictionary with an entry for each requested product,
either set to None (if the product was incomplete), a string
giving the path to the downloaded file, or the string
“ERROR: $msg” where $msg is the reason that the product was
not downloaded.



**Return type**

: dict



**Raises**

**ValueError**
: If the product requested is not complete.


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `getAllPars()`

**Definition:** `getAllPars(showUnset=False)`

Return all parameters that have been set.

Return a dictionary of all parameters set so far. The dictionary
is nested: the top level contains the global parameters and
an entry for each product. The latter are themselves
dictionaries of the parameters for that product.


**Parameters**

**showUnset** (*bool*)
: Return all possible parameters, including those not yet set
(default: False).



**Returns**

: Dictionary of parameters



**Return type**

: dict


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `getAstromPosPars()`

**Definition:** `getAstromPosPars(parName='all', showUnset=False)`

Get an astrometric position parameter.

A wrapper to getProductPar(‘xastrom’, parName, showUnset).


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `getEnhancedPosPars()`

**Definition:** `getEnhancedPosPars(parName='all', showUnset=False)`

Get an enhanced position parameter.

A wWrapper to getProductPar(‘enh’, parName, showUnset).


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `getGlobalPars()`

**Definition:** `getGlobalPars(globPar='all', omitShared=True, showUnset=False)`

Return the current value of the requested global parameter.

Raises a ValueError if an invalid parameter is requested.


**Parameters**


**globPar** (*str*)
: The parameter to get (default ‘all’)


**omitShared** (*bool*)
: There are some ‘shared’ variables which are not really
‘global’, but are shared between products (this are
currently only those controlling which data are used to
generate positions). This parameter controls whether these
are shown in the returned list of globals. Only relevant if
globPar==’all’. Default: false


**showUnset** (*bool*)
: Only used if globPar is ‘all’, will include all of the
global parameters not yet set in the returned dict
(default: False).



**Returns**

: If a single parameter was specified returns the parameter
value (or None).
If all parameters were specified, returns a dict of all
parameters.



**Return type**

: Multiple



**Raises**

**ValueError**
: If globPar is not a valid global parameter.


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `getImagePars()`

**Definition:** `getImagePars(parName='all', showUnset=False)`

Get an image parameter.

A wrapper to getProductPar(‘image’, parName, showUnset).


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `getJSON()`

**Definition:** `getJSON()`

Get the JSON-formatted string to upload.

This calls getJSONDict(), and then converts the dictionary
returned into a JSON string.


**Parameters**

No parameters



**Returns**

: The JSON object (in string format)



**Return type**

: str


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `getJSONDict()`

**Definition:** `getJSONDict()`

Get the data to upload.

This returns the dictionary of values to upload to the server,
built from the current request configuration.

This does *not* submit the request.


**Parameters**

No parameters



**Returns**

: The dictionary which will be converted to JSON.



**Return type**

: dict


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `getLightCurvePars()`

**Definition:** `getLightCurvePars(parName='all', showUnset=False)`

Get a light curve parameter.

A wrapper to getProductPar(‘lc’, parName, showUnset).


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `getProduct()`

**Definition:** `getProduct(what)`

Return the requested product object.

This is mainly of use for copying the product to another request.
It will raise a RuntimeError if you haven’t added the product
in question.


**Parameters**

**what** (*string*)
: The product to return



**Returns**

: The instance of the product requested.



**Return type**

: ProductRequest



**Raises**

**RuntimeError**
: If the product requested hasn’t been added.


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `getProductPars()`

**Definition:** `getProductPars(what, parName='all', showUnset=False)`

Return the specified parameter(s).

Return is a dictionary of par:value pairs, for the requested
parameters, or all parameters if parName is unspecified or set
to the string “all”

It will raise a ValueError ‘parName’ or ‘what’ are invalid


**Parameters**


**what** (*string*)
: The product to get the parameter for (lc, spec, psf etc)


**parName**
: The parameter to get, if “all” will return a dictionary of
all parameters


**showUnset** (*bool*)
: Only used if parName is ‘all’, will return all of the
parameters for this product, even if they have not
have values explicitly assigned to them (default: False).



**Returns**

: The value of the requested parameter, or a dict of
parameter:value pairs if ‘all’ was requested.



**Return type**

: Multiple



**Raises**

**RuntimeError**
: If the product requested hasn’t been added.


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `getSpectrumPars()`

**Definition:** `getSpectrumPars(parName='all', showUnset=False)`

Get a spectrum parameter.

A wrapper to getProductPar(‘spec’, parName, showUnset).


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `getStandardPosPars()`

**Definition:** `getStandardPosPars(parName='all', showUnset=False)`

Get a standard position parameter.

A wrapper to getProductPar(‘psf’, parName, showUnset).


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `hasProd()`

**Definition:** `hasProd(what)`

Return whether the request contains given product.


**Parameters**

**what** (*str*)
: The product to check.



**Returns**

: Whether or not the product in question has been added to the
request.



**Return type**

: bool



**Raises**

**ValueError**
: The ‘what’ is not a valid product type.


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `isValid()`

**Definition:** `isValid(what='all')`

Return whether the jobs is ready to submit.

This checks whether all of the required parameters are set. It
does NOT check that the parameter values are valid, so does not
guarantee that the submission will succeed; those checks are
carried out by the server upon submission.

The return is a tuple with two entries:


* status : bool - Whether or not the request is valid.
* expln : str - A string explaning why the request is invalid
(if it is)

**Parameters**

**what** (*list** (**optional**)*)
: A list of the products to check (e.g. [‘lc’, ‘spec’ etc] )
If this is not set, then the validity of the entire request
is checked.



**Returns**

: A 2-element tuple described above.



**Return type**

: tuple



**Raises**

**ValueError**
: If the what argument is invalid.


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `listOldJobs()`

**Definition:** `listOldJobs()`

List all of the jobs you have submitted.

A wrapper to call xrt_prods.listOldJobs().


**Parameters**

No parameters



**Returns**

: A list of your old jobs. See xrt_prods.listOldJobs() for
details.



**Return type**

: list


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `removeAstromPos()`

**Definition:** `removeAstromPos()`

Remove the astrometric position from the current request.

A wrapper to removeProduct(“xastrom”).


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `removeAstromPosPar()`

**Definition:** `removeAstromPosPar(parName)`

Remove an astrometric position parameter.

A wrapper to removeProductPar(“xastrom”, parName).


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `removeEnhancedPos()`

**Definition:** `removeEnhancedPos()`

Remove the enhanced position from the current request.

A wrapper to removeProduct(“enh”).


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `removeEnhancedPosPar()`

**Definition:** `removeEnhancedPosPar(parName)`

Remove an enhanced position parameter.

A wrapper to removeProductPar(“enh”, parName).


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `removeImage()`

**Definition:** `removeImage()`

Remove the image from the current request.

A wrapper to removeProduct(“image”).


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `removeImagePar()`

**Definition:** `removeImagePar(parName)`

Remove an image parameter.

A wrapper to removeProductPar(“image”, parName).


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `removeLightCurve()`

**Definition:** `removeLightCurve()`

Remove a light curve from te current request.

A wrapper to removeProduct(“lc”).


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `removeLightCurvePar()`

**Definition:** `removeLightCurvePar(parName)`

Remove a light curve parameter.

A wrapper to removeProductPar(“lc”, parName).


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `removeProduct()`

**Definition:** `removeProduct(what)`

Removes the specific product ‘what’ from the product request.


**Parameters**

**what** (*string*)
: The product to remove (lc, spec, psf etc)



**Raises**

**RuntimeError**
: If your request doesn’t include the specified product.


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `removeProductPar()`

**Definition:** `removeProductPar(what, parName)`

Remove (unset) a product parameter.

Removes the parameter ‘parName’ from the product ‘what’.


**Parameters**


**what** (*string*)
: The product to get the parameter for (lc, spec, psf etc)


**parName**
: The parameter to get, if “all” will return a dictionary
of all parameters



**Raises**

**RuntimeError**
: If the parameter or product specified are not valid.


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `removeSpectrum()`

**Definition:** `removeSpectrum()`

Remove the spectrum from the current request.

A wrapper to removeProduct(“spec”).


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `removeSpectrumPar()`

**Definition:** `removeSpectrumPar(parName)`

Remove a spectrum parameter.

A wrapper to removeProductPar(“spec”, parName).


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `removeStandardPos()`

**Definition:** `removeStandardPos()`

Remove the standard position from the current request.

A wrapper to removeProduct(“psf”).


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `removeStandardPosPar()`

**Definition:** `removeStandardPosPar(parName)`

Remove a standard position parameter.

A wrapper to removeProductPar(“psf”, parName).


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `retrieveAstromPos()`

**Definition:** `retrieveAstromPos()`

Get the astrometric position.

This function queries the server for the astrometric position and
returns it in a dictionary, if available. The return dict has
the following keys:

GotPos : bool
: Whether a position was retrieved.

If GotPos is True then the following keys are present:

RA : float
: The RA (J2000) in decimal degrees.

Dec : float
: The declination (J2000) in decimal degrees.

Err90 : float
: The 90% confidence radial postion error, in arcseconds.

If GotPos was False then the following key is present:

Reason : str
: The reason no position was retrieved.


**Parameters**

No parameters



**Returns**

: A dictionary with the position and information as described
above.



**Return type**

: dict



**Raises**

**RuntimeError**
: If the job has not been submitted, or didn’t contain a
enhanced position.


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `retrieveEnhancedPos()`

**Definition:** `retrieveEnhancedPos()`

Get the enhanced position.

This function queries the server for the enhanced position and
returns it in a dictionary, if available. The return dict has
the following keys:

GotPos : bool
: Whether a position was retrieved.

If GotPos is True then the following keys are present:

RA : float
: The RA (J2000) in decimal degrees.

Dec : float
: The declination (J2000) in decimal degrees.

Err90 : float
: The 90% confidence radial postion error, in arcseconds.

FromSXPS : bool
: Whether the position was taken from an SXPS catalogue instead
of being calculated afresh.

WhichSXPS : str
: Which SXPS catalogue the position came from (only if FromSXPS
is True)

If GotPos was False then the following key is present:

Reason : str
: The reason no position was retrieved.


**Parameters**

No parameters



**Returns**

: A dictionary with the position and information as described
above.



**Return type**

: dict



**Raises**

**RuntimeError**
: If the job has not been submitted, or didn’t contain a
enhanced position.


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `retrieveStandardPos()`

**Definition:** `retrieveStandardPos()`

Get the standard position.

This function queries the server for the standard position and
returns it in a dictionary, if available. The return dict has
the following keys:

GotPos : bool
: Whether a position was retrieved.

If GotPos is True then the following keys are present:

RA : float
: The RA (J2000) in decimal degrees.

Dec : float
: The declination (J2000) in decimal degrees.

Err90 : float
: The 90% confidence radial postion error, in arcseconds.

FromSXPS : bool
: Whether the position was taken from an SXPS catalogue instead
of being calculated afresh.

WhichSXPS : str
: Which SXPS catalogue the position came from (only if FromSXPS
is True)

If GotPos was False then the following key is present:

Reason : str
: The reason no position was retrieved.


**Parameters**

No parameters



**Returns**

: A dictionary with the position and information as described
above.



**Return type**

: dict



**Raises**

**RuntimeError**
: If the job has not been submitted, or didn’t contain a
standard position.


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `setAstromPosPars()`

**Definition:** `setAstromPosPars(**xastromPars)`

Set the astrometric position parameters.

A wrapper to setProductPars(“xastrom”, \*\*xastromPars).


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `setEnhancedPosPars()`

**Definition:** `setEnhancedPosPars(**enhPars)`

Set the enhanced position parameters.

A wrapper to setProductPars(“enh”, \*\*enhPars).


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `setFromJSON()`

**Definition:** `setFromJSON(JSONVals, fromServer=False)`

Update parameters to match those in a supplied dict.

This sets your request to match the request detailed in the JSON
object or dictionary supplied.  **This will completely destroy
all of the current settings in the request**


**Parameters**


**JSONVals** (*str** or **dict** (**optional**)*)
: If this is set then the request will be created with the
parameters are defined in the JSON dict or string. This
should be of the correct format, i.e. either that you can
get from myRequest.jobPars or myRequest.getJSON() - where
myRequest as an object of this class.


**fromServer** (*bool** (**optional**)*)
: Only allowed if JSON is set. This specifies whether the JSON
is that which was returned by the UKSSDC server upon
successful submission of a request (True), or that created
by this class, ready to submit (False). i.e. if the object
was obtained via myRequest.jobPars this should be true; if
from myRequest.getJSON() then it should be false.



**Raises**

**ValueError**
: If ‘JSONVals’ is not a string or dictionary.


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `setGlobalPars()`

**Definition:** `setGlobalPars(**globPars)`

Set one more more of the XRTProduct global parameters.

Raises a ValueError if an invalid parameter is set, or a
parameter is set to an invalid value


**Parameters**

**\*\*globPars** (*dict*)
: Sets of parameter = value keywords. Parameter must be a
valid global parameter.



**Raises**


**ValueError**
: If invalid parameter or value is specified.


**TypeError**
: If a value passed is the wrong type for the parameter.


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `setImagePars()`

**Definition:** `setImagePars(**imagePars)`

Set the image parameters.

A wrapper to setProductPars(“image”, \*\*imagePars).


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `setLightCurvePars()`

**Definition:** `setLightCurvePars(**lcPars)`

Set the light curve parameters.

A wrapper to setProductPars(“lc”, \*\*lcPars).


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `setProductPars()`

**Definition:** `setProductPars(what, **prodArgs)`

Set the arguments for a product.

Set the arguments for the product ‘what’ to be those in the
prodArgs list.


**Parameters**


**what** (*string*)
: The product to set the parameters for (lc, spec, psf etc)


**\*\*prodArgs**
: The arguments to set



**Raises**


**ValueError**
: If invalid values are specified.


**RuntimeError**
: If the request has already been submitted, so cannot be
edited.


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `setSpectrumPars()`

**Definition:** `setSpectrumPars(**specPars)`

Set the spectrum parameters.

A wrapper to setProductPars(“spec”, \*\*specPars).


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `setStandardPosPars()`

**Definition:** `setStandardPosPars(**psfPars)`

Set the standard position parameters.

A wrapper to setProductPars(“psf”, \*\*psfPars).


<hr style='border: 1px solid #555; margin: 10px auto;' />


### `submit()`

**Definition:** `submit(updateProds=True)`

Submit the job to the UKSSDC server.

This carries out the actual job submission. It checks that the
request is valid, and if so, submits it.  It parses the data
returned by the UKSSDC servers and adds them to this object.
(e.g. the JobID, UserID, URL, etc will be set; or submitError
will be set on failure).

By default, if the submission is successful it will update the
properties of the requested products.  That is, any values you
did not supply will have the accepted defaults completed, and
any calculated values (e.g. position, targetIDs) will also be
saved, with the request to calculate disabled.  This allows you
to use this request as a template for another.


**Parameters**

**updateProds** (*bool**  (**default: True**)*)
: Whether or not the product definitions in this request
should be updated to have the derived or
default parameters added.



**Returns**

: True if the request was submitted and accepted by the
server, otherwise false. On failure the ‘submitError’
attribute of this request object will be set to the
error message.



**Return type**

: bool



**Raises**

**RuntimeError**
: If the request has already been submitted.



---

### XRTProductRequest Variables


### `AstromPos`

Astrometric position request.



### `EnhancedPos`

Enhanced position request.



### `Image`

The image request.



### `JobID`

JobID assigned on successful submission.



### `LightCurve`

LightCurve request.



### `Spectrum`

Spectrum request.



### `StandardPos`

Standard position request.



### `URL`

URL where the products will appear.



### `UserID`

The registered ID of the user.



### `complete`

Whether all of the build jobs are complete.

To query an individual product use checkProductStatus.



### `globalPars`

Dictionary of all global parmeters.



### `hasAstromPos`

Whether the current request has an astrometric position.



### `hasEnhancedPos`

Whether the current request has an enhanced position.



### `hasImage`

Whether the current request has an image.



### `hasLightCurve`

Whether the current request has a light curve.



### `hasSpectrum`

Whether the current request has a spectrum.



### `hasStandardPos`

Whether the current request has a standard position.



### `jobPars`

Dictionary built from subRetData.



### `silent`

Whether to suppress output.



### `status`

Current status of the job.

This is a list with two elements describing the status:
the code, then the textual description.



### `statusCode`

Numerical code describing the status.



### `statusText`

Textual description of the status.



### `subRetData`

All of the data returned by the server after job submission.



### `submitError`

Textual description of why a request submission failed.



### `submitted`

Whether the request has been successfully submitted.


