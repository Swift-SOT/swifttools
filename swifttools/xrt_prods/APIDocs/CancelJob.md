# How to cancel a requested job

It sometimes happens that products are requested but before they are constructed, the need for them goes away. For example, you may realise that you made an error in your job submission, maybe some parameter was set to the wrong value, and the job needs resubmitting. Or a collaborator may email you a link to the products they've just created, making your recently submitted job redundant. In these cases we ask that you cancel your existing job if possible, to reduce the load on our servers and free up slots for other users.

One way of cancelling a job is simply to visit the web page (identified by the `URL` entry in the [data returned when you requested the products](ReturnData.md), and clicking on the links to cancel the jobs. However, this can also be done via the API.

As for all interactions with the API, you send your request as an `HTTP POST` request with the data in `JSON` format. The URL to send the request to is https://www.swift.ac.uk/user_objects/canceljob.php. Below we describe [the JSON you should send](#format-of-the-json-request) and [the returned JSON data](#format-of-the-json-response), and provide [some examples](#examples).

-----

## Format of the JSON request

The JSON data submitted must contain three keys, all of which are mandatory. These are:

<dl title='Keys needed to cancel a job'>
  <dt style='font-weight: bold;'>JobID</dt>
  <dd>The ID number of the job to cancel.</dd>
  <dt style='font-weight: bold;'>UserID</dt>
  <dd>Your user ID (i.e. registered email address). <strong>This must match the userID used to request the job you are now cancelling.</strong></dd>
  <dt style='font-weight: bold;'>what</dt>
  <dd>The product to cancel. If there are more than one this should be a comma-separated list.</dd>
</dl>

The `what` keyword can contain any of the requestable products, using their short forms i.e.:

* lc
* spec
* enh
* psf
* xastrom
* image

-----

## Format of the JSON response

When you submit a cancellation request you will get a JSON object back, with the following keys.

<dl title='Contents of the returned JSON'</dl>
  <dt style='font-weight: bold;'>JobID</dt>
  <dd>The ID of the job you requested to cancel (provided for ease of bookkeeping).</dd>
  <dt style='font-weight: bold;'>OK</dt>
  <dd>Whether the job was processed successfully. This has the following values:
    <ul title='Status codes'>
      <li>0 = An error occured, request not processed.</li>
      <li>1 = OK, jobs cancelled as requested.</li>
      <li>2 = Partial success: your request was processed but at least one of the requested jobs was not cancelled; details will be in the <code>status</code> entry.</li>
    </ul>
  </dd>
  <dt style='font-weight: bold;'>ERROR</dt>
  <dd>Only present if <code>OK</code>=0; this gives a textual description of the problem.</dd>
  <dt style='font-weight: bold;'>status</dt>
  <dd>This is an array, with one entry for each product you asked to cancel. It provides a textual statement describing whether the job was cancelled and if not, why not.</dd>
  <dt style='font-weight: bold;'>statusCodes</dt>
  <dd>This is an array with one entry for each product you asked to cancel. It gives a numerical code indicating the outcome of the attempts to cancel the job. These codes have values:
    <ul title='Product status codes'>
      <li>0 = Success, job cancelled.</li>
      <li>1 = Job not cancelled, most likely it has already completed.</li>
      <li>2 = Job not cancelled, no record of this product could be found for this jobID.</li>
      <li>3 = Job not cancelled, reason unknown.</li>
      <li>4 = Status unknown: an error occured meaning we can't determine whether or not the job was cancelled.</li>
    </ul>
  </dd>
  
</dl>


-----

# Examples

Here is a simple example that will ask that the light curve and spectrum associated with jobID #1, owned by `YOUR_EMAIL_ADDRESS` be cancelled.

```JSON
{
  "UserID": "YOUR_EMAIL ADDRESS",
  "JobID":  1,
  "what": "lc,spec"
}
```

In the event of success, the JSON object below is received.

```JSON
{
	"JobID": 1,
	"OK": 1,
	"status": {
		"lc": "Job cancelled OK",
		"spec": "Job cancelled OK"
	},
	"statusCodes": {
		"lc": 0,
		"spec": 0
	}
}
```

If the request is processed, but one of the jobs cannot be cancelled you may get some output like this:

```JSON
{
	"JobID": 1,
	"OK": 2,
	"status": {
		"lc": "Job could not be cancelled - has it already finished?",
		"spec": "Job cancelled OK"
	},
	"statusCodes": {
		"lc": 1,
		"spec": 0
	}
}
```
And if the request is not processed due to an error, you will see something like this:

```JSON
{
	"OK": 0,
	"ERROR": "Job 147 is not owned by user frodo@mount.doom"
}
```
