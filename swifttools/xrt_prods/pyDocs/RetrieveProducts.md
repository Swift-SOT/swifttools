# How to retrieve the products

Once your [products are complete](JobStatus.md) you will, one assumes, wish to access them. There are three things you can retrieve:

* [The data files.](#download-the-data)
* [The positions](#retrieve-the-position)
* [The source list](#retrieve-the-source-list)

## Download the data

To download the set of data produced for your request, you need the `downloadProducts()` method.

This method has a single mandatory parameter: the directory into which you wish to save the products. Thus, the easiest way to download the products is:

```python
In [1]: myReq.downloadProducts('/my/safe/place')
Out[24]:
{'LightCurve': '/my/safe/place/lc.zip',
 'Spectrum': '/my/safe/place/spec.zip',
 'StandardPos': '/my/safe/place/psf.zip',
 'EnhancedPos': '/my/safe/place/enh.zip',
 'AstromPos': '/my/safe/place/xastrom.zip'}
```

This will download all of the products that you asked to build which were complete last time [you checked](JobStatus.md) (from which it follows that you should check if your products are complete before trying to download them!)

There are several optional parameters you can also pass, to control the download:

| Parameter | Values? | Description | Default |
| :----:    |  :----: | :-----      | :----:  |
| what | 'all', or a list/tuple of products | Which products to download | 'all' |
| stem | Any string | A string to prepend to the names of the downloaded files | None |
| format | 'tar' / 'tar.gz' / '.zip' | The format to download the products in. | 'tar.gz'
| silent | True/False | Whether to suppress reporting progress to the standard output | False |
| clobber | True/False | Whether to overwrite the files if they already exist | False |


So, here are some examples:

```python
In [2]: myReq.downloadProducts('/my/safe/place/' what=('LightCurve',), format='zip') 
...

In [3]: myReq.downloadProducts('/my/safe/place/', clobber=True, stem='my_test_run_')

...
```

**Important note**: If you are requesting only a single product (e.g. a light curve in the first example above), you must ensure that you give a trailing comma inside the parentheses (or use square brackets), or Python will interpret the 
argument as a single string, not a tuple. (My thanks to Greg Sivakoff for identifying this error in my original documentation).

---

## Retrieve the position

For the three possible position types (standard, enhanced and astrometric), instead of downloading the data files, you may 
just wish to get the position. For this we provide three functions:

* `retrieveStandardPos()`
* `retrieveEnhancedPos()`
* `retrieveAstromPos()`

which will attempt to retrieve the position type implied in the function name.

This returns a dictionary object, they keys of which depend on the status of the position. There will always be
a key `GotPos` which is a `bool`, indicating whether or not a position is available.

If `GotPos` is `False` then the only other key will be `Reason` which is a string, giving some information about
why no position was available. 

If `GotPos` is `True` then keys `RA`, `Dec` and `Err90` exist, giving the position (in decimal degrees, J2000) and 90% confidence
radial position error (in arcsec). 

For the standard and astrometric positions there is also the boolean key `FromSXPS` and, if this is `True`,
a key `WhichSXPS`, indicating whether the position was taken from one of the SXPS catalogues, and if so, which one.
When you request a standard or astrometric position, if the input position corresponds to an object in SXPS, and
the dataset requested corresponds exactly with a dataset analysed for the SXPS catalogue, then the position
returned is simply taken from the catalogue, rather than repeating an identical analysis to that carried out for
the catalogue. The most recent SXPS catalogue will also be that used: at the time of writing this is
[2SXPS](https://www.swift.ac.uk/2SXPS); the `WhichSXPS` key is provided to support future releases of the catalogue.

Here are some example position queries:

```python
In [5]: myReq.retrieveStandardPos()
Out[5]:
{'GotPos': True,
 'RA': '335.69850',
 'Dec': '-7.51788',
 'Err90': '3.5',
 'FromSXPS': False}

In [6]: myReq.retrieveEnhancedPos()
Out[6]: {'GotPos': True, 'RA': '335.69928', 'Dec': '-7.51816', 'Err90': '1.7'}

In [7]: myReq.retrieveAstromPos()
Out[7]:
{'GotPos': True,
 'RA': '335.70087',
 'Dec': '-7.51741',
 'Err90': '14.3',
 'FromSXPS': False}
 ```


---

## Retrieve the source list

If you requested source detection, then you can download the source lists directly, using the `retrieveSourceList()` function.
Assuming the source detection has completed with success, this will return a Python dict, with one entry per energy band for which
source detection was requested, i.e. either `Total`, or `Total`, `Soft`, `Medium`, and `Hard`.

Each of these entries is itself a list, with one entry per source. That entry is another dict, giving the properties of the source.
The details of this dict are described in [the source list file documentation](https://www.swift.ac.uk/user_objects/sourceDet_docs.php#positionFiles)

To demonstrate this (for an example where all energy bands were requested)

```python
In [8]: src = myReq.retrieveSourceList()
In [9]: src.keys()
Out[9]: dict_keys(['Total', 'Soft', 'Medium', 'Hard'])
In [10]: for i in src:
    ...:     print(f"{i}: {len(src[i]):d} sources")
    ...:
Total: 25 sources
Soft: 8 sources
Medium: 13 sources
Hard: 10 sources
In [11]: src['Total'][0]
Out[1]:
{'sno': 1,
 'x': 503.9997227258,
 'y': 470.3955699394,
 'ra': 32.1512120191,
 'ra_pos': 2.28992155234127e-07,
 'ra_neg': -2.28992155234127e-07,
 'dec': 56.9457053386,
 'dec_pos': 1.249e-07,
 'dec_neg': -1.249e-07,
 'err90': 3.50000005791013,
 'l': 133.343725932081,
 'b': -4.35794339989909,
 'C': 1236,
```


