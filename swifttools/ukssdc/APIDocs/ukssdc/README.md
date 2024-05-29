# The `swifttools.ukssdc` module.

Quick links: [Usage policy](#usage) | [`xrt_prods`](xrt_prods.md) | [`data`](data.md) | [`query`](query.md) | [ChangeLog](ChangeLog.md) | [Set of Jupyter notebooks](ukssdc.zip)

## Quick start

If you just want to get straight into using this and only read the documentation when you really have to, then I would
recommend you read the summary section below and skim details of the 3 main packages, via the pages in the quick links
above. When you need more detail, or if you prefer to get a good handle before starting, then read through this page and
follow the links through to the section(s) of interest.

I am hoping to add a page of examples as well, soon, to get you started.

## Summary

The `swifttools.ukssdc` module was added in v3.0 of `swifttools` and adds significant new functionality. This includes,
for example, the much-requested ability to query a GRB catalogue to find all bursts meeting your criteria, and then download all
of the XRT light curves for those object.

The module contains three parts:

[`swifttools.ukssdc.data`](data.md)
: Tools to directly access data; for where you know what you are looking for (so not much help for Bono).

[`swifttools.ukssdc.query`](query.md)
: Tools to query various catalogues, in order to determine what it is you're looking for (more helpful for Bono).

[`swifttools.ukssdc.xrt_prods`](xrt_prods.md)
: Tools to build XRT data analysis products. This module was formerly `swifttools.xrt_prods`.

For convenience and consistency, in all documentation and demonstration we import these with short-cut names as follows:

```python
In [1]: import swifttools.ukssdc.data as ud
In [2]: import swifttools.ukssdc.data as uq
In [3]: import swifttools.ukssdc.xrt_prods as ux
```

with extensions to these for sub-packages which we will cover on the relevant pages. The quick links at the top of this page
will take you to the top-level documentation of each of these main packages.

In addition to the above there are some [functions common to the whole module](commonFunc.md) which are usually (but not always) called via the
above modules.

These modules make substantial use of the standard `pandas` package, and particularly the `DataFrame`. Familiarity with these may
be of benefit, but throughout this documentation I will demonstrate the key behaviour as and when needed. I have *not* made `astropy` a
dependency of this module, but if you do have it available then you gain a few extra features (noted inline again) such as the ability
to pass coordinates as `astropy` objects to some functions. If you're likely to use this module interactively, e.g. in Jupyter notebooks,
then installing the `tqdm` module will also make downloading data look prettier.

There are two arguments which are common to almost every function in this module: `silent` and `verbose` (`swifttools.ukssdc.xrt_prods` has only `silent`).
These control how much information is written to the standard output. By default, almost nothing is written except for error
messages. Setting `silent=False` will give some informative output, and `verbose=True` (which implies `silent=False`) will give
lots of output. The demarcation between non-silent, and verbose output is somewhat arbitrary.

## Usage

This Python module is provided free to use, but if you use it for work leading to a publication,
please do acknowledge this with a footnote pointing to (https://www.swift.ac.uk/API). The standard usage
policy for any of the tools accessed via the API remains in force as well. That is, please incude this
in your acknowledgements:


<blockquote>
    This work made use of data supplied by the UK Swift Science Data Centre at the University of Leicester.
</blockquote>

and cite the appropriate paper(s) relating to the data source or algorithms you accessed through the API.
Details for each of these can be found on their relevant pages; below are links to those pages and
the citations requested.


* [GRB light curves](https://www.swift.ac.uk/xrt_curves/docs.php#usage): [Evans et al., (2007)](https://ui.adsabs.harvard.edu/abs/2007A%26A...469..379E/abstract),
[Evans et al., (2009)](https://ui.adsabs.harvard.edu/abs/2009MNRAS.397.1177E/abstract)
* [GRB enhanced positions](https://www.swift.ac.uk/xrt_positions/docs.php#usage): [Goad et al., (2007)](https://ui.adsabs.harvard.edu/abs/2007A%26A...476.1401G/abstract), [Evans et al., (2009)](https://ui.adsabs.harvard.edu/abs/2009MNRAS.397.1177E/abstract)
* [GRB spectra](https://www.swift.ac.uk/xrt_spectra/docs.php#usage): [Evans et al., (2009)](https://ui.adsabs.harvard.edu/abs/2009MNRAS.397.1177E/abstract)
* [The burst analyser](https://www.swift.ac.uk/burst_analyser/docs.php#usage): [Evans et al., (2010)](https://ui.adsabs.harvard.edu/abs/2010A%26A...519A.102E/abstract)
* [On-demand products](https://www.swift.ac.uk/user_objects/docs.php#usage): [Evans et al., (2009)](https://ui.adsabs.harvard.edu/abs/2009MNRAS.397.1177E/abstract): **please see the [documentation](/user_objects/docs.php#usage) for citations for the different products**.
* [2SXPS](https://www.swift.ac.uk/2SXPS/docs.php#access): [Evans et al., (2020)](https://ui.adsabs.harvard.edu/abs/2020ApJS..247...54E/abstract)
* [LSXPS](https://www.swift.ac.uk/LSXPS/docs.php#access): [Evans et al., (2023)](https://ui.adsabs.harvard.edu/abs/2023MNRAS.518..174E/abstract)

## About this documentation

The documentation for this Python module is organised by package and sub-package as given in the contents list below.
Many of the documentation pages can also be downloaded as Jupyter notebooks, so you can actually execute the example code
and experiment with it. Links to the notebooks appear at the top of each page, and a [zip archive of all of them is available](https://www.swift.ac.uk/API/ukssdc/ukssdc.zip).

**Documentation contents:**

* [Common module-level functions](commonFunc.md)
* [Data structures](structures.md)
* [`swifttools.ukssdc.data`](data.md)
  * [The GRB sub-module](data/GRB.md)
  * [The SXPS sub-module](data/SXPS.md)
* [`swifttools.ukssdc.query`](query.md)
  * [The `GRBQuery` class](query/GRB.md)
  * [The `SXPSQuery` class](query/SXPS.md)
* [`swifttools.ukssdc.xrt_prods`](xrt_prods.md)

## Docstrings, PEP8 and so on.

All functions should be fully documented via PEP 257-compliant docstrings, so the `help` command can be used to obtain
full details. If you find something missing or inaccurate, you can [open an issue on our GitHub
page](https://github.com/Swift-SOT/swifttools/issues/new) or just email me (swifthelp@leicester.ac.uk).

While efforts have been made to ensure that the code is PEP8 compliant, eagle-eyed users will notice that
function names in this module are of the form `someFunction()`, rather than the `some_function()` preferred
by PEP8. This is partly simply due to me not reading PEP8 closely enough, but also justified in my entirely objective
and not remotely biased view but the note in PEP8 which says:

> mixedCase is allowed only in contexts where that’s already the prevailing style (e.g. threading.py), to retain backwards compatibility.

And since all my backend code uses mixedCase, this is clearly a totally acceptable decision &#128539;. And anyway, the recommended
convention is really ugly compared to mixedCase&hellip;

More seriously, this issue was only brought to my attention some years after the `xrt_prods` module was first produced, and so
given the choices of breaking everyone's existing scripts, having a mixtured of styles, or just sticking with mixedCase everywhere,
the latter really was a no-brainer.

If you find other operational or pythonic issues apart from this convention, feel free to ping me or (if it impacts usability) to open an issue, as above.
