# System response to a request to build products

When you submit a job to the API, it returns a JSON object. This contains the key `OK`, which has a value of `0` (i.e. no, not OK), or `1` (i.e. yes, request processed OK). The remaining contents of the JSON object depend on whether the job was processed OK or not, as described below.

### Successful job submission

In the event that the job was submitted OK, the JSON object will have the following entries.

<dl title='Structure of a successful job acknowledgment'>
  <dt style='font-weight: bold;'>OK</dt>
  <dd>Whether the job was submitted successfully; in this case it will be 1.</dd>
  <dt style='font-weight: bold;'>URL</dt>
  <dd>The URL at which you can view the products/progress, or from which you can download them when complete.</dd>
  <dt style='font-weight: bold;'>JobID</dt>
  <dd>A unique identifier relating your job. <strong>This ID is needed for you to perform any future interaction with the job through the API, e.g. cancel the job or query the progress</strong>.</dd>
  <dt style='font-weight: bold;'>APIVersion</dt>
  <dd>The current version of the API.</dd>
  <dt style='font-weight: bold;'>jobPars</dt>
  <dd>An object corresponding to all of the parameters related to the job, after internal processing. More details below.</dd>
</dl>

The `jobPars` entry in the returned JSON may appear at first glance redundant, however may do more than simply echo back your own parameters to you. It will also include any parameters which you did not specify with their default values, and also any values which you requested the system to determine (such as coordinates or targetID). This is helpful as it both tells you what those defaults were, and it allows to to request a job with the same set of parameters again if you need to, without relying on the fact that we have not changed these. An example of such use may be where Swift is observing an object for you every few days, with the same targetID (but obviously a new obsID each time). After each observation you want to create a new spectrum and light curve using all available data but with all other parameters the same, i.e. the only difference between each product is the addition of the new observation. By saving the `jobPars` returned from your first job request, and then using this as the submission string for all future requests, you would achieve this. **Important note** if you do wish to exactly repeat a job in this way, and the original submission used any of the `getT0`, `getTargs` or `getCoords` options you should **remove** these from the returned JSON before your next submission, to ensure that the value determined by these options in the first run are used in subsequent runs.


### Unsuccessful job submission

If the job cannot be processed due to an error, the JSON object will have the following structure:

<dl title='Structure of an unsuccessful job acknowledgment'>
  <dt style='font-weight: bold;'>OK</dt>
  <dd>Whether the job was submitted successfully; in this case it will be 0.</dd>
  <dt style='font-weight: bold;'>APIVersion</dt>
  <dd>The current version of the API.</dd>
  <dt style='font-weight: bold;'>ERROR</dt>
  <dd>The error message</dd>
  <dt style='font-weight: bold;'>listErr [optional]</dt>
  <dd>Some errors provide one or more lists of problems to resolve (such as missing or invalid parameters). In that case this element of the returned JSON is also set; it is itself an array as it can have one or more entries; the structure of this array is:
    <dl title='Structure of listErr'>
      <dt style='font-weight: bold;'>label</dt>
        <dd>Some explanatory text relating to the listed values</dd>
      <dt style='font-weight: bold;'>list</dt>
        <dd>An array of the errors in this list</dd>
    </dl>

  </dd>
</dl>

See [the example return JSON](ReturnExamples.md) for an illustration.


