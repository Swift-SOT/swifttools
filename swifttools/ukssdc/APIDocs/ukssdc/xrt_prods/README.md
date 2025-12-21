# The `xrt_prods` Python module

**This documentation is for `xrt_prods` v1.10, in `swifttools` v3.0** ([Release notes](../ReleaseNotes_v110.md))

The `swifttools.ukssdc/xrt_prods` Python module provides an interface to the [tools to build Swift-XRT data products for
point sources](https://www.swift.ac.uk/user_objects).

**Important note** Our servers have a finite capacity, so please do not submit large numbers of jobs en masse; instead you can use the API to submit all of your jobs, but a few at a time, waiting until the requested jobs have completed before submitting the next tranche. We have provided [an example of how to do this](advanced.md#scripting-large-numbers-of-jobs).

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

The `xrt_prods` module is part of the `swifttools` package. The easiest way to install this is via `pip`:

```bash
> pip3 install swifttools
```

Alternatively, you can [download the sourcecode from GitHub](https://github.com/Swift-SOT/swifttools) and install it manually if you prefer.

This requires Python 3.6 or higher.

The module obviously needs to be imported before use; there is a single
class which you will need to use: `XRTProductRequest`.

For consistency with other parts of the `swifttools.ukssdc` module, in this documentation we assume
that you import the module thus:

```python
import swifttools.ukssdc.xrt_prods as ux
```

and this `import` line is generally omited from the examples. There are a small number
of exceptions to this, covered on the [Miscellaneous methods and advanced usage](advanced.md) page.

To use this module you will need to create an object of the `XRTProductRequest` class, set parameters in it, and submit
it. The very simple example below is not directly runable as I've left out the actual parameter values, but it gives a
simple feel for the interface. The specific parameters and options are detailed on the [relevant pages in this
documentation](#documentation-contents). **In particular, the full set of all possible parameters that you can set for
the request are given on the [How to request products](RequestJob.md) page**.

**Please note** Our servers have finite capacity, and we ask you to be considerate in your submissions: do not
request large numbers of jobs in quick succession. There is a hard limit on the server of how many jobs a user
can have in the queue at any one time which is currently very generous but may be tightened depending on need.
On the [advanced usage page](advanced.md#controlling-the-number-of-active-jobs) we demonstrate how to keep track of how many
jobs you have on the server and throttle your submission rate accordingly.

### Very simple example:

```python
import swifttools.ukssdc.xrt_prods as ux

# Create an XRTProductRequest object
myReq = ux.XRTProductRequest('YOUR_EMAIL_ADDRESS', silent=False)

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

**Another note** If you are an experienced Python user, familiar with PEP8, you're probably already cursing me. "Why," you will
be asking, "are your functions `addLightCurve()` instead of `add_light_curve()`? Are you not aware of Python conventions
and standards?" To which the answer is, of course, that actually, no, I wasn't! This module was my first major forray into Python,
and while I did make considerable efforts to comply with the PEP8 and PEP257, this convention/rule passed me by, and now it
is inappropriate to change everything. In my defense, PEP8 actually says:

> mixedCase is allowed only in contexts where that’s already the prevailing style (e.g. threading.py), to retain backwards compatibility.

This module is part of a larger set of software and services at the UKSSDC (albeit comprising the back end) which
all use mixedCase, because this is the convention I am familiar with. So I think we can all agree that this is actually
PEP8 compliant &#128539;
