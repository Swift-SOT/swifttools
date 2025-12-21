# Checking the progress of the job

After submitting your product request, you need to be able to check the status of the job on the server, so that you know when your products are
ready to download - or whether something has gone wrong.

The `XRTProductRequest` class contains two ways of checking whether your products are ready: [the `complete` variable](#the-complete-variable), and [the `checkProductStatus()` method](#querying-the-product-status).

Obviously, if your products are not complete you will need to continue to poll them until they are. We ask that you do not overdo this, for the sake of our servers: it should not normally be necessary to poll more often than once a minute.

---

## The complete variable

`complete` is a boolean variable that simply reports whether or not the jobs to build your requested products have all finished. i.e.

```python
In [1]: myReq.complete
True
```

(Or `False` as the case may be). This may take a moment to respond because, until the products are actually complete, when you access this variable Python will poll the UKSSDC servers to check the job status.

**Important note** This variable only reports whether the jobs to build the products have completed. It does not tell you whether they completed *successfully*. If you cancelled all of the jobs, or if they failed, this variable will still be `True`. If you want to check the actual status of the different products, you need to use [the `checkProductStatus()` method](#querying-the-product-status)...

---

## Querying the product status

To query the product status, use the `checkProductStatus()` method. This takes a single, optional argument detailing which product(s) to query. This can either be the string 'all' (to query all requested products) or a tuple/list of the product names. e.g.

```python
In [2]: prodStatus = myReq.checkProductStatus(('LightCurve', 'StandardPos')) # Poll only the light curve and standard position
In [3]: prodStatus = myReq.checkProductStatus() # same as myReq.checkProductStatus('all')
```

This returns a dictionary with one entry per product. Each of these entries is in turn a dictionary with four entries:

* [statusCode](#status-code)
* [statusText](#status-text)
* [progressText](#progress-text)
* [progress](#progress)

### Status code

This is an integer code, describing the current status of the product. This is complementary to [statusText](#status-text); this code is for machine use, the text is for humans to read.

It can have any of the following values:

 * -10 = No status returned by the server. Implies something has gone wrong!
 * -4 = The job was cancelled by the user (i.e. you).
 * -3 = The product could not be built, the job was called OK, but did not produce a product.
 * -2 = An internal error occurred at the UKSSDC, and the attempt to add the job to the queue failed.
 * -1 = An internal error occured at the UKSSDC, and the job could not even be requested.
 * 1  = Job has been requested, but not yet queued.
 * 2  = Job has been entered into our processing queue.
 * 3  = The job is actually running (progress information may be available)
 * 4  = The job completed OK. Your products are available
 * 5  = [Status code only for astrometric positions]: the astrometry is waiting for the standard PSF position to be produced, and will then correct that.

Codes -2 and -3 should never exist, and most likely indicate either a transient fault with one of our servers or services, or that one of the executable scripts has become corrupted. **If you get one of these errors please email us immediately on swifthelp@leicester.ac.uk**. It is probable that we already know of the issue, but not certain, so a prompt report of the error will enable us to fix it.

### Status text

The status text is a human-readable description of the status of the product. This is complementary to [statusCode](#status-code); this text is for human use, the code is for use by your scripts.

### Progress text

This is a human-readable string giving a summary of the current progress for the product. This is contructed from the [progress](#progress) entry.
It lists the various stages involved in creating the product, indicating which ones are done and which is in progress.

Progress information is only available for prodcuts that are currently running (`statusCode: 3`).

### Progress

This is another dictionary, containing the various steps involved in creating the product, along with their status and other information. We provide this for completeness, however it is a complex structure and we suggest that you use the [progressText](#progress-text) entry instead, as that is a ready-to-read string created from this entry.

If you do want to use the `progress` entry directly, then its contents are described in detail in the [raw API documentation](../APIDocs/JobStatus.md); note that on those pages it is described as a JSON object whereas within the Python module it has been converted to a dictionary, however these are directly analogous.

---

## Examples

The output of [the `checkProductStatus()` method](#querying-the-product-status) is described above, but it's much easier to explain with examples.

First, let's just get the status of everything, and then print the human-readable summary:

```python
In [4]: prodStatus = myReq.checkProductStatus()
In [5]: for prod,status in prodStatus.items():
    ...:     print (f"{prod} -> {status['statusText']}")
    ...:
LightCurve -> Running
Spectrum -> Running
StandardPos -> Running
EnhancedPos -> Running
AstromPos -> Running
```

As you can see, in this example I had requested all products be built, and they are all currently underway. Of course, we could have examined the `statusCode` instead; that's more helpful for a script to make decisions based on:

```python
In [6]: for prod,status in prodStatus.items():
    ...:     print (f"{prod} -> {status['statusCode']}")
    ...:
LightCurve -> 3
Spectrum -> 3
StandardPos -> 3
EnhancedPos -> 3
AstromPos -> 3
```

Well, that was exciting. Let's have a look at the full progress report for the enhanced position:

```python
In [7]: print (prodStatus['EnhancedPos']['progressText'])
Trying using the <em>v,b,white</em> filters:
  Identify XRT-UVOT overlaps. - DONE
  ** Determine position. - ACTIVE -- Working on overlap 1 / 1**
  Build Images.

The job has been running for 00:00:08
```

This tells us that the code has passed the first step (identifying overlaps) and is currently determining the position, working on overlap 1 out of 1. There is one more step - building images - to go. The job had been running for 8 seconds when I polled it. **Note** this doesn't mean it's 8 seconds since I submitted the job, it means it's 8 seconds since the server began executing the job. If the servers are busy, jobs may sit in the queue for some time before they start running.

Of course, there is more you can do here: you could examine the `progress` entry in detail if you want, but you don't. Seriously. Oh, OK then:


```
In [8]: prodStatus['Spectrum']['progress']
{'GotProgress': 1,
 'ProgressSteps': [{'StepLabel': 'Prepare data.', 'StepStatus': 2},
  {'StepLabel': 'Build spectra.',
   'StepStatus': 1,
   'StepExtra': 'Working on spectrum: interval0 (1/1)',
   'SubStep': [{'StepLabel': 'Extract data.',
     'StepStatus': 1,
     'StepExtra': 'Working on observation 1 / 1'},
    {'StepLabel': 'Fit spectrum.', 'StepStatus': 0}]}],
 'TimeRunning': '00:00:08'}
 ```

 It isn't so bad (it can get rather more messy than this) but the `statusText` entry had done the job of parsing this for us,
 so for human-readable cases, it makes more sense to use that.
