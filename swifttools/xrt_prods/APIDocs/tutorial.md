# XRT Product Generator API Tutorial

This tutorial gives a simple example of how to use the API via the `curl` command line tool. It should be relatively simple to adapt the examples in here to create the products you need, but of course you will need to read the [full job-submission API description](RequestJob.md) to know what the different parameters are.

In this tutorial we will do the following:

* [Request all possible products be constructed for GRB 200416A.](#request-the-products)
* [Cancel the creation of the spectrum.](#cancel-the-spectrum)
* [Poll the status until all products are completed.](#get-the-job-status)
* [Download all of the products.](#retrieve-the-products)

This example assumes you are doing everything interactively from the command line. Of course, if you are going to work interactively, you would be much better served using [the website](https://www.swift.ac.uk/user_objects) and so the likelihood is that, after doing some command-line testing, you will be writing scripts to use the API, and particularly to parse the returned JSON. At the current time we do not provide any examples of how you may wish the script this up, although we are working on a Python module which will be able to construct, send and process queries for you, in a slightly more friendly way than using the API &lsquo;raw&rsquo; as in this example.

## Preparation

First, check that you have the `curl` utility installed, and if not, install it (instructions will vary from platform to platform and are not supplied here. It tends to be a standard part of linux, and for Mac is certainly available via macports).

Next, you need to register to use the API, so go to [the registration page](https://www.swift.ac.uk/user_objects/register.php), fill out the form, and then click the link in the email you get sent to confirm your address is real, and yours.

Now we're ready to start. 

## General notes

The API works by the sending and receiving of JSON. Although you can enter the JSON directly on the command line, I find it much easier to save it in a text file: this way you have the file for posterity, and also if you make a mistake it's easy to edit and resubmit the command.

JSON doesn't care about whitespace, so in the examples below I've formatted the JSON to be human readable - the JSON returned by the UKSSDC servers is not formatted with humans in mind so your files will look slightly different from mine unless you reformat them youself.

JSON does not support comments, so there is no explanation inline in any of the examples. I have given a few explanatory notes below the examples, but in general you should read the main documentation to understand the details of what is shown.

### Book keeping

I'm expecting that if you're using the API it's because you're expecting to build products fairly often, or at least, build several of them. In this case book keeping is really important; the last thing you want is to end up with a whole load of `all.tar.gz` files on your computer with no idea which one corresponds to which job. How you go about book keeping is up to you, but the API service does try to help you a bit: each job has a unique jobID, and when you first request the job, you will get back a full list of all of the parameters (including any that you didn't specify but which have default values).

How you go about keeping track of your jobs is entirely up to you, but I'd strongly advise you to make sure you save the JSON returned by every query to the server in a file. If all of the files have the same stem to their name (e.g. `GRB200416A_allProds_2020May03`) or are in the same directory, this will obviously make life easier for you when, 10 months down the line, your paper gets its referee's report and you need to remember exactly what light curve binning you had used.

In the example below, I'm assuming you started by creating a directory and are working in that but of course, it's entirely up to you.

---

## Request the products

The first thing to do is to request a job. So, create a file called `requestJob.json` and populate it with the following JSON. If you are actually going to submit this, don't forget to correct the `UserID` field!

```JSON
{
  "UserID":      "YOUR_EMAIL_ADDRESS",  
  "name":        "GRB 200416A", 
  "targ":        "00966554",  
  "RA":          335.6985,  
  "Dec":         -7.5179,  
  "cent":        1,
  "centMeth":    "simple",   
  "poserr":      1,   

  "lc":          1,
  "binMeth":     "counts",
  "wtcounts":    30,
  "pccounts":    20,
  "dynamic":     1,
  "ratefact":    10,
  "binfact":     1.5,

  "spec":        1,
  "specz":       0,
  "specobs":     "all",
  "timeslice":   "obsid",

  "posobs":      "all",
  
  "doenh":       1,
  
  "dopsf":       1,
  
  "doxastrom":   1,
  
  "image":       1,
  "imen":        "0.3-10,1-4",
  "imobs":    "all"
}
```

To keep this simple, I've left out a lot of fields that have default values. I've also supplied some blank lines to separate out the different sections of the request for ease of reading. In the top section the object is identified, along with the request that we carry out a simple centroid to ensure we have a good position in the XRT coordinate frame.

In the second section I've requested a light curve with the &lsquo;counts&rsquo; binning approach; the values then entered reflect how the [automated GRB light curves](https://www.swift.ac.uk/xrt_curves) are built.

For a spectrum I've requested that all observations be used, stated that there is no redshift, and requested one spectrum be created for every observation of this GRB.

For the position I've requested again that all observations be used, and then accepted the defaults for everything else.

For the image, I have requested all observations be used, and I've specified that I want two images, a 0.3-10 keV image and a 1-4 keV image. Because why not?

OK, we can submit this now, so let's enter this command

```console
> curl --data @requestJob.json --request POST https://www.swift.ac.uk/user_objects/run_userobject.php -o ret_request.json
```

As soon as this command finishes we'll have a look at `ret_request.json` to see what the server returned. I've truncated the output below, because I'm not including the `jobPars` entry. That lists the full set of parameters assigned automatically by the processing, including default values for those we didn't supply. This can be helpful but not for this tutorial. So, my version of `ret_request.json`, reformatted and with `jobPars` removed, looks like this:


```JSON
{
  "OK": 1,
  "URL": "https://www.swift.ac.uk/user_objects/tprods/USERPROD_803",
  "JobID": "803",
  "APIVersion": 0.1,
      "jobPars": {
        //Redacted
      }
    }
```

Great. The `OK` field was set to `1`  so the job has been submitted. If you want proof that everything's working OK, you can open the URL in your web browser, but that's cheating so we will resist the temptation! What we really care about is the `JobID`, because we will need this to do anything else with the job via the API. You should also keep it for bookkeeping (this is partly why the `jobPars` object is returned to you): it's a unique identifier of this job. 

---

## Cancel the spectrum

You know what, I don't want a spectrum after all. I mean, it's a GRB so it's just a power-law with a photon index around 2, right? Let's cancel part of the job. 

So, first we need to create a file for our request, I'll call this `cancelSpectrum.json` because I'm incredibly original. This needs to contain:

```JSON
{
  "UserID": "YOUR_EMAIL_ADDRESS",
  "JobID":  464,
  "what": "spec"
}
```

Of course, if you're doing this you need to correct the `UserID` field **and also the JobID!** Don't worry, you can't kill my job because a) it finished before and published these documents, and b) you can only cancel your own job.

Right, let's send this job off:


```console
> curl --data @cancelSpectrum.json --request POST https://www.swift.ac.uk/user_objects/canceljob.php -o ret_cancel.json
```

And let's have a look at `ret_cancel.json`:

```JSON
{
  "JobID": 803,
  "OK": 1,
  "APIVersion": 0.1,
  "status": {
    "spec": "Job cancelled OK"
  },
  "statusCodes": {
    "spec": 0
  }
}
```

OK, good, the spectrum's gone. You could go to the web page and confirm that, but why would you? You trust me, right? No? Oh well, fortunately the next step is to poll the server for the job status, so let's do that instead.

---

## Get the job status

Of course you believe me that you've safely cancelled the spectrum, but what about the other products, have they finished yet? Let's find out. We'll create another request file, and I'm going to call mine, `getJobStatus.json`. Bet you didn't see that coming. Here're its contents:

```JSON
{
  "UserID": "YOUR_EMAIL_ADDRESS",
  "JobID": 464,
  "what": "lc,spec,enh,psf,xastrom,image"
}
```

Remember to correct the `UserID` and `JobID` fields. You won't be able to get the status of someone else's job, so I wouldn't waste time trying if I were you. Note that I've included the spectrum in the list of products to poll. I don't need to do this, since I cancelled it, but it won't hurt and you get to see what happens when you ask about a job you've cancelled. I haven't included the optional `whatProg` field to get the full details of how far through its processing each product is because the [returned data in this case are a bit more involved](JobStatus.md), and really you want your script to be reading that and presenting it to you a bit more nicely, we don't want that information when we're playing on the command line.

Right, let's fire this request off:

```console
> curl --data @getJobStatus.json --request POST https://www.swift.ac.uk/user_objects/checkProductStatus.php -o ret_query.json
```

And let's take a look at the `ret_query.json`:

```JSON
{
  "lc": {
    "statusCode": 3,
    "statusText": "Running",
    "progress": {
      "GotProgress": 0
    }
  },
  "spec": {
    "statusCode": -4,
    "statusText": "Cancelled at your request",
    "progress": {
      "GotProgress": 0
    }
  },
  "enh": {
    "statusCode": 3,
    "statusText": "Running",
    "progress": {
      "GotProgress": 0
    }
  },
  "psf": {
    "statusCode": 3,
    "statusText": "Running",
    "progress": {
      "GotProgress": 0
    }
  },
  "xastrom": {
    "statusCode": 3,
    "statusText": "Running",
    "progress": {
      "GotProgress": 0
    }
  },
  "image": {
    "statusCode": 3,
    "statusText": "Running",
    "progress": {
      "GotProgress": 0
    }
  },
  "OK": 1,
  "JobID": 803,
  "APIVersion": 0.1
}
```

OK, good, the spectrum was cancelled. Told you. The other jobs have all started, but they're not done yet, so we have to wait. Generally I can't tell you how long the job will take because it depends on many factors (if you'd got the detailed progress information you could take a ~~wild~~ ~~informed~~ semi-informed guess), so you just have to poll the server periodically; that is, reissue that curl command and check the output. **Please** don't do this too often: do you really need to check it more than once a minute? Really? 

This particular job I know from experience takes around 5 minutes, so go and put the kettle on, and when you're freshly supplied with caffeine poll the server again. We're looking for an output where all of the jobs have a `statusCode` of 4 (`statusText`: `complete`), or a negative number indicating a failure. In this case we expect the spectrum to have a negative number, because we cancelled it, but everything else should complete OK. So, when everything's done the above `curl` command should return something like this:

```JSON
{
  "lc": {
    "statusCode": 4,
    "statusText": "Complete",
    "progress": {
      "GotProgress": 0
    }
  },
  "spec": {
    "statusCode": -4,
    "statusText": "Cancelled at your request",
    "progress": {
      "GotProgress": 0
    }
  },
  "enh": {
    "statusCode": 4,
    "statusText": "Complete",
    "progress": {
      "GotProgress": 0
    }
  },
  "psf": {
    "statusCode": 4,
    "statusText": "Complete",
    "progress": {
      "GotProgress": 0
    }
  },
  "xastrom": {
    "statusCode": 4,
    "statusText": "Complete",
    "progress": {
      "GotProgress": 0
    }
  },
  "image": {
    "statusCode": 4,
    "statusText": "Complete",
    "progress": {
      "GotProgress": 0
    }
  },
  "OK": 1,
  "JobID": 803,
  "APIVersion": 0.1
}
```

---

## Retrieve the products

Great, it's all finished! Now let's get our hands on the data. For this we need to know where they are, and as ~~luck~~ sensible design would have it, when you first requested the job all those minutes ago, the server returned the relevant URL to us. You may not have paid much attention to that at the time, but that's partly why I suggested you capture the JSON returned by the server into a file. Let's have a quick look at that file again (I called in `ret_request.json`) and find the `URL` field. Got it? Mine is: `https://www.swift.ac.uk/xrt_products/tprods/USERPROD_803`, your will look similar. (Quick aside here, you should spot the obvious link between URL and JobID. While I have no current plans to break this relationship *it is not guaranteed to remain forever*, this is why the URL is given to you explicitly when you request a job. So make sure you rely on the `URL` field, not engineering it yourself from the Job ID).

Getting the products is really easy. I just want to download everything, and I'll get it as a gzipped tar file:

```console
> curl https://www.swift.ac.uk/user_objects/tprods/USERPROD_803/all.tar.gz -o allProds.tar.gz
```


I chose this format purely for personal preference, due to the wonders of muscle memory my fingers automatically type the correct command (due to the problems of muscle memory, my fingers will try to type this for other file formats too, which doesn't work so well):

```console
> tar -xzvf allProds.tar.gz
```

This creates a directory `USERPROD_803` with all of the products in their own subdirectories. There's even a `spec` directory (since we did originally request a spectrum) but it's not very interesting.

We deliberately keep that top-level `USERPROD_` directory in the file you're returned, since I personally hate it when I extract downloaded files and it pollutes my current working directory. Of course, when you've extracted the files you can move them around as you like.

One final thing to note: although the astrometric position ended up with a `statusCode` of 4, i.e. the job completed OK, no position was found. The status code is correct here: the process ran with no errors, it just turns out that, for this object, there are too few XRT sources for us to create an astrometric position. If you look in the `xastrom/` directory you will see a file `NOCORR` (and no `corrpos.dat` file) informing you of this; for more, see [the details about the retrieved products](RetrieveProducts.md).


And that's it. Have fun, but please do respect our servers as well. We have recently increased our capacity significantly but it's not unlimited, and we don't want any individual user to monopolise it. If you want to submit many jobs then please, do them a few at a time (it doesn't take much to set up your script to submit the next job after the current one has completed). And if you have problems, drop us a line on swifthelp@leicester.ac.uk.
