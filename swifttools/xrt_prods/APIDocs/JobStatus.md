# How to query the status of your job.

After requesting products be built, you will need to check their status as (obviously) you cannot [download the final products](RetrieveProducts.md) until they are complete.

One way to view the status is  simply to visit the web page (identified by the `URL` entry in the [data returned when you requested the products](ReturnData.md), where the products' statuses will be shown, along with (optionally) progress reports indicating how far through the creation process each product is. Alternatively, you can retrieve this information via the API, as described here.

Of course, polling the status is usually not a one-off process, instead you will need to poll periodically until your jobs are complete. **Please be considerate in how often you poll** as such requests are not &lsquo;free&rsquo; in terms of their resource usage. There should normally be no need to poll more frequently than every 10 s or so, and for most uses of the API we would expect a longer interval would be perfectly adequate.

As for all interactions with the API, you send your request as an `HTTP POST` request with the data in `JSON` format. The URL to send the request to is https://www.swift.ac.uk/user_objects/checkProductStatus.php. Below we describe [the JSON you should send](#format-of-the-json-request) and [the returned JSON data](#format-of-the-json-response), and provide [some examples](#examples).
Due to the complexity of this returned object, we have also given [an example parser](#example-parsing-code) illustrating how this can be parsed.


-----

## Format of the JSON request

The JSON data submitted must contain three mandatory keys, and one optional key. These are:

<dl title='Keys needed to request a job process a job'>
  <dt style='font-weight: bold;'>JobID</dt>
  <dd>The ID number of the job you are querying.</dd>
  <dt style='font-weight: bold;'>UserID</dt>
  <dd>Your user ID (i.e. registered email address). <strong>This must match the userID used to request the job you are now querying.</strong></dd>
  <dt style='font-weight: bold;'>what</dt>
  <dd>The product(s) to obtain the status of. If there are more than one this should be a comma-separated list.</dd>
  <dt style='font-weight: bold;'>whatProg (optional)</dt>
  <dd>The product(s) for which you would like to retrieve the progress report, as well as the basic status. This should be the same as, or a subset of, the products given in the <code>what</code> entry. For multiple products, use a comma-separated list.</dd>
</dl>

The `what` keyword can contain any of the requestable products, using their short forms i.e.:

* lc
* spec
* enh
* psf
* xastrom
* image

If you have requested multiple products within the same job, we advise sending a single status request for all of them (i.e. the `what` keyword should contain a comma-separated list), and then parsing the output for each parameter; this should be more efficient then polling each product separately.



-----

## Format of the JSON response

When you request the job status you will receive a JSON object. The structure of this is more complicated than the other JSON objects this API produces, with significant substructure. For ease of reading, we give a very simplified summary, and then each level of structure is presented separately below. To help with navigation, before each description after the first follows an example of where within the JSON tree this structure resides. This assumes that the JSON has been parsed into an array called `returnedJSON`, and refers to the results for the light curve (analogues exist for all of the other products). 

 We advise you to have a look at the [examples](#examples), as these demonstrate the layout more clearly than can be achieved by a full description of the possible contents

### Summary

The overall structure of the JSON object (where no error occurs) is as shown here:


```JSON
{
  "JobID": "JobID",
  "OK": "isOK",
  "lc": {
    "statusCode": "code",
    "statusText": "text",
    "progress": {
      "TimeRunning": "time",
      "GotProgress": "code",
      // Some products may have a "PreProgress" key here. 
      "ProgressSteps": [
        {
          "StepLabel": "step1label",
          "StepStatus": "step1status",
          "StepExtra": "step1text",
          "SubStep": [
            {
              "StepLabel": "step1alabel",
              "StepStatus": "step1astatus",
              "StepExtra": "step1atext"
              // Can have another "SubStep" entry with another layer of steps
            },
            {
              "StepLabel": "step1blabel",
              "StepStatus": "step1bstatus",
              "StepExtra": "step1btext"
              // Can have another "SubStep" entry with another layer of steps
            }
            // &c for more steps
          ]
        },
        {
          "StepLabel": "step2label",
          "StepStatus": "step2status",
          "StepExtra": "step2text"
          // Can have a "SubStep" entry too
        }
        // &c for more steps
      ]
    }

  }
  // &c for spec, enh etc.
}
```

---


### **High level structure**

The top-level of the returned JSON is actually very simple:

<dl title='Contents of the returned JSON'>
  <dt style='font-weight: bold;'>JobID</dt>
    <dd>The ID of the job you queried (provided for ease of bookkeeping).</dd>
  <dt style='font-weight: bold;'>OK</dt>
    <dd>Whether the job was processed successfully. 1 = yes, 0 = no.</dd>
  <dt style='font-weight: bold;'>ERROR</dt>
    <dd>Only present if <code>OK</code>=0; this gives a textual description of the problem.</dd>  
  <dt style='font-weight: bold;'><em>Prod</em>*</dt>
    <dd>The status information for the product <em>Prod</em>; this is itself a structure described next.</dd>
</dl>

&#42; The &lsquo;Prod&rsquo; entry above is a placeholder; no entry with key &lsquo;Prod&rsquo; will exist in the JSON object. Instead there will be an entry for each product you queried (in the &lsquo;what&rsquo; field of your request), i.e. there will be entries on the JSON with keys, &lsquo;lc&rsquo;, &lsquo;spec&rsquo; etc.

---

### **Per-product structure**

Each of the &lsquo;Prod&rsquo; entries above will be a sub-object with the structure described here. For a light curve, this structure exists as `returnedJSON[lc]`.

<dl title='Contents of the individual product status values'>
  <dt style='font-weight: bold;'>statusCode</dt>
    <dd>A code indicating the status of the product. These are described below.</dd>
  <dt style='font-weight: bold;'>statusText</dt>
    <dd>A textual description of the status</dd>
  <dt style='font-weight: bold;'>progress</dt>
    <dd>This is itself a structure, described below, which lists the steps involved in the creation of the product and indicates 
    where in that process the execution has currently reached.</dd>
</dl>

The status codes can have any of the following values. You will see that a negative number indicates that the product will not be produced.

 * -4 = The job was cancelled by the user.
 * -3 = The product could not be built, the job was called OK, but did not produce a product.
 * -2 = An internal error occurred at our end, and the attempt to add the job to the queue failed.
 * -1 = An internal error occured at our end, and the job could not even be requested.
 * 1  = Job has been requested, but not yet queued.
 * 2  = Job has been entered into our processing queue.
 * 3  = The job is actually running (progress information may be available)
 * 4  = The job completed OK. Your products are available
 * 5  = [Extra status code only for astrometric positions]: the astrometry is waiting for the standard PSF position to be produced, and will then correct that.
 

Codes -2 and -3 should never exist, and most likely indicate either a transient fault with one of our servers or services, or that one of the executable scripts has become corrupted. **If you get one of these errors please email us immediately on swifthelp@leicester.ac.uk**. It is probable that we already know of the issue, but not certain, so a prompt report of the error will enable us to fix it.


---

### **Progress structure**

If the progress of any products was requested (via the &lsquo;whatProg&rsquo; field of your request), that progress is contained within another sub-object, described here. For a light curve, this structure exists as `returnedJSON[lc][progress]`.

<dl title='Contents of the individual product progress reports'>
  <dt style='font-weight: bold;'>TimeRunning</dt>
    <dd>How long it is since the product build began running, in HH:MM:SS format. NB, this is not the time since you requested the job, as it may have sat in the job queue for some time, depending on how busy our servers were. This reflects the time since the job was actually executed by the scheduler.</dd>
  <dt style='font-weight: bold;'>GotProgress</dt>
    <dd>A numerical value indicating whether the job progress was returned. 0 = the progress of this product was not requested. 1 = progress returned OK. 2 = progress information unavailable.</dd>
  <dt style='font-weight: bold;'>PreProgress (optional)</dt>
    <dd>If present may indicate some text that describes the steps, but is not one of them.</dd>
  <dt style='font-weight: bold;'>ProgressSteps</dt>
    <dd>This is another structure (the last one&hellip; sort of) described below, which details the steps involved in creating the product.</dd>
</dl>

---

### **Progress Steps structure**

This is the final level of the JSON object, although it has a recursive structure so extra depth can be obtained sometimes. This structure is actually a list/array (with no keys), each entry of which is a JSON structure describing one of the waymarker steps involved in creating your product, and indicating whether this step has been reached or not. The `ProgressSteps` object itself, for a light curve, would exist as `returnedJSON[lc][progress][ProgressSteps]`, but as this is simply a list, the actual structure below describes the entries: `returnedJSON[lc][progress][ProgressSteps][n]`.

<dl title='Contents of the individual product progress steps'>
  <dt style='font-weight: bold;'>StepLabel</dt>
    <dd>A textual description of this step.</dd>
  <dt style='font-weight: bold;'>StepStatus</dt>
    <dd>A numerical value indicating whether this step has been reached. 0 = not yet reached, 1 = this is the active step, 2 = this step has been completed.</dd>
  <dt style='font-weight: bold;'>StepExtra (Optional)</dt>
    <dd>Extra textual information about this step. For example, if this step has to be performed on multiple datasets this entry may indicate which dataset (out of how many) is currently being processed. Not all steps provide such extra information, and for those that do, it is normally only provided when the step is active, as this is the only time it is relevant.</dd>
  <dt style='font-weight: bold;'>SubStep (optional)</dt>
    <dd>Some steps are broken up into smaller steps that are carried out multiple times (e.g. once per dataset selected).
    In this case the parent step has this <code>SubStep</code> entry which is itself an array of steps, i.e. an array of the
    structure being described here. As can be seen, this allows arbitrary nesting, although at the time of writing no product has more
    than one level of <code>SubStep</code> entries.
</dl>



-----

## Examples

### **Example 1, very basic scenario**

This first example is a very simple case; simply get the status of a light curve and a spectrum, do not get the detailed progress for anything.

Here is the JSON object we will send to make the request:

```JSON
{
  "UserID": "YOUR_EMAIL_ADDRESS",
  "JobID": 1,
  "what": "lc,spec"
}
```

And here is the returned JSON. You can see that both products here are running. Although we didn't set the `progWhat` key in our request, the returned JSON still contains a `progress` entry, but it simply has the `GotProgress` key set to 0 and nothing more.

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
    "statusCode": 3,
    "statusText": "Running",
    "progress": {
      "GotProgress": 0
    }
  },
  "OK": 1,
  "JobID": 1
}
```



### **Example 2, More complex scenario**

In this example we request the status of 3 products: light curve, spectrum and a standard (PSF) position. For the spectrum and position we have asked for the detailed progress reporting.

Here is the JSON object we will send to make the request

```JSON
{
  "UserID": "YOUR_EMAIL_ADDRESS",
  "JobID": 1,
  "what": "lc,spec,psf",
  "whatProg" : "spec,psf"
}
```

And here is the returned JSON (explanation below it):

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
    "statusCode": 3,
    "statusText": "Running",
    "progress": {
      "GotProgress": 1,
      "ProgressSteps": [{
        "StepLabel": "Prepare data.",
        "StepStatus": 2
      }, {
        "StepLabel": "Build spectra.",
        "StepStatus": 1,
        "StepExtra": "Working on spectrum: Obs_00081637001 (14/156)",
        "SubStep": [{
          "StepLabel": "Extract data.",
          "StepStatus": 2
        }, {
          "StepLabel": "Fit spectrum.",
          "StepStatus": 1
        }]
      }],
      "TimeRunning": "00:20:40"
    }
  },
  "psf": {
    "statusCode": 3,
    "statusText": "Running",
    "progress": {
      "GotProgress": 1,
      "ProgressSteps": [{
        "StepLabel": "Collect data.",
        "StepStatus": 2
      }, {
        "StepLabel": "Sum images and exposure maps.",
        "StepStatus": 2
      }, {
        "StepLabel": "Perform detection with locally-estimated background",
        "StepStatus": 2
      }, {
        "StepLabel": "Perform PSF fit.",
        "StepStatus": 1
      }],
      "TimeRunning": "00:00:54"
    }
  },
  "OK": 1,
  "JobID": 1
}
```

The light curve looks the same as in the previous example, as you would expect. For the spectrum and standard position the `progress` entry contains much more information. The standard position (`psf`) has reached the &lsquo;Perform PSF fit&rsquo; stage; the preceding steps have `StepStatus`=2, i.e. they are done. 

For the spectrum the situation is a little more complex so needs some explanation. It has reached the &lsquo;Build spectra&rsquo; stage, and it has a `StepExtra` entry which tells me that I requested a total of 156 spectra, and the process is currently working only the 14th of these. This &lsquo;Build spectra&rsquo; stage also has a `SubStep` entry which itself is a list with two stages, &lsquo;Extract data&rsquo; and &lsquo;Fit spectrum.&rsquo; Looking at the `StepStatus` values we can see that it is the second step that is currently active. However, *this will cycle as the job proceeds*, because this `SubStep` is, well, a sub-step of the &lsquo;Build spectra&rsquo; that we can see is going to run 156 times in total. So, if we were polling the status frequently, then when spectrum 14 has been fitted we would find that the `StepExtra` entry for the &lsquo;Build spectra&rsquo; step would change to show that it was working on spectrum 15, and the  &lsquo;Extract data&rsquo; phase would become active (`StepStatus`=1) while &lsquo;Fit spectrum.&rsquo;
would revert to `StepStatus`=0, i.e. it has not yet been reached. Then of course &lsquo;Extract data&rsquo; would change to `StepStatus`=0, and &lsquo;Fit spectrum.&rsquo; to `StepStatus`=1, and so on.

Note also the presence of the `progress.TimeRunning` entry for the spectrum and position. These times are not the same, since the time is how long it is since the job scheduler actually initiated the execution of the jobs, not how long it is since you requested the job.


### **Example 3, The full shebang!**

In this final example we want to know everything. All available products are being built, and we want the status and progress reporting for all of them.

Here is the JSON object we will send to make the request

```JSON
{
  "UserID": "YOUR_EMAIL_ADDRESS",
  "JobID": 1,
  "what": "lc,spec,enh,psf,xastrom,image",
  "whatProg": "lc,spec,enh,psf,xastrom,image"
}
```

And here is the returned JSON. 

```JSON
{
  "lc": {
    "statusCode": 3,
    "statusText": "Running",
    "progress": {
      "GotProgress": 1,
      "ProgressSteps": [{
        "StepLabel": "Prepare data and centroid (if selected).",
        "StepStatus": 1
      }, {
        "StepLabel": "Extract data.",
        "StepStatus": 0
      }, {
        "StepLabel": "Binning light curve.",
        "StepStatus": 0
      }, {
        "StepLabel": "Plotting light curve as image.",
        "StepStatus": 0
      }],
      "TimeRunning": "00:01:23"
    }
  },
  "spec": {
    "statusCode": 3,
    "statusText": "Running",
    "progress": {
      "GotProgress": 1,
      "ProgressSteps": [{
        "StepLabel": "Prepare data.",
        "StepStatus": 2
      }, {
        "StepLabel": "Build spectra.",
        "StepStatus": 1,
        "StepExtra": "Working on spectrum: Obs_00081637001 (14/156)",
        "SubStep": [{
          "StepLabel": "Extract data.",
          "StepStatus": 2
        }, {
          "StepLabel": "Fit spectrum.",
          "StepStatus": 1
        }]
      }],
      "TimeRunning": "00:20:40"
    }
  },
  "enh": {
    "statusCode": 3,
    "statusText": "Running",
    "progress": {
      "PreProgress": "Trying using the <em>v,b,white</em> filters:",
      "GotProgress": 1,
      "ProgressSteps": [{
        "StepLabel": "Identify XRT-UVOT overlaps.",
        "StepStatus": 2
      }, {
        "StepLabel": "Determine position.",
        "StepStatus": 2
      }, {
        "StepLabel": "Build Images.",
        "StepStatus": 1
      }],
      "TimeRunning": "00:01:53"
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
    "statusCode": 3,
    "statusText": "Running",
    "progress": {
      "GotProgress": 1,
      "ProgressSteps": [{
        "StepLabel": "Prepare data.",
        "StepStatus": 2
      }, {
        "StepLabel": "Collect data.",
        "StepStatus": 2
      }, {
        "StepLabel": "Prepare data for iterative source detection.",
        "StepStatus": 2
      }, {
        "StepLabel": "Create per-snapshot images and exposure maps.",
        "StepStatus": 1,
        "StepExtra": "Working on observation 2 / 121"
      }, {
        "StepLabel": "Sum per-snapshot images and exposure maps.",
        "StepStatus": 0
      }, {
        "StepLabel": "Run source detection.",
        "StepStatus": 0
      }, {
        "StepLabel": "Perform initial rough detection with locally-estimated background",
        "StepStatus": 0
      }, {
        "StepLabel": "Construct initial background map.",
        "StepStatus": 0
      }, {
        "StepLabel": "Perform initial source detection using the background map.",
        "StepStatus": 0
      }, {
        "StepLabel": "Searching for sources.",
        "StepStatus": 0,
        "SubStep": [{
          "StepLabel": "PSF fit sources found in previous iteration.",
          "StepStatus": 0
        }, {
          "StepLabel": "Build background map.",
          "StepStatus": 0
        }, {
          "StepLabel": "Perform source detection.",
          "StepStatus": 0
        }]
      }, {
        "StepLabel": "Perform final fit.",
        "StepStatus": 0
      }, {
        "StepLabel": "Calculate astrometric correction.",
        "StepStatus": 0
      }],
      "TimeRunning": "00:02:21"
    }
  },
  "image": {
    "statusCode": 3,
    "statusText": "Running",
    "progress": {
      "GotProgress": 1,
      "ProgressSteps": [{
        "StepLabel": "Collect data.",
        "StepStatus": 2
      }, {
        "StepLabel": "Merge event lists.",
        "StepStatus": 2
      }, {
        "StepLabel": "Creating images.",
        "StepStatus": 2
      }, {
        "StepLabel": "Creating exposure map.",
        "StepStatus": 1
      }],
      "TimeRunning": "00:02:23"
    }
  },
  "OK": 1,
  "JobID": 1
}
```

Obviously this has a lot of entries, as we have requested the progress for every job. A few notes to pull out:

* The standard position has completed, so no detailed progress information is reported.
* The spectrum output looks like in the previous example, not surprising since we requested the same information.
* For both the spectrum and astrometric position (`xastrom`) the active step (where `StepStatus` = 1) has a `StepExtra` entry as well, giving some further information relating to that step.


### **Example 4, requesting the status of non-existent products**

In this example we issued exactly the same request as in example 3 (so not reproduced here), i.e. we asked for the full status and detailed progress of all possible products. However, the job we were querying only contained a spectrum, i.e. there was no light curve, image etc, to get the status of! As you can see from the returned JSON below, this still returns with no error. The spectrum status is reported correctly, whereas for the other products a null, unknown status is returned.

```JSON
{
  "lc": {
    "statusCode": null,
    "statusText": "Unknown status",
    "progress": {
      "GotProgress": 0
    }
  },
  "spec": {
    "statusCode": 3,
    "statusText": "Running",
    "progress": {
      "GotProgress": 1,
      "ProgressSteps": [{
        "StepLabel": "Prepare data.",
        "StepStatus": 1
      }, {
        "StepLabel": "Build spectra.",
        "StepStatus": 0,
        "SubStep": [{
          "StepLabel": "Extract data.",
          "StepStatus": 0
        }, {
          "StepLabel": "Fit spectrum.",
          "StepStatus": 0
        }]
      }],
      "TimeRunning": "00:00:40"
    }
  },
  "enh": {
    "statusCode": null,
    "statusText": "Unknown status",
    "progress": {
      "GotProgress": 0
    }
  },
  "psf": {
    "statusCode": null,
    "statusText": "Unknown status",
    "progress": {
      "GotProgress": 0
    }
  },
  "xastrom": {
    "statusCode": null,
    "statusText": "Unknown status",
    "progress": {
      "GotProgress": 0
    }
  },
  "image": {
    "statusCode": null,
    "statusText": "Unknown status",
    "progress": {
      "GotProgress": 0
    }
  },
  "OK": 1,
  "JobID": 2
}
```



-----


## Example parsing code

At first glance parsing this JSON object can seem a bit daunting, especially given the possibility of recursion within the progress steps. For those programmers less experienced at this kind of parsing, or those (like me) who much prefer the lazy route of stealing and modiying someone else's code wherever possible, here's some example code designed to parse the JSON returned by a status request, and produce some human-readable text.

This example is written in javascript: it's actually the code responsible for producing the status reports on the web pages (those reports are built from the same JSON object described above: under the hood the web page simply submits a request as described on this page, and then turns the output into some HTML). It should be relatively simple to adapt it to your preferred language. NB, to keep this short I've removed all of the error checking from the actual code! i.e. this assumes that the JSON structure return does comply with the above format (if you're feeling particularly masochistic, javascript is by definition viewable from the web, so you can read my [full source code](https://www.swift.ac.uk/user_objects/tprods/statusCheck.js) - see the `checkStatuses()` function).

**Notes**

In the code extract below:

 * The returned JSON has been parsed into an object `data`.
 * The variable `tmpWhat` contains the products for which the status was queried
 * The variable `showProg` is an object whose keys are the products for which the detailed progress was created.
 


```javascript

  // Was OK set?
  if (data.OK === undefined || data.OK==0)
  {
    statusFail(); // Some error function
    return;
  }

  // Loop over the products I asked for, stored in tmpWhat
  for (var i=0; i<tmpWhat.length; ++i)
  {
    const what=tmpWhat[i];
    var myHTML=what+" status: "; // This is where I'm going to save the HTML output describing the status of this product.

    // Get the status and description
    var text = data[what].statusText;
    var code = parseInt(data[what].statusCode);

    myHTML=myHTML + "<code>"+text+"</code>. ";
    
    // Add the progress, id requested
    // We only show the progress for a job that is not complete, i.e. code in the range 1--3
    if (showProg[what] && code>0 && code<4)
    {
      // Should really check that data[what].progress.GotProgress is defined and ==1; removed to shorted this extract

      // If there is somem preprogress text, write it
      if (data[what].progress.PreProgress !== undefined)
        myHTML = myHTML + "<p>" + data[what].progress.PreProgress + "</p>";

      // Now get the steps
      const mySteps=data[what].progress.ProgressSteps;
      // And call a function to write this steps as an HTML list. This function will recursively navigate the steps,
      // including sublists if any step has a SubStep entru
      myHTML = myHTML + showProgressList(mySteps, what);
      
      // And let's report how long we've been going
        myHTML = myHTML + "<p>The job has been running for "+data[what].progress.TimeRunning+" so far.</p>\n";
      
    }
    
    // myHTML now contains the status, and, if requested, progress report of the product 
    // So there is code here to write it to the web page, I leave this to your imagination.
    

  } // Next product
  

  // And we also need the function showProgressList() which was called above to navigate the ProgressSteps object
  // and build a list of the steps etc.


  function showProgressList(mySteps, what)
  {
    // Create an unordered list of the steps
    var out = "<ul title='Steps in the "+what+" creation'>";
    
    // Now go through all the steps and create an entry in the list for each
    for (const i in mySteps) 
    {
      // Get the step into a variable as it  makes the code easier to read.
      const step=mySteps[i];
      out = out + "<li>";
      // If the step is in progress, I want it to be strong
      if (step.StepStatus == 1) // Step in progress:
        out = out + "<strong>";
      // Write the step label
      out = out + step.StepLabel;
      // And, if it was in progress, say so , and add any extra text. And close that <strong> tag!
      if (step.StepStatus == 1) // Step in progress:
      {
        out = out + " <span style='color:blue'>ACTIVE</span>";
        if (step.StepExtra !== undefined) // i.e. write the extra text, if it exists
          out = out + "&#8212; "+step.StepExtra;
        out = out + "</strong>";
      }
      // If the step is done, then say so
      else if (step.StepStatus==2)
        out = out + " <strong style='color:#0D0'>DONE</strong>";

      // If there are substeps then call this same function for those steps. This will create
      // a new unordered list (<ul> tag) within the current list index (<li> tag), i.e. a nested list
      // Since we're calling ourself this is just recursion and will continue adding nested lists
      // for however many levels of substeps we've defined.
      if (step.SubStep !== undefined)
        out = out + showProgressList (step.SubStep, step.StepLabel);

      // End of this step, so close this list index
      out = out + "</li>";
    }
    // And close this list
    out = out + "</ul>";
    return out;
  }




```
