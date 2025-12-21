# Miscellaneous methods and advanced usage

## Contents

* [Controlling the number of active jobs](#controlling-the-number-of-active-jobs)
* [Scripting large numbers of jobs](#scripting-large-numbers-of-jobs)
* [Copying old requests](#copying-old-requests)
  * [Copying entire requests](#copy-an-entire-request)
  * [Copying specific products](#copy-a-specific-product)
  * [Reproducing an old request](#reproduce-an-old-request).
  * **[Really big caveat](#really-big-caveat)**

---

## Controlling the number of active jobs

The main purpose of this API is to make it easy for you to submit jobs, and to automate this into
your analysis pipelines. **But we ask you to be considerate as you do so.** Submitting vast numbers of
jobs will monopolise or overload our servers, and we'd really rather you don't. A simple way of managing this
is to check how many jobs you currently have queued or running, and to throttle your submission rates accordingly.
For this we have the `countActiveJobs()` method. This is actually a method of the `xrt_prods` module, so to use this directly, you need to import that module to use this function. Here, I have assumed you have done `from swifttools import xrt_prods`, and then we can check the number of active jobs thus:

```python
In [1]: howMany = ux.countActiveJobs('YOUR_EMAIL_ADDRESS')
```

However, for the sake of ease the `XRTProductRequest` class has a wrapper to this using the `UserID` value of
your class, i.e. if you have created a request, `myReq` then:

```python
In [2]: howMany = myReq.countActiveJobs()
```

is the same as the call above.

So you can easily throttle job submission in your scripts, for example with a structure as in this snippet:

```python
import swifttools.ukssdc.xrt_prods as ux
import time
import sys
myReq = ux.XRTProductRequest('YOUR_EMAIL_ADDRESS')
...
my waited = 0
while (myReq.countActiveJobs()>5):
    print("Going to wait a moment - too many jobs")
    time.sleep(30)
    waited+=30
    if waited>3600:
      print("OK, I'm bored")
      sys.exit(1)
ok = myReq.submit()
...
```

There is a hard limit on the server of how many jobs a user can have in the queue at any one time.
At the moment it is pretty generous, but it may be changed, depending on usage and load. We would much
prefer not to have to enforce restrictions, so please do be considerate in your usage.

---

## Scripting large numbers of jobs

A large part of the motivation for providing this API is for those users who want to analyse a large number
of objects, for which the website does not really offer an ideal interface. It is obviously beyond the scope
of this documentation to define exactly how one would write such a script, and it will depend upon the needs
and personal coding style and preference. Below we do give a simple example, or framework that could be adapted.
Crucially, this example controls the maximum number of jobs you may want to submit.

This example is not complete, and it includes calls to functions that are not defined in the example, but from their
names you can identify what they have to do. This is not intended as some code to copy and paste, but rather as a
demonstration of how one may use this API.

```python
import swifttools.ukssdc.xrt_prods as ux
import time
# Other imports

max_jobs = 5 # How many jobs we'll submit in any one go.
my_email = "me@myinstitute.countryCode"

productsIWant = someFunctionToDefineWhatIWant() # Exercise for reader: write this function :)

myReqs = [] # This will hold the requests.
ix=0

while ix < len(productsIwant):

    # Check if any jobs have finished, and download the products if they have
    # NB, on the first run this will of course not do anything, because ix=0
    ctr = 0
    for i in myReqs:
        if i.complete:
            i.downloadProducts('/mydir', stem='myProd_'+str(ctr))
        ctr = ctr + 1

    # Submit as many as I can:
    while ux.countActiveJobs(my_email) < max_jobs:
        # Create the new XRTProductRequest
        myReqs.append(ux.XRTProductRequest(my_email))
        # Set its details
        g = productsIWant[ix].globalPars
        myReqs[ix].setGlobalPars(**g)
        if productsIWant[ix].hasLightCurve:
          l = productsIWant[ix].lcPars
          tmpReq.addLightCurve(**l)
        # etc for spectrum, pos &c

        # Submit the job
        # You probably want to capture the return value of this
        # and do something if it fails
        myReqs.submit()
        ix = ix + 1

    # OK, now we've submitted as many jobs as we can at one time
    # Let's give them time to run, and then try again
    time.sleep(120)
    print (f"I have submitted {ix} / {len(productsIwant)} jobs")

# OK, if we're here all jobs have been submitted.
# Can go through myReqs[] and download them all.
```

This is a pretty rudimentary script, and far from optimal. A real script would
probably want to check to see if the jobs submit OK, for example; and in the
download loop it would probably want to use [`checkProductStatus`](JobStatus.md#querying-the-product-status)
to note any failures and only download things that completed OK.
You may also want some `try:` and `except:` blocks in there so that any errors
are handled gracefully. However, it gives a reasonable example of how one could go about
requesting a large number of jobs in a controlled way.

---

## Copying old requests

All of the documentation so far has focussed on one-off product requests. In reality your requests may well not be independent. You may want to run the same request every time your source is observed; or you may want to build the same set of products for a range of parameters. In this case, rather than having to duplicate a lot of input, there are some useful methods or variables for passing this information around. Below we split this into three parts:
[copying entire requests](#copy-an-entire-request),  [copying specific products](#copy-a-specific-product), and [reproducing an old request](#reproduce-an-old-request). Please also see the [really big caveat](#really-big-caveat) at the end of this section.

### Copy an entire request

At first glance you may think that it's easy to copy a request: `myNewReq = myOldReq`. But this is not a good idea. When a request is submitted you can't edit it, so if you do this after submitting a request then `myNewReq` is useless. On the other hand, if you do this before submitting the request then the only parameters you can **guarantee** will be the same between product requests are the parameters you set. Any parameters you don't set will be assigned default value by the server, and while we have no plans to change these, we offer no guarantee that they will not change. And your request may ask the server to fill out some parameters, such as the target IDs that overlap your source, or the source position. These can also change and Swift carries out new observations, or as name resolvers are updated with improved positions.

Instead there are two ways you can copy the data from one request to another.

* The `XRTProductRequest` constructor can receive a set of parameters, either as a JSON object or a dictionary.
* Using the `setFromJSON()` method. **This will completely overwrite any settings the request you call it on.**

i.e.

```python
In [1]: myNewReq = ux.XRTProductRequest('YOUR_EMAIL_ADDRESS', JSONVals=something) # constructor method
In [2]: myNewReq.setFromJSON(something) # other method. myNewReq already exists, and 'something' is the JSON object/dict
```

This alone doesn't help, because we need to create the data, represented above as `something`. Fortunately we thought of that too, and we provide method `getJSON()` or `getJSONDict()` which dump out the status of the existing request. So we can recast the above calls:

```python
In [3]: myNewReq = ux.XRTProductRequest('YOUR_EMAIL_ADDRESS', JSONVals = myOldReq.getJSONDict() ) # constructor method
In [4]: myNewReq.setFromJSON( myOldReq.getJSONDict()) # other method. myNewReq already exists
```

Or, in the case that you want to build your products periodically, after new observations, you may do something like this:

```python
In [5]: myJSON = myOldReq.getJSON()
In [6]: # Write myJSON to a file
...
# A week later
In [213]: # Load myJSON from that file
In [214]: myNewReq = ux.XRTProductRequest('YOUR_EMAIL_ADDRESS', JSONVals = myJSON)
```

**Important note** If you run this before submitting `myOldReq` you have the same problem as in a direct copy: you are trusting that nothing important will change between submitting `myOldReq` and `myNewReq`. But the above also assumes that when you called `myOldReq.submit()` you let the `updateProds` argument retain its default value of `True`. If you set it to `False`, then the `myOldReq` did not update with the values from the server, so the above assignments only copied the pre-submission data.

This is why `updateProds` is `True` by default. But don't despair: if for some reason you want to set this to false, you can still get hold of the parameters returned by the server, and pass those around. These are stored in the `subRetData['jobPars']` dictionary [set when you submitted the job](ReturnData.md). As
[discussed elsewhere](ReturnData.md), the names of these parameters don't match those used by the Python API, so if you want to use these values, you need to pass an extra argument when you assign these values: `fromServer=True`, i.e.

```python
In [7]: myNewReq = ux.XRTProductRequest('YOUR_EMAIL_ADDRESS', JSONVals = myOldReq.subRetData['jobPars'], fromServer=True ) # constructor method
In [8]: myNewReq.setFromJSON( myOldReq.subRetData['jobPars'], fromServer=True) # other method. myNewReq already exists
```

If you want to save the data from your original request to come back to it later, it may be easier to do this as a JSON object:

```python
In [9]: myJSON = json.dumps(myOldReq.subRetData['jobPars'])
In [10]: # Write myJSON to a file
...
# A week later
In [217]: # Load myJSON from that file
In [218]: myNewReq = ux.XRTProductRequest('YOUR_EMAIL_ADDRESS', JSONVals = myJSON, fromServer=True)
```

---

### Copy a specific product

Maybe you don't want to duplicate an entire product request, but you do want the specifications of one of the products to stay the same; such as if you want to create light curves of 80 different objects, all with the same light curve parameters.

For this you can access the products within your request directly, and assign them, thus:

```python
In [1]: myNewReq = ux.XRTProductRequest('YOUR_EMAIL_ADDRESS')
In [2]: myNewReq.LightCurve = myOldReq.LightCurve
```

And we can check this has worked if we want:

```python
In [3]: myNewReq.getLightCurvePars()
Out[3]:
{'binMeth': 'counts',
 'pcCounts': 20,
 'wtCounts': 30,
 'dynamic': True,
 'matchHR': 0,
 'softLo': 0.3,
 'softHi': 1.5,
 'hardLo': 1.5,
 'hardHi': 10.0,
 'minEnergy': 0.3,
 'maxEnergy': 10.0,
 'grades': 'all',
 'minSig': 3.0,
 'allowUL': 'both',
 'allowBayes': 'both',
 'bayesCounts': 15,
 'bayesSNR': 2.4,
 'timeType': 's',
 'rateFact': 10.0,
 'binFact': 1.5,
 'minCounts': 15,
 'minSNR': 1.5,
 'pcMaxGap': 100000000,
 'wtMaxGap': 100000000,
 'minFracExp': 0.0}
```

Yep, that worked. Replace `LightCurve` with `Spectrum`, `StandardPos`, `EnhancedPos`, `AstromPos` or `Image` as appropriate.

---

### Reproduce an old request

The above examples both assume your Python session has been persistent, so you can pass parameters between
objects. This will often not be the case. So you can also create a request from a previous request,
provided that you know the jobID, and that you own that job.

This is done thus:

```python
In [1]: myNewReq = ux.XRTProductRequest('YOUR_EMAIL_ADDRESS')
In [2]: myNewReq.copyOldJob(868)
```

Here, job 868 was retrieved from the server.

There is an optional argument to `copyOldJob`: `becomeThis`. If this is `True` then `myNewReq` will act as if
it actually is job 868, rather than a duplicate of it. This means that it cannot be submitted, but you can
download the products for that job (if they still exist). `becomeThis` is `False` by default.

Of course, you may not remember what the jobID of the job you ran 6 months ago was, in which case read on...

### List old requests

If you want to recover some information about one of your previous jobs, perhaps so that you can reproduce one,
then you need the ``listOldJobs()`` method. This is actually a method of the ``xrt_prods`` module, so is called thus:

```python
In [1]: myOldJobs = ux.listOldJobs('YOUR_EMAIL_ADDRESS')
```

(as above, this assumes you have first done `from swifttools import xrt_prods`).

However, for the sake of ease the ``XRTProductRequest`` class has a wrapper to this using the ``UserID`` value of
your class, i.e.

```python
In [2]: myOldJobs = myReq.listOldJobs()
```

is the same as the call above.

This will return a list, containing one entry for every job you have ever requested using the supplied email
address, either via the API or directly on the website. The list is in reverse order of jobID, i.e. most recent jobs first.
Each entry is a dictionary, thus:

```python
In [3]: myOldJobs[8]
Out[3]:
{'JobID': 2870,
 'Name': 'GRB 200116A',
 'DateSubmitted': '2020-07-07 14:05:17',
 'LightCurve': False,
 'Spectrum': False,
 'StandardPos': False,
 'EnhancedPos': False,
 'AstromPos': False,
 'Image': True,
 'hasProd': False}
```

The keys are the JobID, the name I have to the object, the date the request was submitted and then a series of ``bool``s indicating
which products were requested. The last entry ``hasProd`` tells me whether the products I requested are still available or not. In this case, not.

This list in itself can be quite long (at the time of writing, I have 66 old jobs), but being a list we can easily filter
it using list comprehensions. For example, let us assume that I want to find an old request I made to analyse GK Per:

```python
In [4]: gkperJobs = [x for x in oldJobs if x['Name']=='GK Per']
In [5]: len(gkperJobs)
Out[5]: 12
```

In this case I've still got 12 jobs (look, I did a lot of testing of this API, OK?). So I could have filtered more strictly, say if I knew the job I was after had requested a light curve:

```
In [6]: gkperJobs = [x for x in oldJobs if x['Name']=='GK Per' and x['LightCurve]]
In [7]: len(gkperJobs)
Out[7]: 7
```

and so on. It is not the purpose of this guide to teach list comprehensions or other methods of filtering Python objects, but to demonstrate that the ``listOldJobs()`` function output can be readily filtered or searched to find what you
are looking for.

---

### Really Big Caveat

There is one thing you should bear in mind when trying to reproduce requests: the Swift data archive keeps changing, because Swift is still observing. Practically, what this means is that if you set `whichData='all'` for any product then there is no guarantee that every time you build this product you will get the same output. If you request the job in January, and then again in May, and Swift has been observing your target weekly, then the product build in May will contain a lot more data.

Of course, this may well be what you want. We don't expect people to be routinely trying to rebuild products identical to those they made in the past (Ok, you accidentally deleted the products once, but regularly?), and it's more likely that for re-submitted jobs you are resubmitting precisely because we have more data. But you should bear this in mind. If you find a re-run request results in unexpected changes, the first thing to do is find the log files in your downloaded products and see if the set of observations used has changed.

It's also worth noting that we do periodically reprocess the entire XRT data archive, if there is a significant change either to the analysis software or to the calibration: obviously this will have an effect on any products created before/after the reprocessing.
