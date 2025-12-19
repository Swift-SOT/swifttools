# The `swifttools.ukssdc.data` module

[Jupyter notebook version of this page](Data.ipynb)

**Latest version v1.0, released in swifttools v3.0**

## Summary

The `data` module provides direct access to data and services if you know the details of the object you are interested in (if you don't, you probably want the [query module](query.md)).

The basic `swifttools.ukssdc.data` module provides just two functions, described on this page, for accessing Swift's observational data; but there are also two submodules which significantly extend this functionality:

* [`swifttools.ukssdc.data.GRB`](data/GRB.md) - this gives access to GRB data products and related tools (light curve rebinning, timeslicing spectra).
* [`swifttools.ukssdc.data.SXPS`](data/SXPS.md) - this gives access to the data in the SXPS catalogues.

---

## Contents

* [Observation data](#obs)
  * [Downloading by ObsID](#obsid)
  * [Downloading by targetID](#targid)

<a id='dataObs'></a>

## Observation data

There are only two things we can do with the top-level `data` module. We can download observation data by specifying an obsid (or a list of them), or by specifying a targetID, and I will demonstrate these below.

Just to clarify from the off, by 'observation data', I mean the set of data you get on the archive or quick-look site for an observation, like you can see [here](https://www.swift.ac.uk/archive/browsedata.php?oid=00030366099&source=obs).

One thing worth noting before we start: various other classes and functions will call this module behind the scenes. So, for example, when we come to [`ukssdc.data.GRB` module](data/GRB.md) the `getObsData()` function will basically wrap the `downloadObsData()` function demonstrated here, passing on various arguments via `**kwargs`, so even if you don't intend using this module directly, it's helpful to know a bit about it.


To get started, let's import the module, using the shortform convention I use throughout this documentation:


```python
import swifttools.ukssdc.data as ud
```

<a id='obsid'></a>
### Downloading data by obsID

The simplest use of this module is to know the ID of an observation you want, and retrieve the observation data. The function for this is cunningly named `downloadObsData()` and has just one mandatory parameter, the obsid, which should be the first parameter. There are quite a few optional ones which we'll consider in a minute, but to start with I'll just include a couple.


```python
ud.downloadObsData('00282445000',
                   destDir='/tmp/APIDemo_download1',
                   silent=False)
```

    Making directory /tmp/APIDemo_download1
    Downloading 1 datasets
    Making directory /tmp/APIDemo_download1/00282445000
    Making directory /tmp/APIDemo_download1/00282445000/bat/
    Making directory /tmp/APIDemo_download1/00282445000/bat/event/
    Making directory /tmp/APIDemo_download1/00282445000/bat/hk/
    Making directory /tmp/APIDemo_download1/00282445000/bat/masktag/
    Making directory /tmp/APIDemo_download1/00282445000/bat/products/
    Making directory /tmp/APIDemo_download1/00282445000/bat/pulsar/
    Making directory /tmp/APIDemo_download1/00282445000/bat/rate/
    Making directory /tmp/APIDemo_download1/00282445000/bat/survey/
    Making directory /tmp/APIDemo_download1/00282445000/xrt/
    Making directory /tmp/APIDemo_download1/00282445000/xrt/event/
    Making directory /tmp/APIDemo_download1/00282445000/xrt/hk/
    Making directory /tmp/APIDemo_download1/00282445000/uvot/
    Making directory /tmp/APIDemo_download1/00282445000/uvot/event/
    Making directory /tmp/APIDemo_download1/00282445000/uvot/hk/
    Making directory /tmp/APIDemo_download1/00282445000/uvot/image/
    Making directory /tmp/APIDemo_download1/00282445000/uvot/products/
    Making directory /tmp/APIDemo_download1/00282445000/auxil/



    Downloading 00282445000:   0%|          | 0/130 [00:00<?, ?files/s]


If you have the `tqdm` module installed, and `silent=False` you should have had a nice progress bar as that was downloading.
It doesn't render in the exported webpage version of the notebook, sadly.

Let's have a quick look at this call shall we?

The first parameter, the obsid, I gave as a string; it could instead have been an `int`: 282445000; I included the leading zeroes because I prefer them, and if you want to include leading zeroes, you need to use a string or Python gets upset (I think it assumes you are giving a number in octal, or something).

The two named parameters I gave appear in a lot of places, so it's worth getting to know them.

* `destDir` appears in any function that saves things to disk. It specifies the top-level directory in which to save. It is always assigned a default value, relative to the current directory so you don't *need* it, but ask yourself this: who knows better where to save your data, you or me? (I'm flattered, but not, it's not me).
* `silent` is `True` by default and basically supresses all output except important warnings or errors. When running interactively, like in this tutorial, I like to set `silent=False` because I get some feedback on what's happening, but in standalone scripts, you probably want to leave this as `True`.
* `verbose` does not appear above, but is also present in almost every function. This parameter (which defaults to `False`), causes extra output to appear on your console. The idea was the `silent` would turn of all messages, whereas `verbose` would add a load of extra ones. I freely confess that the judgement about what is classed as `verbose` is somewhat arbitrary.



This simple demonstration shows the basic functionality but it's somewhat limited. What if I only wanted the XRT data? Or what if I want to choose where I get it from?


```python
ud.downloadObsData(221755001,
                    instruments=('XRT',),
                    source='us',
                    destDir='/tmp/APIDemo_download2',
                    silent=False
                   )
```

    Making directory /tmp/APIDemo_download2
    Downloading 1 datasets
    Making directory /tmp/APIDemo_download2/00221755001
    Making directory /tmp/APIDemo_download2/00221755001/xrt/
    Making directory /tmp/APIDemo_download2/00221755001/xrt/event/
    Making directory /tmp/APIDemo_download2/00221755001/xrt/hk/
    Making directory /tmp/APIDemo_download2/00221755001/xrt/products/
    Making directory /tmp/APIDemo_download2/00221755001/auxil/



    Downloading 00221755001:   0%|          | 0/27 [00:00<?, ?files/s]


These new arguments should be fairly self-explanatory.

* `instruments` specifies which instruments' data to get. It can be the string 'all' or a list. So, as shown above, when I only want one instrument I still need to supply a list (or tuple) just with a single entry.
* `source` specifies where I want to get the data from. It must be one of ("uk", "us", "italy", "uk_reproc"). The first three entries refer to the archive/quicklook areas supplied by the UK, US or Italy (bet you didn't guess that). The default, "reproc", is the UK-provided site where the XRT data have been locally reprocessed, using a recent (normally the newest) release of HEASoft and the CALDB.

You may be wondering why, given that we only asked for XRT data, the 'auxil' directory was downloaded. The reason is that 'auxil', and indeed 'tdrss' and 'log', are not actually instruments so aren't included in the `instruments` parameter. Instead they are controlled by three parameters: `getAuxil`, `getTDRSS` and `getLog`. By default `getAuxil` is `True` (because you usually need this for any analysis) while the others are `False` (because you don't).

There are also two parameters which I will not demonstrate here, which let you filter specific file type if you want. These can take either a string, or a list/tuples of strings. They are:

* `match`: This should be a file-glob type string (e.g. `*evt*`).
* `reMatch`: This should be a regular expression (e.g. `r'u\w{2}_sky'`).

Note three things regarding these arguments:

1. You can supply `match` OR `reMatch`, not both.
1. If you supply a list of strings then files matching *any* of those in the list will be retrieved.
1. The matching is done only on the actual filename, not the path/directory it is in.


For full information, run `help(ud.downloadObsData)`.

#### Getting multiple observations

The above demonstrates getting a single observation, but you can supply a list, instead of a single argument:


```python
ud.downloadObsData((221755001,282445000),
                    instruments=(),
                    destDir='/tmp/APIDemo_download3',
                    silent=False
                   )
```

    Making directory /tmp/APIDemo_download3
    Downloading 2 datasets
    Making directory /tmp/APIDemo_download3/00221755001
    Making directory /tmp/APIDemo_download3/00221755001/auxil/



    Downloading 00221755001:   0%|          | 0/11 [00:00<?, ?files/s]


    Making directory /tmp/APIDemo_download3/00282445000
    Making directory /tmp/APIDemo_download3/00282445000/auxil/



    Downloading 00282445000:   0%|          | 0/11 [00:00<?, ?files/s]


A a side-effect here, I've pointed out that `instruments` can be an empty list, if for some reason you only want the 'auxil' (or 'log' or 'tdrss') data; here I've done that just to speed up the download for this demo.

If you've been paying careful attention you will have realised that I have used a different `destDir` each time. If I had not done so, I would have generated an error in the second and third downloads, complaining that the destination directory already existed. If I didn't care and wanted to overwrite it I could have added `clobber=True` to the function call.

`clobber` is another parameter that turns up quite a lot, it always defaults to `False`, so that you shouldn't ever be able to overwrite something accidentally.

----
<a id='targid'></a>
### Downloading data by targetID

Sometimes you may know the targetID of the object you care about, and simply want to get all of the data for that target. You have probably already guessed how we are going to do this:



```python
ud.downloadObsDataByTarget(282445,
                           instruments=(),
                           destDir='/tmp/APIDemo_download4',
                           silent=False)
```

    Making directory /tmp/APIDemo_download4
    Downloading 4 datasets
    Making directory /tmp/APIDemo_download4/00282445000
    Making directory /tmp/APIDemo_download4/00282445000/auxil/



    Downloading 00282445000:   0%|          | 0/11 [00:00<?, ?files/s]


    Making directory /tmp/APIDemo_download4/00282445001
    Making directory /tmp/APIDemo_download4/00282445001/auxil/



    Downloading 00282445001:   0%|          | 0/11 [00:00<?, ?files/s]


    Making directory /tmp/APIDemo_download4/00282445002
    Making directory /tmp/APIDemo_download4/00282445002/auxil/



    Downloading 00282445002:   0%|          | 0/11 [00:00<?, ?files/s]


    Making directory /tmp/APIDemo_download4/00282445003
    Making directory /tmp/APIDemo_download4/00282445003/auxil/



    Downloading 00282445003:   0%|          | 0/11 [00:00<?, ?files/s]


The arguments here are identical to those for `downloadObsData()`, except that we start off with a targetID (or a list of them), not an obsID. In fact, the other arguments for this function are just `**kwargs` to pass to `downloadObsData`, so are literally identical.

As with obsData, we can provide an int (as above) or string (e.g. '00282445') and we can also request multiple targets:


```python
ud.downloadObsDataByTarget((282445,20014),
                           instruments=(),
                           destDir='/tmp/APIDemo_download5',
                           silent=False)
```

    Making directory /tmp/APIDemo_download5
    Downloading 4 datasets
    Making directory /tmp/APIDemo_download5/00282445000
    Making directory /tmp/APIDemo_download5/00282445000/auxil/



    Downloading 00282445000:   0%|          | 0/11 [00:00<?, ?files/s]


    Making directory /tmp/APIDemo_download5/00282445001
    Making directory /tmp/APIDemo_download5/00282445001/auxil/



    Downloading 00282445001:   0%|          | 0/11 [00:00<?, ?files/s]


    Making directory /tmp/APIDemo_download5/00282445002
    Making directory /tmp/APIDemo_download5/00282445002/auxil/



    Downloading 00282445002:   0%|          | 0/11 [00:00<?, ?files/s]


    Making directory /tmp/APIDemo_download5/00282445003
    Making directory /tmp/APIDemo_download5/00282445003/auxil/



    Downloading 00282445003:   0%|          | 0/11 [00:00<?, ?files/s]


    Downloading 3 datasets
    Making directory /tmp/APIDemo_download5/00020014001
    Making directory /tmp/APIDemo_download5/00020014001/auxil/



    Downloading 00020014001:   0%|          | 0/10 [00:00<?, ?files/s]


    Making directory /tmp/APIDemo_download5/00020014002
    Making directory /tmp/APIDemo_download5/00020014002/auxil/



    Downloading 00020014002:   0%|          | 0/10 [00:00<?, ?files/s]


    Making directory /tmp/APIDemo_download5/00020014003
    Making directory /tmp/APIDemo_download5/00020014003/auxil/



    Downloading 00020014003:   0%|          | 0/10 [00:00<?, ?files/s]


And that's it for the `data` module. Don't forget to do an `rm -fr /tmp/APIDemo_*` at some point...
