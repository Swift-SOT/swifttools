# XRT Products API

The [tools to build Swift-XRT data products for point sources](https://www.swift.ac.uk/user_objects) can now be accessed via an API. This allows the creation of jobs to be done as part of a command-line script, for example, or within your own pipelines, making it easier to carry out repeated analyses, or analyse a sample of sources. This documentation describes how to use the API. We assume that you are already familiar with the tools themselves, and do not here describe their operation, allowable data formats (e.g. time systems supported) or the detailed meanings of the various parameters. For this, please [read the product generator documentation](https://www.swift.ac.uk/user_objects/docs.php).

**Important note** We still have a finite capacity, so please do not submit large numbers of jobs en masse; instead you can use the API
to submit all of your jobs, but a few at a time, waiting until the requested jobs have completed before submitting the next tranche. 
We do provide [a method to check how many active jobs you have](History.md#check-how-many-active-jobs-you-have), which can
be used in your scripts to control the number of jobs you have active at a time. The limits imposed by the server are very generous
at present, but we suggest that there are few cases in which it wouldbe necessary to have more than 5 requests active at any one time.

This documentation is designed to describe the API and how to use it; it does not explain how to write your own scripts to use this API. The examples given use simple command-line tools interactively, to demonstrate the system operation. Of course, in reality if you ware working interactively it will likely be easier to use the [web interface](https://www.swift.ac.uk/user_objects), and so we expect most users will write their own scripts to call this API, only using the interactive command line for testing and debugging. It is not within our remit to teach you how to write such scripts, nor can we offer any support in terms of debugging any given scripts; only support related to the API.


## Documentation contents

The documentation is organised as follows.

 * [High-level summary of the system](README.md)
 * [Interface for submitting a product request](RequestJob.md).
   * [Example JSON structures for different products](JobRequestExamples1.md).
   * [Example complete JSON structures ready for submission](JobRequestExamples2.md).
 * [Description of the return values from a job submission](ReturnData.md).
   * [Examples of the returned data](ReturnExamples.md).
 * [The interface for cancelling requested jobs](CancelJob.md).
 * [The interface for query the status of a job](JobStatus.md).
 * [How to retrieve the completed products](RetrieveProducts.md).
 * [A simple end-to-end tutorial](tutorial.md).
 * [Exploring old jobs](History.md)
 
 
## Registration

In order to use the API you must register and confirm your email address. No password is needed, and you will never need to log in, however you do need to supply your registered email address with any request or query, and you will only be able to retrieve details about your own jobs via the API. This is primarily for bookkeeping purposes.

To register, please visit [the registration page](https://www.swift.ac.uk/user_objects/register.php) in your web browser. After supplying your email address you will be emailed a link to verify said address.

## Basic use

The API is based on JavaScript Object Notation or [JSON](https://www.json.org). All data sent to the API system should be sent in JSON format, using the HTTP POST protocol. JSON and POST are mature standards, well supported by a range of programming languages and command-line tools, and therefore should be available to use in your environment of choice. In the near future, we will be providing a complete Python front-end to this API, however for now you need to understand the API itself in order to use it.

The simplest way of using the API is via the cross-platform command-line tool `curl`. If you create a file containing a JSON object, you can then submit this via `curl` thus:

```console
> curl --data @myfile.json --request POST -o returnFile.json https://www.swift.ac.uk/user_objects/run_userobject.php 
```

This will send the JSON data contained in `myfile.json` to the URL `https://www.swift.ac.uk/user_objects/run_userobject.php`, and save the returned data in `returnFile.json`. Of course, you can change the filenames, and the URL you submit the request to may change depending on what it is you want to do.

The data returned, here stored in `returnFile.json`, will also be in JSON format (unless there is an HTTP error - see [below](#http-errors). The format of this object depends on the type of request, whether it was to build products, cancel a running job, or request the status of a running job. The formats of the returned JSON are described on the relevant documentation pages (see the [contents](#documentation-contents)).


## HTTP errors

When you send any request to our servers using this API, our servers should return a JSON object. This is true even if the JSON you uploaded was invalid JSON, or your request was invalid in some way: you will get an error message in JSON format. However, *this assumes that there are no network or server errors*. In the event of such a problem the data returned will not be the JSON produced by our API service, but instead some form of HTTP error from either our system or an intervening gateway, and these are normally in HTML format. For example, if you mistype the URL and send a request to `run_userboject.php` then the server will simply return an HTML 404 (page not found) error, and the HTML of our standard 404 page. Similarly if there are network issues so the UKSSDC cannot be reached, or there is a server error on one of our servers then you will get an HTML-format error code. Obviously in this case any attempt to parse the output as JSON will fail.

It is not the purpose of this documentation to teach the general methods to manage the transmission and retrieval of data via HTTP, and indeed, different languages provide different interfaces to achieve this (for example, the `requests` module in Python). However, since all of the examples in this guide and the [tutorial](tutorial.md) make use of `curl` we give here a brief explanation of how to check for HTTP errors with this tool.

In order to check if the request was transmitted and received OK by the server, you need to check the headers of the returned data, and specifically, the very first header value which gives the [HTTP status message](https://www.w3schools.com/tags/ref_httpmessages.asp).
`curl` will include the headers in its output if you call it with the `-i` flag. This will cause the output to contain the full HTTP headers before the data the server returns . The opening line will be the HTTP status, and should read `HTTP/1.1 200 OK`. Any other value indicates that a problem occured. 

Here is an example of a case where the submission proceeded OK (note that code 200 on the opening line); the job itself failed because there were errors with the submission, reported in JSON using the [structure defined for our API](ReturnData.md), but the request was correctly sent and processed. So in this case, you should read and parse the JSON to determine why your job failed.

```
HTTP/1.1 200 OK
Date: Wed, 29 Apr 2020 13:28:37 GMT
Server: Apache
Strict-Transport-Security: max-age=63072000;includeSubDomains
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
X-XSS-Protection: 1;mode=block
Set-Cookie: PHPSESSID=q2tdmajeg135vtiph5sd1t0qc1; expires=Thu, 30-Apr-2020 13:28:37 GMT; path=/; HttpOnly
Expires: Thu, 19 Nov 1981 08:52:00 GMT
Cache-Control: no-store, no-cache, must-revalidate, post-check=0, pre-check=0
Pragma: no-cache
Content-Length: 298
Content-Type: text/html; charset=UTF-8


{"OK":0,"ERROR":"There were problems with the parameters you supplied.","listErr":[{"label":"The following parameters are needed, but were not supplied:","list":["Dec","cent"]},{"label":"The following parameters have invalid values:","list":["poserr is 0.01, but must be between 1 and 6"]}]}
```

In contrast, here is an example where submission failed because of an HTTP error (I mistyped the URL in the `curl` command). You can see that there is no JSON, and the opening header reports an error. (I have truncated the output rather than giving the full HTML 404 error page!):

```
HTTP/1.0 404 Not Found
Date: Thu, 30 Apr 2020 08:42:48 GMT
Server: Apache
Strict-Transport-Security: max-age=63072000;includeSubDomains
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
X-XSS-Protection: 1;mode=block
Connection: close
Content-Type: text/html; charset=UTF-8

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html lang="en" xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title>UKSSDC | 404 page not found</title>
... etc
```

Of course, if you call `curl` with `-i` then this means that you can't simply parse the output file, you must first check and then remove the headers, but this is pretty straight forward: the first line should be the HTTP status, and the JSON will be on a single line, beginning with a `{`, so it is easy enough to find the lines of interest in your script, e.g. via the shell commands:

```
> head -1 returnFile.json # Get the first line = the HTTP status
> grep ^{ returnFile.json # Get the JSON line
```

As noted above, it is not the purpose of this documentation to teach you how to incorporate this into a script, or to produce, submit and process automatically: we are not able to offer a debugging or development service. The above examples simply demonstrate a simple way of using the API interactively from the command line and of managing the result.

