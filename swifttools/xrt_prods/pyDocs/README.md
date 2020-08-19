# The `xrt_prods` Python module

The `xrt_prods` Python module provides an interface to the tools to build Swift-XRT data products for point sources.
This is based on the [XRT Products API](../APIDocs/README.md), but is intended to present a rather easier interface
than having to create and manage JSON objects and HTTP POST requests yourself.

**Important note** We still have a finite capacity, so please do not submit large numbers of jobs en masse; instead you can use the API to submit all of your jobs, but a few at a time, waiting until the requested jobs have completed before submitting the next tranche. 


## Documentation contents

The documentation is organised as follows.

 * [Introduction / quickstart](README.md)
 * [How to request products](RequestJob.md).
 * [Examining your submitted job](ReturnData.md).
 * [How to cancel requested jobs](CancelJob.md).
 * [How to query the status of a job](JobStatus.md).
 * [How to retrieve the completed products](RetrieveProducts.md).
 * [A simple end-to-end tutorial](tutorial.md).
 * [Miscellaneous methods and advanced usage](advanced.md).
 
 
## Registration

In order to use the API you must register and confirm your email address. No password is needed, and you will never need to log in, however you do need to supply your registered email address with any request or query, and you will only be able to retrieve details about your own jobs via the API. This is primarily for book keeping purposes.

To register, please visit [the registration page](https://www.swift.ac.uk/user_objects/register.php) in your web browser. After supplying your email address you will be emailed a link to verify said address.

## Summary and quick start

The `xrt_prods` module is part of the `swifttools` package, which must
obviously be imported before use. Within the module there is a single
class which you will need to use: `XRTProductRequest`.

In the examples throughout this documentation, it is assumed that you have imported this thus:

```python
from swifttools.xrt_prods import XRTProductRequest
```

and this `import` line is generally ommited from the examples.

To use this module you will need to create an object of this class, set parameters
in it, and submit it. The very simple example below is not directly
runable as I've left out the actual parameter values, but it gives a
simple feel for the interface. The specific parameters and options are
detailed on the [relevant pages in this
documentation](#documentation-contents). **In particular, the full set
of all possible parameters that you can set for the request are given on
the [How to request products](RequestJob.md) page**.

**Please note** Our servers have finite capacity, and we ask you to be considerate in your submissions: do not
request large numbers of jobs in quick succession. There is a hard limit on the server of how many jobs a user
can have in the queue at any one time which is currently very generous but may be tightened depending on need.
On the [advanced usage page](advanced.md#controlling-the-number-of-active-jobs) we demonstrate how to keep track of how many
jobs you have on the server and throttle your submission rate accordingly.

### Very simple example:

```python
from swifttools.xrt_prods import XRTProductRequest

# Create an XRTProductRequest object
myReq = XRTProductRequest('YOUR_EMAIL_ADDRESS', silent=False)

# Set the global parameters
myReq.setGlobalPars (centroid=True, ...etc ...)

# Add a light curve
myReq.addLightCurve ( **somePars)

# An an enhanced postion
myReq.addEnhancedPos ( **somePars)

# Submit the job - note, this can fail so we ought to check the return code in real life
myReq.submit()

# Now wait until it's complete
done=myReq.complete
while not done:
  time.sleep(60)
  done=myReq.complete

# And download the products
myReq.downloadProducts('/my/path/', format='zip')
```

And that's it. Except that you need to know what parameters you can set, how to check that your submission worked, and much more. So follow the links in the [contents, above](#documentation-contents) for more details.

**Note** In the example above, and throughout this guide, I have created the `XRTProductRequest` with `silent=False`; the default, if `silent` is not
specified, is `True`. This variable, which can also be set directly (i.e. `myReq.silent=True`) controls whether any feedback is
written to the standard output. In interactive mode, this feedback may be helpful and informative; in a script, it is more
likely an annoyance. Since all of the examples in this documentation are for an interactive shell, I have always set `silent=False`.

**Another note** As most Python users will be aware, the `import` convention used in this documentation is not the only
possibly convention. For example, you could do `import swifttools.xrt_prods` and then access the main class via
`xrt_prods.XRTProductRequest` if you prefer not to pollute your global namespace. Or you could save your fingers a little
with `from swifttools.xrt_prods import XRTProductRequest as xpr` (at the cost of making your code a little less readable). It is not the purpose of this guide to suggest how you style your code; I have used the `from swifttools.xrt_prods import XRTProductRequest` convention from personal choice, and as I think it makes the guide easier to read.