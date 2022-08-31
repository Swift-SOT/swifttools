# Examining your submitted job

When you successfully [request some products](RequestJob.md), the following properties of your `XRTProductRequest` object are set:

* `JobID` - the ID of the job on the server. This is used internally for any future operations on this job ([cancelling it](CancelJob.md), [checking the status](JobStatus.md) or [downloading the products](RetrieveProducts.md)).
* `URL` - this is the URL where your products will be stored, if you want to view them online.
* `subRetData` - this is a dictionary containing:
  * `submitError` - the error message if the server rejected the request.
  * `URL` - the URL as above (the `XRTProductRequest.URL` variable is actually a short-cut to this value).
  * `jobPars` - a dictionary listing all of the parameters associated with your job.


This last entry, `jobPars`, may at first glance seem superfluous: why does the server need to send us a list of the parameters which we sent to it? The reason is because we may not have sent a complete list of parameters. In some cases we may have simply allowed the server to give us the defaults. In some cases we may have asked the server to calculate some parameters for us (e.g. if we set `getCoords=True`). So, the `subRetData['jobPars']` dictionary allows us to confirm exactly what parameters were used to build our products.

For historical reasons, the parameters used interally by the server have names which are not very friendly or helpful. The Python module presents you with some more sensible names and then internally converts them before submitting. This means that if you just examime the  `subRetData['jobPars']` dictionary it may look a bit incomprehensible. This is why the `submit()` method has the  `updateProds` argument.  When `submit()` is called with `updateProds=True` (the default), then
on successful submission, the Python module will go through the `subRetData['jobPars']` dictionary and update all of the internal parameters of your request according to the contents of that dictionary. You can then examine them using the `getAllPars()` method. The outputs below show the difference.


```python
In [1]: myReq.subRetData['jobPars']
Out[1]:
{'api_name': 'xrt_prods',
 'api_version': '0.1',
 'UserID': 'YOUR_EMAIL_ADDRESS',
 'cent': 1,
 'name': 'GRB 200416A',
 'RA': '335.6985',
 'Dec': '-7.5179',
 'centMeth': 'simple',
 'useSXPS': 0,
 'Tstart': 608713541.952,
 'poserr': 1,
 'lc': 1,
 'binMeth': 'counts',
 'pccounts': '20',
 'wtcounts': '30',
 'dynamic': 1,
 'spec': 1,
 'specz': 0,
 'dopsf': 1,
 'doenh': 1,
 'doxastrom': 1,
 'allxastrom': 1,
 'whatSXPS': '2SXPS',
 'image': 0,
 'sss': '0',
 'sinceT0': 0,
 'lcobs': 0,
 'hrbin': 0,
 'do3col': 0,
 'enh': 0,
 'wtpuprate': 150,
 'pcpuprate': 0.6,
 'maxCentTries': '10',
 'soft1': '0.3',
 'soft2': '1.5',
 'hard1': '1.5',
 'hard2': '10',
 'minen': '0.3',
 'maxen': '10',
 'grades': 'all',
 'sigmin': '3',
 'allowUL': 'both',
 'allowB': 'both',
 'bayesCounts': 15,
 'bayesSNR': 2.4,
 'lctimetype': 's',
 'pcbin': '2.51',
 'wtbin': '0.5',
 'ratefact': '10',
 'binfact': '1.5',
 'mincmin': '15',
 'minsnr': 1.5,
 'pcmaxbin': 100000000,
 'wtmaxbin': 100000000,
 'pcmaxgap': 100000000,
 'wtmaxgap': 100000000,
 'femin': '0',
 'timeslice': 'single',
 'specobs': 'hours',
 'specobstime': 12,
 'specgrades': 'all',
 'posRadius': '20',
 'posobs': 'hours',
 'posobstime': 12,
 'detornot': 'detect',
 'detMeth': 'simple',
 'targ': '00966554'}
```

You can see that some of these parameter names are not listed in the tables on the [requesting products page](RequestJob.md). On the other hand, if we list the parameters associated with the request, having submitted it we get this:


```python
In [2]: myReq.getAllPars()
Out[2]:
{'name': 'GRB 200416A',
 'targ': '00966554',
 'T0': 608713541.952,
 'RA': 335.6985,
 'Dec': -7.5179,
 'centroid': True,
 'centMeth': 'simple',
 'maxCentTries': 10,
 'posErr': 1,
 'sss': False,
 'useSXPS': False,
 'wtPupRate': 150,
 'pcPupRate': 0.6,
 'getTargs': True,
 'LightCurve': {'binMeth': 'counts',
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
  'timeFormat': 's',
  'rateFact': 10.0,
  'binFact': 1.5,
  'minCounts': 15,
  'minSNR': 1.5,
  'pcmaxGap': 100000000,
  'wtmaxGap': 100000000,
  'minFracExp': 0.0},
 'Spectrum': {'hasRedshift': False,
  'grades': 'all',
  'timeslice': 'single',
  'whichData': 'hours',
  'incHours': 12},
 'StandardPos': {'whichData': 'hours',
  'incHours': 12,
  'posRadius': 20.0,
  'detOrCent': 'detect',
  'centMeth': 'simple'},
 'EnhancedPos': {'whichData': 'hours',
  'incHours': 12,
  'posRadius': 20.0,
  'detOrCent': 'detect',
  'centMeth': 'simple'},
 'AstromPos': {'useAllObs': True,
  'whichData': 'hours',
  'incHours': 12,
  'posRadius': 20.0,
  'detOrCent': 'detect',
  'centMeth': 'simple'}}
```

The parameters are now organised by product, and have the same names that we would supply
when setting them, which is rather easier to follow.
