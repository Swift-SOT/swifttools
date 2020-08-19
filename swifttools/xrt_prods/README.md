# XRT Products API

The [tools to build Swift-XRT data products for point sources](https://www.swift.ac.uk/user_objects) can now be accessed via an API. This allows the creation of jobs to be done as part of a command-line script, for example, or within your own pipelines, making it easier to carry out repeated analyses, or analyse a sample of sources. This documentation describes how to use the API. We assume that you are already familiar with the tools themselves, and do not here describe their operation, allowable data formats (e.g. time systems supported) or the detailed meanings of the various parameters. For this, please [read the product generator documentation](https://www.swift.ac.uk/user_objects/docs.php).

**Important note** We still have a finite capacity, so please do not submit large numbers of jobs en masse; instead you can use the API
to submit all of your jobs, but a few at a time, waiting until the requested jobs have completed before submitting the next tranche. 

We provide two mechanisms for using the API, each with their own documentation.

The recommended method is to use [the Python module](pyDocs/README.md), since this manages all of the interaction with the server for you. However, you can also
[directly access the API](APIDocs/README.md) if you prefer to use the command line, or another language.

## Documentation Contents:

 * **Python module**
    * [Introduction / quickstart](pyDocs/README.md)
    * [How to request products](pyDocs/RequestJob.md).
    * [Examining your submitted job](pyDocs/ReturnData.md).
    * [How to cancel requested jobs](pyDocs/CancelJob.md).
    * [How to query the status of a job](pyDocs/JobStatus.md).
    * [How to retrieve the completed products](pyDocs/RetrieveProducts.md).
    * [A simple end-to-end tutorial](pyDocs/tutorial.md).
    * [Miscellaneous methods and advanced usage](pyDocs/advanced.md). 
    * [Full API description](pyDocs/fullAPI.md). 
 * **Direct API access** 
  * [High-level summary of the system](APIDocs/README.md)
  * [Interface for submitting a product request](APIDocs/RequestJob.md).
    * [Example JSON structures for different products](APIDocs/JobRequestExamples1.md).
    * [Example complete JSON structures ready for submission](APIDocs/JobRequestExamples2.md).
  * [Description of the return values from a job submission](APIDocs/ReturnData.md).
    * [Examples of the returned data](APIDocs/ReturnExamples.md).
  * [The interface for cancelling requested jobs](APIDocs/CancelJob.md).
  * [The interface for query the status of a job](APIDocs/JobStatus.md).
  * [How to retrieve the completed products](APIDocs/RetrieveProducts.md).
  * [A simple end-to-end tutorial](APIDocs/tutorial.md).
  * [Exploring old jobs](APIDocs/History.md)

