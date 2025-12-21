# How to cancel a job

It may occasionally happen that, after submitting your product request to the UKSSDC servers, you realise that you don't need them, or you made a mistake, or one of the requested products is unnecessary. In this case you can ask the UKSSDC server to cancel the jobs. We do ask that you do this when appropriate, to reduce load on our servers and shorten the queueing time for products that people need.

**Note**: Cancellation refers to an actual product build job &#8212; a request that has been successfully submitted. If you have added a product to your request and not submitted you can just use the `removeLightcurve()` (etc) methods [described on the product request documentation page](RequestJob.md#managing-specific-products)

To cancel a submitted job, simply call the `cancelProducts()` method of your `XRTProductRequest` instance. This takes a single, optional argument detailing which product(s) to cancel. This can either be the string 'all' (to cancel all requested products) or a tuple/list of the product names. e.g.

```python
In [1]: cancelStatus = myReq.cancelProducts(('LightCurve', 'StandardPos')) # Cancel only the light curve and standard position
In [2]: cancelStatus = myReq.cancelProducts() # same as myReq.cancelProducts('all')
```

`cancelProducts()` returns some information to let you know whether the request to cancel the products were successful or not. In the above, I captured this in the `cancelStatus` variable.

This variable is a list with two entries, thus:

* `cancelStatus[0]` = cancelled OK? An int with the following possible values
  * -1 = HTTP error. Either the request was not sent, it was rejected by the server, or the data returned by the server was not understood by the Python module (meaning either there was a server error, or you need to update the Python module).
  * 0 = Cancellation error - the request was received by the server, but your jobs were not cancelled.
  * 1 = OK - requested job were cancelled.
  * 2 = Partial success. The request was processed OK, but not all requested jobs were cancelled.
* ProductStatus = dict, with one entry per product. This dict itself will have 2 entries, one designed for the computer to read, one for you:
  * code = an integer status code with the following possible values:
     *  0 = Success, job cancelled.
     *  1 = Job not cancelled, most likely it has already completed.
     *  2 = Job not cancelled, no record of this product could be found for this jobID.
     *  3 = Job not cancelled, reason unknown.
     *  4 = Status unknown: an error occured meaning we can't determine whether or not the job was cancelled.
  * text = A textual description of the status.


This is probably best understood by means of some examples. So, here is a case where we requested simply to cancel a light curve, and it was successful. I've actually printed it 3 times below just to help with clarity: the first statement prints the entire object; the second statement just prints the summary code, and the final statement shows the `LightCurve` entry.

```python
In [3]: print(cancelStatus)
(1, {'LightCurve': {'code': 0, 'text': 'Job cancelled OK'}})

In [4]: print(cancelStatus[0]) # Just get the overall status
1

In [5]: print (cancelStatus[0]['LightCurve']) # Just get the light curve status
{'code': 0, 'text': 'Job cancelled OK'}
```

So we can see here that the cancellation was OK ( `cancelStatus[0]==1`). Then looking at the light curve entry we can see that this has status code 0 = OK, and the text confirms this.

Here's a slightly more complex case. I've submitted a request for a light curve and a standard position. I will cancel first the light curve, and then everything:


```python
In [6]: ok, cancelStatus = myReq.cancelProducts(['LightCurve'])
In [7]: ok
Out[7]: 1

In [8]: cancelStatus
Out[7]: {'LightCurve': {'code': 0, 'text': 'Job cancelled OK'}}

In [8]: ok, cancelStatus = myReq.cancelProducts()
In [9]: ok
Out[9]: 2

In [10]: cancelStatus
Out[10]:
{'LightCurve': {'code': 1, 'text': 'Job could not be cancelled - has it already finished?'},
 'StandardPos': {'code': 0, 'text': 'Job cancelled OK'}}
```

So first I cancelled the light curve, which returned an `OK` value of 1 (success) and the `LightCurve` status and code within `cancelStatus` confirm this.
Next I cancelled everything. This time, OK came back as 2 (partial success). Looking at the `cancelStatus` dictionary, I can see that the light curve could not be cancelled (not surprising, since we'd already cancelled it) but the standard position was cancelled fine.
