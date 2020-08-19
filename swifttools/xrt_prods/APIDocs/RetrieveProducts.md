# How to retrieve the completed products

Once your [products are complete](JobStatus.md) you will, one assumes, wish to access them. There are two things you can retrieve:

* [The data files.](#download-the-data)
* [The positions](#retrieve-the-position)

# Download the data

To recover your data you will need the `URL` entry from the [JSON object returned when you submitted the job](ReturnData.md). This
points you to the top-level directory for dowbload. This is the one function for which we do not provide any specific API routine, since you can directly download the files and any attempt to use JSON as an intermediary would add unnecessary complication.

The files are available in `tar`, `tar.gz` or `zip` format, and can be accessed via the generic URL:

```
$URL/$what.$format
```

* `$URL` is the top-level URL described above, i.e. the value returned to you when you submitted your job.
* `$what` is the product you want to download, and can be any of:
  * `lc` - to get the light curve files
  * `spec` - to get the spectrum files
  * `psf` - to get the standard position files
  * `enh` - to get the enhanced position files
  * `xastrom` - to get the astrometric position files
  * `image` - to get the image files
  * `all` - to get files for all created products
* `format` is one of  `tar`, `tar.gz` or `zip`

So a simple example download command may be


```console
> curl https://www.swift.ac.uk/user_objects/tprods/USERPROD_1/all.tar -o myJob1.tar
```

This will download all products from the job with `JobID` 1, as a `tar` file, and save them to the file `myJob1.tar`

For various reasons, our servers do not support directory listings and hence recursive downloads, i.e. you cannot simply call `wget -r $URL` to get the full set of data products. 

-----

## Downloaded files

The files you download are essentially all created files; this includes logs and some files used to enable the [status tracking](JobStatus.md). Below we identify the primary files of interest for each product.

### Light curves

The main light curve file is `curve.qdp`, which contains all of the light curve data in a single file. Also potentially of interest are the `PCCURVE.qdp` and `PCUL.qdp` files (and `WTCURVE.pl` and `WTUL.qdp`) which contain a detailed breakdown each each data point and upper limit in each mode.

For more details about the light curve files see [the light curve documentation](https://www.swift.ac.uk/user_objects/lc_docs.php#format)


-----

## Spectra

For the spectra the downloaded file will consist of one or more gzipped `tar` files, one per spectral timeslice created. If you specified timeslices manaully, these will be named according to your labels (with non-alphanumeric characters stripped out). For per-snapshot or per-obsid spectra the names will reflect the snapshot or obsid; for a single spectrum it will be called &lsquo;interval0&rsquo;.

The contents of these files are described in [the spectrum documentation](https://www.swift.ac.uk/user_objects/spec_docs.php).

Additionally there will be a directory `scripts/` containing a couple of quick `xspec` scripts to set up the environment, which may be of use.


-----

## Standard position

The standard position can be obtained in two ways. If the observation(s) you requested corresponds exactly to an entry in the [2SXPS catalogue](https://www.swift.ac.uk/2SXPS) then the position will simply be taken from that entry rather than duplicate the processing. Otherwise, the position will be determined specifically for you.

In the former case, the file of interest is `INSXPS`. In the latter case, it is `results.dat` that you will need.

### **Positions from 2SXPS**

If the position was taken from the SXPS catalogue then the only file of interest is `INSXPS`. This file contains one field per line, as follows:

1. The source identifier in the SXPS catalogue (i.e. the `2SXPS_ID` value)
1. RA (J2000, decimal degrees)
1. Declination (J2000, decimal degrees)
1. Radial position error (90% confidence, arcseconds, including systematics)
1. RA (J2000, sexagsesimal hours / minutes / seconds)
1. Declination (J2000, sexagsesimal degrees / minutes / seconds)
1. The identifier of the SXPS data set from which the position was taken (i.e. the `obsid` value).
1. The SXPS catalogue the position was taken from. At the time of writing this will be 2SXPS, but with future SXPS releases this may be updated.


### **Newly-determined positions**

If your position was calculated afresh for you then the details of the position are in `results.dat`. If no position could be found, it contains `NOPOS`, otherwise this file contains all the results on a single line, with the following fields, separated by tabs.

1. RA (J2000, decimal degrees)
1. Declination (J2000, decimal degrees)
1. RA (J2000, sexagsesimal hours / minutes / seconds)
1. Declination (J2000, sexagsesimal degrees / minutes / seconds)
1. Radial position error (90% confidence, arcseconds, including systematics)
1. Whether the source was fitted as piled up. (0=no, 1=yes)
1. Which of the identified sources was identified as corresponding to the one you requested (by number)
1. The last 4 fields give the S/l/c/&tau; values fitted to account for pile up, if necessary. For an explanation of these, please see [Evans et al., 2020](https://ui.adsabs.harvard.edu/abs/2019arXiv191111710E/abstract).

There are a few other files that may be of interest: `summed.gif` is a GIF image of all of the data used to determine the position. If you requested to centroid only, or to detect in a single pass, then there will be files `centroid.img.gz` and `centroid_ex.img.gz` which are the FITS image and exposure map on which the detect/centroid was carried out. If you requested the iterative detect and centroid process then instead there will be a subdirectory `centroid/` which will contain the summed image and exposure map that was used by the centroiding.



-----

## Enhanced position

If an enhanced position was successfully created then the file `success.txt` will contain a summary of the result. This contains one field per line, as follows:

1. The object name (from your input)
1. The targetID(s) used to find the position
1. The number of XRT-UVOT overlaps used for the final position
1. The total exposure time in these overlaps
1. The number of overlaps that were not included, as they yielded positions too far from the weighted mean position, so were likely outliers.
1. The total time in overlaps that were not included in the final position (for any reason, not just being outliers)
1. RA (J2000, decimal degrees)
1. Declination (J2000, decimal degrees)
1. RA (J2000, sexagsesimal hours / minutes / seconds)
1. Declination (J2000, sexagsesimal degrees / minutes / seconds)
1. Radial position error (90% confidence, arcseconds, including systematics)

This directory also contains a few GIF and postscript format images of the UVOT field with the final XRT position and the outliers etc marked on it, as show on the results web pages. 

-----

## Astrometric position

The contents of the `xastrom/` directory are very similar to that of the [standard position](#standard-position). As with that position, if the observation(s) you requested corresponds exactly to an entry in the [2SXPS catalogue](https://www.swift.ac.uk/2SXPS) then the position will simply be taken from that entry rather than duplicate the processing. Otherwise, the position will be determined specifically for you.

In the former case, the file of interest  is `INSXPS`. In the latter case, it is `corrpos.dat` that you will need, although `xastrom_corr.dat` will also be of interest.

### **Positions from 2SXPS**

If the position was taken from the SXPS catalogue then the only file of interest is `INSXPS`. This file contains one field per line, as follows:

1. The source identifier in the SXPS catalogue (i.e. the `2SXPS_ID` value)
1. RA (J2000, decimal degrees)
1. Declination (J2000, decimal degrees)
1. Radial position error (90% confidence, arcseconds, including systematics)
1. RA (J2000, sexagsesimal hours / minutes / seconds)
1. Declination (J2000, sexagsesimal degrees / minutes / seconds)
1. The identifier of the SXPS data set from which the position was taken (i.e. the `obsid` value).
1. The SXPS catalogue the position was taken from. At the time of writing this will be 2SXPS, but with future SXPS releases this may be updated.


### **Newly-determined positions**

If your position was calculated afresh for you then the details of the position are in `corrpos.dat`. If no position was found then this file will not exist, although a file `NOCORR` will be present.

If a position was found this file contains all the results on a single line, with the following fields, separated by tabs.

1. RA (J2000, decimal degrees)
1. Declination (J2000, decimal degrees)
1. RA (J2000, sexagsesimal hours / minutes / seconds)
1. Declination (J2000, sexagsesimal degrees / minutes / seconds)
1. Radial position error (90% confidence, arcseconds, including systematics)

The details of the astrometric correction are held in `xastrom_corr.dat`. This is again a single-line file with the following fields separated by tabs:

1. The RA correction applied, in arcseconds
1. The declination correction applied, in arcseconds
1. The roll angle correction applies, in arcminutes
1. The 90% uncertainty on this correction, in arcseconds

There may be other files of interest in this directory, depending on the way in which the position was created. There will always be two images: `orig.gif` and `corrected.gif`. These show the XRT field of view, with XRT sources marked a green circles and 2MASS objects as cyan squares. `orig.gif` shows these aligned using the original astrometry from the XRT star trackers; `corrected.gif` uses the final astrometry used to create the final position.

If the astrometric position was created with the same observation as the [standard position](#standard-position) and the standard position used the iterative centroid approach, then there will be no other important files in this directory; if not then there will be a `centroid` directory which contains some of the files, images and outputs used in the source detection process.


## Image

In the `image/` directory you should first examine the `images.log` file. This will contain one line for each image created, and each line has 3 fields (separated by tabs):

1. The image number
1. The minimum energy of events in this image (keV)
1. The maximum energy of events in this image (keV)

For each entry in here there will be the files `image$n.img.gz` and `image$n.gif`. These are FITS and GIF-format images respectively for image `$n`, where `$n` is the image number from the entry in `images.log`. i.e. if the first line of that file is `1      0.3      10` then `image1.img.gz` is a 0.3-10 keV FITS image.

There will also be files `summed_ex.img.gz` and `summed_vignet_ex.img.gz` (with `.gif` equivalents). These are the exposure maps corresponding to your images; the former does not include vignetting, the latter does.

---

## Retrieve the position

For positions (standard, enhanced or astrometric) we provide a slightly more convenient interface which will simply return the position
(if available) in a JSON obect.

For this we need to supply a UserID and JobID, so we can create a file: `getpos.json`:

```JSON
{
  "UserID": "YOUR_EMAIL_ADDRESS",
  "JobID": 3510
}
```

We send this to 

* `https://www.swift.ac.uk/user_objects/tprods/getPSFPos.php`
* `https://www.swift.ac.uk/user_objects/tprods/getEnhPos.php`
* `https://www.swift.ac.uk/user_objects/tprods/getXastromPos.php`

As always, the returned object will contain the keys `APIVersion` and `OK`. If `OK`==0 then it will also contain the key `ERROR` explaining the problem.
If `OK==1` then the following keys will be returned:

GotPos
:A boolean (1 or 0) indicating whether or not the position was determined.

If GotPos == 1 then the following will also be included in the JSON object:

RA
:The RA (J2000) in decimal degrees
Dec
:The declination (J2000) in decimal degrees
Err90
:The 90% confidence radial position error in arcseconds.

For the PSF and astrometric positions there is also the key `FromSXPS` which is a boolean (0 or 1), indicating whether the position
was taken from the SXPS catalogue. If this is true (1) then the key `WhichSXPS` tells you which catalogue it was taken from.
When you request a standard or astrometric position, if the input position corresponds to an object in SXPS, and
the dataset requested corresponds exactly with a dataset analysed for the SXPS catalogue, then the position
returned is simply taken from the catalogue, rather than repeating an identical analysis to that carried out for
the catalogue. The most recent SXPS catalogue will also be that used: at the time of writing this is
[2SXPS](https://www.swift.ac.uk/2SXPS); the `WhichSXPS` key is provided to support future releases of the catalogue.

