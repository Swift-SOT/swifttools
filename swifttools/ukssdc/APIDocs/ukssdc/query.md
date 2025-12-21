# The `swifttools.ukssdc.query` module

[Jupyter notebook version of this page](query.ipynb)

**Latest version v1.0, released in swifttools v3.0**

The `query` module provides tools to query various catalogues held at the UKSSDC (and a couple of others) and provides wrappers to get data for the objects we find. There are two types of query supported, a cone search and a more complex search applying filters to different fields. These are analogous to the 'simple' and 'advanced' searches available on the website.

Unlike the [the `data` module](data.md) (which provided functions to get specific products), the `query` module provided classes: we create query objects and then manipulate and use these to perform our query and play with the results. There are three query classes provided:

* [ObsQuery](#obsquery) - This lets us query the databases of Swift observations.
* [GRBQuery](query/GRB.md) - This lets us query several GRB catalogues.
* [SXPSQuery](query/SXPS.md) - This lets us query the SXPS catalogues.

Whichever class you want, I **strongly** advise you to read this page first. Although it deals with the `ObsQuery` class, that class only contains functionality common to all of the classes, and so all the common concepts are introduced here, and not necessarily repeated on the other pages.

The `query` module also provides access to data or data products, by wrapping functions from [the data module](data.md).I will not go into much detail about those functions and what they produce, since this has been covered in the relevant pages for the [data module](data.md) already. One crucial point, however, does need discussing: how the query module makes any requested data available to you (if you haven't read about the data module, ignore this point because it will just confuse you - you'll see how we get data shortly).
In [the data module](data.md) the default behaviour when getting a product was to download files to disk, but you could instead request the data be returned from the function so you could capture it in a variable. For the query module, the requested data are always stored in variables inside your query object. You can still also request that they be saved to disk, or returned from the function that got them (using the same `returnData` and `saveData` arguments as in [the data module](data.md)) but these are not done by default.

In this notebook we will demonstrate the query interface for observation data, which is quite straightforward and also gets us familiar with the module syntax.

We will import the query module as `uq`:


```python
import swifttools.ukssdc.query as uq
```

## Contents

* [The `ObsQuery` class](#obsquery)
  * [Selecting a table](#table)
* [Simple (cone) searches](#simple)
* [Selecting columns to retrieve](#columns)
* [Advanced queries](#advanced)
* [Extra query settings](#extra)
* [Retrieving products](#prods)
  * [For only some rows](#subsets)

<a id='obsquery'></a>
## The `ObsQuery` Class

The `ObsQuery` class allows us to query the Swift observation database, it is the API equivalent of [this UKSSDC webpage](https://www.swift.ac.uk/swift_live). The only functionality it provides is that which is common to the entire `swifttools.ukssdc.query` module and all subclasses, so it's the perfect one to use as an introduction.

As discussed above, this module is built around classes, so the first thing we have to do is create an ObsQuery object:





```python
q = uq.ObsQuery(silent=False)
```

    Resetting query details


I set `silent=False` because in an interactive case like this, it can be helpful to get some textual feedback. If you want even more feedback you can set `verbose=True`. These can be set in the constructor, or via simple calls:


```python
q.verbose = True
q.verbose = False # Turn it off again!
```

<a id='table'></a>
### Selecting a table

There are several database tables relating to Swift observations. Just like [the website](https://www.swift.ac.uk/swift_live), the API gives you the most useful (I think) one by default, but of course, you can change this. But how? Well, first, we want to know what tables we have to choose from, and this is stored in the `tables` variable of our query object:


```python
q.tables
```




    ('swiftmastr', 'swiftxrlog', 'swiftbalog', 'swiftuvlog', 'swifttdrss')



We can also check which one is currently selected, or change it, via the `table` variable:


```python
q.table
```




    'swiftmastr'




```python
q.table = 'swiftxrlog'
```

    Resetting query details


You'll notice the cell that changed the table warned us that it was resetting the query details. This only appeared because we have `silent=False` and don't worry about it too much now. Basically it is warning us that any filters set or results retrieved (all covered below) have been wiped because we changed table. We could also have set the table we wanted in the constructor:


```python
q = uq.ObsQuery(table='swiftbalog',
                silent=False
               )
q.table
```

    Resetting query details





    'swiftbalog'



I won't keep saying this but I'll remind you here: `ObsQuery` only contains behaviour common to the entire `query` module, so the syntax for checking and changing tables is the same for the [`GRBQuery`](query/GRB.md) and [`SXPSQuery`](query/SXPS.md) modules (and for any others I may add in the future).

<a id='simple'></a>
## Simple (cone) searches

A simple search is just a cone search, and rather than pontificating, let's just demonstrate. I will stick with the default table, "swiftmastr" for all the demonstrations below.


```python
q = uq.ObsQuery(silent=False)
q.addConeSearch(name='GK Per', radius=300, units='arcsec')
q.submit()
```

    Resetting query details
    Need to get the metadata to check the query is valid.
    Calling DB look-up for rows 0 -- 1000
    Resolved 'GK Per' as (52.80004119305, 43.90429720867) via SIMBAD
    Received 145 rows.


That was pretty straightforward wasn't it? We introduced two functions here, `addConeSearch()` and `submit()`. The latter is very easy: it takes no arguments and just submits our query object for execution.

`addConeSearch()` should also be pretty clear, but I'll elaborate on its arguments in a moment.

Because we disabled silent mode, we got a bit of information about what was going on, and we can see, firstly, that "GK Per" was resolved into coordinates (thank you [SIMBAD](http://simbad.u-strasbg.fr/simbad/)), and secondly, that we got 145 results. But where are those results? They are stored inside your query object (`q`) and the variable holding them is cunningly named `results`. This is a `pandas DataFrame` and we can have a look at it:


```python
q.results
```




<div style='width: 95%; max-height: 200px; overflow: scroll;'><style scoped>    .dataframe tbody tr th:only-of-type {        vertical-align: middle;    }    .dataframe tbody tr th {        vertical-align: top;    }    .dataframe thead th {        text-align: right;    }</style><table border="1" class="dataframe">  <thead>    <tr style="text-align: right;">      <th></th>      <th>_r</th>      <th>name</th>      <th>target_id</th>      <th>ra</th>      <th>decl</th>      <th>roll_angle</th>      <th>start_time</th>      <th>stop_time</th>      <th>obs_segment</th>      <th>obsid</th>      <th>bat_exposure</th>      <th>xrt_exposure</th>      <th>xrt_expo_wt</th>      <th>xrt_expo_pc</th>      <th>uvot_exposure</th>      <th>ra_s</th>      <th>ra_apy</th>      <th>decl_s</th>      <th>decl_apy</th>    </tr>  </thead>  <tbody>    <tr>      <th>0</th>      <td>10.171878</td>      <td>GKPer</td>      <td>30842</td>      <td>52.796556</td>      <td>43.903002</td>      <td>254.995416</td>      <td>2010-03-09T00:11:00</td>      <td>2010-03-09T01:29:57</td>      <td>27</td>      <td>00030842027</td>      <td>1483</td>      <td>1717.359</td>      <td>3.086</td>      <td>1714.273</td>      <td>1698.728</td>      <td>+03h 31m 11.17s</td>      <td>52d47m47.6016s</td>      <td>+43d 54m 10.8s</td>      <td>43d54m10.8072s</td>    </tr>    <tr>      <th>1</th>      <td>12.212516</td>      <td>GKPer</td>      <td>30842</td>      <td>52.803476</td>      <td>43.901977</td>      <td>257.760120</td>      <td>2010-03-08T19:18:00</td>      <td>2010-03-08T23:09:41</td>      <td>24</td>      <td>00030842024</td>      <td>2031</td>      <td>1978.567</td>      <td>12.484</td>      <td>1966.083</td>      <td>1958.950</td>      <td>+03h 31m 12.83s</td>      <td>52d48m12.5136s</td>      <td>+43d 54m 7.1s</td>      <td>43d54m07.1172s</td>    </tr>    <tr>      <th>2</th>      <td>15.595530</td>      <td>GKPeroffset1</td>      <td>31653</td>      <td>52.805844</td>      <td>43.905432</td>      <td>239.081804</td>      <td>2010-03-29T21:23:00</td>      <td>2010-03-29T23:53:15</td>      <td>44</td>      <td>00031653044</td>      <td>600</td>      <td>88.973</td>      <td>88.973</td>      <td>0.000</td>      <td>85.682</td>      <td>+03h 31m 13.40s</td>      <td>52d48m21.0384s</td>      <td>+43d 54m 19.6s</td>      <td>43d54m19.5552s</td>    </tr>    <tr>      <th>3</th>      <td>17.510511</td>      <td>GKPeroffset1</td>      <td>31653</td>      <td>52.793651</td>      <td>43.905866</td>      <td>239.071668</td>      <td>2010-03-12T11:49:59</td>      <td>2010-03-12T12:44:19</td>      <td>11</td>      <td>00031653011</td>      <td>301</td>      <td>39.563</td>      <td>1.963</td>      <td>37.600</td>      <td>39.575</td>      <td>+03h 31m 10.48s</td>      <td>52d47m37.1436s</td>      <td>+43d 54m 21.1s</td>      <td>43d54m21.1176s</td>    </tr>    <tr>      <th>4</th>      <td>21.057130</td>      <td>GKPer</td>      <td>30842</td>      <td>52.792533</td>      <td>43.902073</td>      <td>270.123645</td>      <td>2007-01-30T01:37:30</td>      <td>2007-01-30T07:19:01</td>      <td>7</td>      <td>00030842007</td>      <td>1054</td>      <td>986.560</td>      <td>19.631</td>      <td>966.929</td>      <td>986.906</td>      <td>+03h 31m 10.21s</td>      <td>52d47m33.1188s</td>      <td>+43d 54m 7.5s</td>      <td>43d54m07.4628s</td>    </tr>    <tr>      <th>...</th>      <td>...</td>      <td>...</td>      <td>...</td>      <td>...</td>      <td>...</td>      <td>...</td>      <td>...</td>      <td>...</td>      <td>...</td>      <td>...</td>      <td>...</td>      <td>...</td>      <td>...</td>      <td>...</td>      <td>...</td>      <td>...</td>      <td>...</td>      <td>...</td>      <td>...</td>    </tr>    <tr>      <th>140</th>      <td>269.556139</td>      <td>GKPer</td>      <td>30842</td>      <td>52.724707</td>      <td>43.955901</td>      <td>220.787476</td>      <td>2015-04-07T01:17:59</td>      <td>2015-04-07T13:43:55</td>      <td>73</td>      <td>00030842073</td>      <td>1271</td>      <td>1264.049</td>      <td>1264.049</td>      <td>0.000</td>      <td>1256.760</td>      <td>+03h 30m 53.93s</td>      <td>52d43m28.9452s</td>      <td>+43d 57m 21.2s</td>      <td>43d57m21.2436s</td>    </tr>    <tr>      <th>141</th>      <td>281.324633</td>      <td>GKPeroffset1</td>      <td>31653</td>      <td>52.697974</td>      <td>43.930776</td>      <td>238.993264</td>      <td>2010-03-25T13:09:00</td>      <td>2010-03-25T15:44:59</td>      <td>36</td>      <td>00031653036</td>      <td>600</td>      <td>103.897</td>      <td>103.897</td>      <td>0.000</td>      <td>97.012</td>      <td>+03h 30m 47.51s</td>      <td>52d41m52.7064s</td>      <td>+43d 55m 50.8s</td>      <td>43d55m50.7936s</td>    </tr>    <tr>      <th>142</th>      <td>287.191916</td>      <td>GKPer</td>      <td>30842</td>      <td>52.692720</td>      <td>43.923969</td>      <td>245.243652</td>      <td>2015-03-26T19:32:59</td>      <td>2015-03-26T21:07:46</td>      <td>62</td>      <td>00030842062</td>      <td>1227</td>      <td>1220.134</td>      <td>4.095</td>      <td>1216.039</td>      <td>1219.336</td>      <td>+03h 30m 46.25s</td>      <td>52d41m33.792s</td>      <td>+43d 55m 26.3s</td>      <td>43d55m26.2884s</td>    </tr>    <tr>      <th>143</th>      <td>292.861073</td>      <td>GKPer</td>      <td>30842</td>      <td>52.699655</td>      <td>43.941577</td>      <td>249.143502</td>      <td>2015-03-16T13:42:58</td>      <td>2015-03-16T14:36:55</td>      <td>42</td>      <td>00030842042</td>      <td>970</td>      <td>958.988</td>      <td>6.226</td>      <td>952.762</td>      <td>961.740</td>      <td>+03h 30m 47.92s</td>      <td>52d41m58.758s</td>      <td>+43d 56m 29.7s</td>      <td>43d56m29.6772s</td>    </tr>    <tr>      <th>144</th>      <td>299.472390</td>      <td>GKPer</td>      <td>30842</td>      <td>52.792423</td>      <td>43.987303</td>      <td>241.157935</td>      <td>2015-04-02T03:08:59</td>      <td>2015-04-02T04:02:27</td>      <td>68</td>      <td>00030842068</td>      <td>1058</td>      <td>1054.447</td>      <td>1054.447</td>      <td>0.000</td>      <td>1050.411</td>      <td>+03h 31m 10.18s</td>      <td>52d47m32.7228s</td>      <td>+43d 59m 14.3s</td>      <td>43d59m14.2908s</td>    </tr>  </tbody></table><p>145 rows × 19 columns</p></div>


You can explore this at your leisure, but let me highlight one point regarding coordinates. In the databases we query, coordinates are stored in decimal degrees (J2000), but this may not be how you want them. So, when you perform a query that gets coordinates, the `query` module will do a bit of extra work. It identifies all of the coordinate columns and creates sexagesimal versions of the coordinates to (in the format of strings). To identify these, "\_s" is appended to the column name (so in the above, "ra" and "decl" were part of the database, and "ra_s", "decl_s" have been added. Also, if you have the `astropy` module installed then the coordinates will be converted into `astropy.coordinate.Angle` objects and identied by "\_apy" ("ra_apy" and "decl_apy" in the above.

When we executed the query above, we were told how the name supplied had been resolved; but only because we set `silent=False`, and not in a way that we could have readily captured in our script. Despair not, the details of the name resolution are also in class variables:


```python
q.resolvedInfo
```




    "Resolved 'GK Per' as (52.80004119305, 43.90429720867) via SIMBAD"



Or indeed:


```python
print(q.resolvedRA)
print(q.resolvedDec)
```

    52.80004119305
    43.90429720867


We're going to go back and look at `addConeSearch()` a bit more and explore some of its syntax, but if we just ran `q.addConeSearch()` again now, we'd get an error telling us our query was locked. This is because when a query is submitted it is locked to prevent ending up in a confused state (a trivial example; imagine you ran the query above and then ran `q.addConeSearch(name='FO Aqr')` but due to an error, didn't submit it; it would be easy to mistakenly think that `q.results` was related to the FO Aqr search. It isn't).

So, if we want to do another query we either need to make a new `ObsQuery` object, or reset the one we have. Let's do the latter:


```python
q.reset()
```

    Resetting query details


Now we can make any changes we like. Before I move on I'll note that `q.reset()` has some options, you don't have to reset literally everything, but you can read about those via the `help` command if you want.

So, now we can do another cone search if we want. Before we do, let's look at the arguments that this function takes. You could do this via `help (q.addConeSearch)` but I'll be nice and elaborate here.

A cone search needs to know two things:

1. The centre of the cone
1. The radius of the cone.

The latter is easy, it is managed by two arguments:

* `radius` - a number giving the radius.
* `units` - the units of `radius`, must be 'arcsec', 'arcmin' or 'deg' (default: 'arcsec').

The centre of the cone can be specified in a few ways, via these arguments:

* `name` - a string giving an object name which we will attempt to resolve.
* `position` - a free-form string giving the position, which we will attempt to parse.
* `ra` and `dec` - Two arguments that can either be `float`s or `astropy.coordinates.Angle` objects.

You should only provide one of these arguments (OK, two if `ra` and `dec`) or you will get an error. `name` was used above. `position` is a free-form string and we have tried to accept almost any sane way in which you may enter coordinates (provided they are in J2000). So, all of the examples below will work:



```python
q.addConeSearch(ra=123.456, dec=-43.221, radius=1, units='deg')
q.addConeSearch(position='12 13 15, -15 16 17', radius=12, units='arcmin')

from astropy.coordinates import Angle
ra = Angle('12h 13m 14s')
dec = Angle('-13d 14m 15s')
q.addConeSearch(ra=ra, dec=dec, radius=300, units='arcsec')
```

If you provided a `name` or `position`, it will be resolved when the query is submitted, so you can check the details of the resolution using the `q.resolvedRA` etc. variables already introduced. If you supplied `ra` and `dec` you can actually read these back; for example if you don't trust `astropy` as used above, we can check that the correct decimal values were extracted:


```python
print(q.coneRA)
print(q.coneDec)
```

    183.3083333333333
    -13.237499999999999


Note that these variables are read-only so don't try to edit them. If you made a mistake you can use `q.editConeSearch()`, which takes exactly the same arguments as `addConeSearch()`.

We can also change our minds completely and remove the cone search settings from our query:


```python
q.removeConeSearch()
```

That's all there is to setting up the cone search aspect of the query.
## Selecting which columns to retrieve

When we ran our demo query above, we got a lot of columns containing data, but what if we didn't want them all? Or if we wanted one not included? The default set of columns returned is not exhaustive. Well, of course, you can change what set of columns you get as we'll now discuss. First of all, it would be nice to know what we are going to get by default. These are stored in the `defaultCols` variable:


```python
q = uq.ObsQuery(silent=False)
q.defaultCols
```

    Resetting query details
    Need to get the metadata.





    ['name',
     'target_id',
     'ra',
     'decl',
     'roll_angle',
     'start_time',
     'stop_time',
     'obs_segment',
     'obsid',
     'bat_exposure',
     'xrt_exposure',
     'xrt_expo_wt',
     'xrt_expo_pc',
     'uvot_exposure']



As you can see, this is just a list, and it's a list of column names. Which is nice and all, but what actually are these columns, and what extra ones are available?

Because we have `silent=False` you can see from the above that in order to identify the default columns, the Python module grabbed some metadata. It is this metadata which tells us all about the table. Let's take a look at it:


```python
q.metadata
```




<div style='width: 95%; max-height: 200px; overflow: scroll;'><style scoped>    .dataframe tbody tr th:only-of-type {        vertical-align: middle;    }    .dataframe tbody tr th {        vertical-align: top;    }    .dataframe thead th {        text-align: right;    }</style><table border="1" class="dataframe">  <thead>    <tr style="text-align: right;">      <th></th>      <th>ColName</th>      <th>Class</th>      <th>Description</th>      <th>Type</th>      <th>LongDescription</th>      <th>IsObsCol</th>      <th>IsTargetCol</th>    </tr>  </thead>  <tbody>    <tr>      <th>0</th>      <td>name</td>      <td>BASIC</td>      <td>Designation of the NFI Pointed Source</td>      <td>TXT</td>      <td>This is the name of the pointed target. For GR...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>1</th>      <td>orig_target_id</td>      <td>MISC</td>      <td>Trigger Number as Originally Assigned</td>      <td>INT</td>      <td>This is a numerical value assigned automatical...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>2</th>      <td>target_id</td>      <td>BASIC</td>      <td>Unique Trigger Number with Any Degeneracy Removed</td>      <td>INT</td>      <td>This is a unique numerical value assigned to e...</td>      <td>0</td>      <td>1</td>    </tr>    <tr>      <th>3</th>      <td>ra</td>      <td>BASIC</td>      <td>Right Ascension (Pointing Position)</td>      <td>COORDH</td>      <td>Right Ascension of the pointing position. Note...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>4</th>      <td>decl</td>      <td>BASIC</td>      <td>Declination (Pointing Position)</td>      <td>COORDD</td>      <td>Declination of the pointing position. Note tha...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>5</th>      <td>roll_angle</td>      <td>BASIC</td>      <td>Roll Angle (degree)</td>      <td>FLOAT</td>      <td>Roll angle of the observation given in degrees.</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>6</th>      <td>start_time</td>      <td>BASIC</td>      <td>Start Time of the Observation</td>      <td>TXT</td>      <td>Start time of the observation. Note that the d...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>7</th>      <td>stop_time</td>      <td>BASIC</td>      <td>Stop Time of the Observation</td>      <td>TXT</td>      <td>Stop time of the observation. For an Automatic...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>8</th>      <td>orig_obs_segment</td>      <td>MISC</td>      <td>Observation Segment as Originally Assigned</td>      <td>INT</td>      <td>The Swift observation strategy is similar to a...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>9</th>      <td>obs_segment</td>      <td>BASIC</td>      <td>True Observation Segment (Corrected Value)</td>      <td>INT</td>      <td>Observation Segment. The Swift observation str...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>10</th>      <td>orig_obsid</td>      <td>MISC</td>      <td>Observation Number as Originally Assigned (Ori...</td>      <td>TXT</td>      <td>This parameter contains a numeric value that s...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>11</th>      <td>obsid</td>      <td>BASIC</td>      <td>Unique Observation Number (Target_ID + Obs_Seg...</td>      <td>TXT</td>      <td>This parameter contains a numeric value that u...</td>      <td>1</td>      <td>0</td>    </tr>    <tr>      <th>12</th>      <td>bat_exposure</td>      <td>BASIC BAT</td>      <td>Effective Exposure Event and Survey modes with...</td>      <td>FLOAT</td>      <td>The BAT exposure in seconds on source. The BAT...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>13</th>      <td>xrt_exposure</td>      <td>BASIC XRT</td>      <td>Effective Exposure on Source All XRT Modes</td>      <td>FLOAT</td>      <td>The XRT exposure in seconds on source. The XRT...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>14</th>      <td>xrt_expo_wt</td>      <td>BASIC XRT</td>      <td>Effective Exposure on Source Windowed Timing  ...</td>      <td>FLOAT</td>      <td>The XRT exposure on source when the Windowed T...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>15</th>      <td>xrt_expo_pc</td>      <td>BASIC XRT</td>      <td>Effective Exposure on Source Photon Counting X...</td>      <td>FLOAT</td>      <td>The XRT exposure on source when the Photon Cou...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>16</th>      <td>uvot_exposure</td>      <td>BASIC UVOT</td>      <td>Effective Exposure on Source All UVOT Filters ...</td>      <td>FLOAT</td>      <td>The UVOT exposure in seconds on source. The UV...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>17</th>      <td>xrt_expo_lr</td>      <td>XRT</td>      <td>Effective Exposure on Source Low Rate Photodio...</td>      <td>FLOAT</td>      <td>The XRT exposure on source when the Low-Rate P...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>18</th>      <td>xrt_expo_pu</td>      <td>XRT</td>      <td>Effective Exposure on Source Piled-up Photodio...</td>      <td>FLOAT</td>      <td>The XRT exposure on source when the Piled-Up P...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>19</th>      <td>xrt_expo_im</td>      <td>XRT</td>      <td>Effective Exposure on Source Image Modes</td>      <td>FLOAT</td>      <td>The XRT exposure on source when the IMAGE (IM)...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>20</th>      <td>uvot_expo_uu</td>      <td>UVOT</td>      <td>Effective Exposure on Source U UVOT Filter</td>      <td>FLOAT</td>      <td>The UVOT exposure on source when the U filter ...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>21</th>      <td>uvot_expo_bb</td>      <td>UVOT</td>      <td>Effective Exposure on Source B UVOT Filter</td>      <td>FLOAT</td>      <td>The UVOT exposure on source when the B filter ...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>22</th>      <td>uvot_expo_vv</td>      <td>UVOT</td>      <td>Effective Exposure on Source V UVOT Filter</td>      <td>FLOAT</td>      <td>The UVOT exposure on source when the V filter ...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>23</th>      <td>uvot_expo_w1</td>      <td>UVOT</td>      <td>Effective Exposure on Source UVW1 UVOT Filter</td>      <td>FLOAT</td>      <td>The UVOT exposure on source when the UVW1 filt...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>24</th>      <td>uvot_expo_w2</td>      <td>UVOT</td>      <td>Effective Exposure on Source UVW2 UVOT Filter</td>      <td>FLOAT</td>      <td>The UVOT exposure on source when the UVW2 filt...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>25</th>      <td>uvot_expo_m2</td>      <td>UVOT</td>      <td>Effective Exposure on Source UVM2 UVOT Filter</td>      <td>FLOAT</td>      <td>The UVOT exposure on source when the UVM2 filt...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>26</th>      <td>uvot_expo_wh</td>      <td>UVOT</td>      <td>Effective Exposure on Source WHITE UVOT Filter</td>      <td>FLOAT</td>      <td>The UVOT exposure on source when the White fil...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>27</th>      <td>uvot_expo_gu</td>      <td>UVOT</td>      <td>Effective Exposure on Source UGRISM UVOT Filter</td>      <td>FLOAT</td>      <td>The UVOT exposure on source when the UGRISM fi...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>28</th>      <td>uvot_expo_gv</td>      <td>UVOT</td>      <td>Effective Exposure on Source VGRISM UVOT Filter</td>      <td>FLOAT</td>      <td>The UVOT exposure on source when the VGRISM fi...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>29</th>      <td>uvot_expo_mg</td>      <td>UVOT</td>      <td>Effective Exposure on Source Magnifier UVOT Fi...</td>      <td>FLOAT</td>      <td>The UVOT exposure on source when the Magnifier...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>30</th>      <td>uvot_expo_bl</td>      <td>UVOT</td>      <td>Effective Exposure Blocked Filter</td>      <td>FLOAT</td>      <td>None</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>31</th>      <td>bat_expo_ev</td>      <td>BAT</td>      <td>Effective Exposure Event mode</td>      <td>FLOAT</td>      <td>The BAT exposure on source when the EVENT mode...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>32</th>      <td>bat_expo_sv</td>      <td>BAT</td>      <td>Effective Exposure Survey mode</td>      <td>FLOAT</td>      <td>BAT exposure on source when the SURVEY mode wa...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>33</th>      <td>bat_expo_rt</td>      <td>BAT</td>      <td>Effective Exposure Rate mode</td>      <td>FLOAT</td>      <td>BAT exposure on source when the RATE mode was ...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>34</th>      <td>bat_expo_mt</td>      <td>BAT</td>      <td>Effective Exposure Masktag mode</td>      <td>FLOAT</td>      <td>Cumulative BAT exposure of all sources tagged ...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>35</th>      <td>bat_expo_pl</td>      <td>BAT</td>      <td>Effective Exposure pulsar mode</td>      <td>FLOAT</td>      <td>BAT exposure on source when the PULSAR mode wa...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>36</th>      <td>bat_no_masktag</td>      <td>BAT</td>      <td>Number of sources with mask tag rate within th...</td>      <td>INT</td>      <td>Number of sources for which the MASKTAG rate m...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>37</th>      <td>archive_date</td>      <td>MISC</td>      <td>Public date</td>      <td>TXT</td>      <td>The archive_date is the date when the data are...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>38</th>      <td>soft_version</td>      <td>MISC</td>      <td>Software version used in the pipeline</td>      <td>TXT</td>      <td>None</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>39</th>      <td>processing_date</td>      <td>MISC</td>      <td>Date of Processing</td>      <td>TXT</td>      <td>This records the date when the data were proce...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>40</th>      <td>processing_version</td>      <td>MISC</td>      <td>Version of Processing Scrip</td>      <td>TXT</td>      <td>This records the version of the processing scr...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>41</th>      <td>num_processed</td>      <td>MISC</td>      <td>Number of Times a Sequence Has Been Processed</td>      <td>INT</td>      <td>This records the number of times a data set ha...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>42</th>      <td>cycle</td>      <td>MISC</td>      <td>Proposal cycle number</td>      <td>INT</td>      <td>The proposal cycle number of the observation.</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>43</th>      <td>pi</td>      <td>MISC</td>      <td>PI Last Name</td>      <td>TXT</td>      <td>Principal Investigator. If the Swift Announcem...</td>      <td>0</td>      <td>0</td>    </tr>    <tr>      <th>44</th>      <td>att_flag</td>      <td>MISC</td>      <td>Attitude flag</td>      <td>TXT</td>      <td>Attitude flag.</td>      <td>0</td>      <td>0</td>    </tr>  </tbody></table></div>


Table metadata is made available in the form of a `pandas DataFrame`. The exact columns in this do differ slightly for the different tables (and modules; 'LongDescription' is only present for the `ObsQuery` class), and not all of them are relevant for you - some are needed internally by the Python module, and some are needed by the web interfaces to the databases. The columns you really care about are "ColName" and "Description" which should provide enough details for you to choose whether the default columns are enough, or if you want to edit them.

So, knowing what columns exist, we can now decide which ones we want to obtain, if we didn't just want the default. We add columns using the `addCol()` function. This takes either `*` (to get everything), a column name, or a list/tuple of column names. So:


```python
q.addCol('name')
q.colsToGet
```




    ['name']



As shown above, the `colsToGet` variable (which you cannot edit directly) tells you what columns are selected, and you may have noticed that now we've explicitly said what we want, all the default columns are not there. We can easily add them back in though:


```python
q.addCol(q.defaultCols)
q.colsToGet
```

    Cannot add column name; it is already selected.





    ['name',
     'target_id',
     'ra',
     'decl',
     'roll_angle',
     'start_time',
     'stop_time',
     'obs_segment',
     'obsid',
     'bat_exposure',
     'xrt_exposure',
     'xrt_expo_wt',
     'xrt_expo_pc',
     'uvot_exposure']



You note that we got a warning because we tried to add an existing column in, but it was just a warning and did not stop the other columns being added. We can also remove columns with `removeCol`, or `removeAllCols`. So here are some examples:


```python
q.removeCol('name')
q.colsToGet
```




    ['target_id',
     'ra',
     'decl',
     'roll_angle',
     'start_time',
     'stop_time',
     'obs_segment',
     'obsid',
     'bat_exposure',
     'xrt_exposure',
     'xrt_expo_wt',
     'xrt_expo_pc',
     'uvot_exposure']




```python
q.removeCol(('obsid', 'stop_time'))
q.colsToGet
```




    ['target_id',
     'ra',
     'decl',
     'roll_angle',
     'start_time',
     'obs_segment',
     'bat_exposure',
     'xrt_exposure',
     'xrt_expo_wt',
     'xrt_expo_pc',
     'uvot_exposure']




```python
q.addCol(['cycle', 'soft_version']+q.defaultCols)
```

    Cannot add column target_id; it is already selected.
    Cannot add column ra; it is already selected.
    Cannot add column decl; it is already selected.
    Cannot add column roll_angle; it is already selected.
    Cannot add column start_time; it is already selected.
    Cannot add column obs_segment; it is already selected.
    Cannot add column bat_exposure; it is already selected.
    Cannot add column xrt_exposure; it is already selected.
    Cannot add column xrt_expo_wt; it is already selected.
    Cannot add column xrt_expo_pc; it is already selected.
    Cannot add column uvot_exposure; it is already selected.


The latter was a slightly gratuitous demonstration of a way that you can add the default columns, and some others, all in one go. We can also remove the whole lot in one go:


```python
q.removeAllCols()
q.colsToGet
```

If we were to submit this now we would not get an empty result set, but rather the default columns, which are always request if `colsToGet` is empty.

If you've been reading everything very carefully, you may be wondering why the results from our demonstration cone search contained the column `_r`, which has not appeared anywhere in the metadata or our requests. `_r` is a special column only created for cone searches, and it contains the angular distance of each row from the centre of the search. The units are whatever was given as the `units` argument to `addConeSearch()` (arcsec by default).

---

<a id='advanced'></a>
## 'Advanced' searches

'Advanced' searches are those where we select data based on filters applied to specific columns. This is actually fairly simple, we just define a series of filters to apply to the query and then submit it. These can be in addition to, or instead of the cone search. There are a few things to note before we start:

1. Filters are combined with a logical AND; that is if you define multiple filters, only rows matching all of them will be returned.
1. Each filter applies to a single column but can have two clauses, combined with AND or OR.

This will hopefully all make sense as we go on.

<a id='filters'></a>
### Filters

We add filters using the imaginatively-named `addFilter()` function, which takes a single argument, a filter definition. A filter definition can either be a `dict` or a `list` and has the following components:

* column name
* filter
* value (if applicable)
* combiner (optional)
* filter2 (optional)
* value2 (optional)

I will unpack these in more detail but an example is probably a better helper so, here are two filters created using the two approaches:


```python
filter1 = ('xrt_exposure', '>', 1000, 'OR', '<', 200)

filter2 = {
    "colName": "ra",
    "filter": ">",
    "val": 123,
    "combiner": "and" ,
    "filter2": "<",
    "val2": 200
}
```

If these filters were converted to SQL they would be written as

* filter1: `xrt_exposure>1000 OR xrt_exposure<200`
* filter2: `ra>123 AND ra<200`

And if we submitted this query they would combine as:

`(xrt_exposure>1000 OR xrt_exposure<200) AND (ra>123 AND ra<200)`

If we wanted to create a query using these filters we would do:


```python
q = uq.ObsQuery(silent=False)
q.addFilter(filter1)
q.addFilter(filter2)
```

    Resetting query details
    Need to get the metadata.


A filter doesn't have to have all of the elements we used above. You may not want the second part of the filter, so everything from `combiner` onwards can simply be omitted. Also, some of the filters do not require arguments, so in that case, `val` (or `val2`) can be left out. Conversely, the 'BETWEEN' filter requires two arguments and so `val` must take a 2-element tuple/list.

Some more examples:


```python
q.removeAllFilters()

q.addFilter ( ('xrt_exposure', '<', 2000))

q.addFilter ( ('ra', 'BETWEEN', [100,200]))

q.addFilter ({
    'colName': 'target_id',
    'filter': 'IS NULL',
    'combiner': 'or',
    'filter2': '<',
    'val2': 10000
})
```

Here I've introduced the `removeAllFilters()` function (you can probably guess what it does) and a few more examples of adding filters, including some where we don't need all elements of the filter definition.

The following values are permitted for the 'filter' and 'filter2' keys:

* "<"
* ">"
* "="
* "<="
* ">="
* "LIKE"
* "BETWEEN"
* "NOT LIKE"
* "!="
* "IS NULL"
* "IS NOT NULL"

All of these require a single value, except for 'BETWEEN', which requires 2, and 'IS NULL' and 'IS NOT NULL' which take no values.

Having added filters we can check them:



```python
q.showFilters()
```

    0:	xrt_exposure < 2000
    1:	ra BETWEEN [100, 200]
    2:	target_id IS NULL OR < 10000


The outputs as you can see are strings.

We can also remove specific filters by their index. **Please bear in mind indices will change when you remove a filter!**


```python
q.removeFilter(1)
```

    0:	xrt_exposure < 2000
    1:	target_id IS NULL OR < 10000


Because `silent=False` the above function printed out the revised set of filters, if it was `True` you'd have to do this yourself with another `showFilters()` call.

Right, enough messing around, let's do an actual query. I'm going to do both a cone and advanced search together here, just to prove you can (and to limit how many rows we get), but of course, you don't have to.


```python
q=uq.ObsQuery(silent=False)
q.addConeSearch(name='GK Per', radius=12, units='arcmin')
q.addFilter( ('xrt_exposure', '>', 3000))
q.isValid()
```

    Resetting query details
    Need to get the metadata.





    True



Here, we have created a query, requested a cone search of 12' radius, centred on "GK Per", and we have asked to only get those rows where the "xrt_exposure" field is above 3000. I also made use of a function, `isValid()`. This just checks that the syntax is OK and we haven't done anything silly. Let's submit the query:


```python
q.submit()
```

    Calling DB look-up for rows 0 -- 1000
    Resolved 'GK Per' as (52.80004119305, 43.90429720867) via SIMBAD
    Received 21 rows.


Again, because we were not silent we got some information printed, but this is also available in variables. I have already discussed accessing details of the name resolution, but how could I find out that 21 rows were returned without having to read from the screen? Like this:


```python
q.numRows
```




    21



Or indeed:


```python
len(q.results)
```




    21



if you prefer. They should be the same. And let's just prove that our filters worked:



```python
q.results
```




<div style='width: 95%; max-height: 200px; overflow: scroll;'><style scoped>    .dataframe tbody tr th:only-of-type {        vertical-align: middle;    }    .dataframe tbody tr th {        vertical-align: top;    }    .dataframe thead th {        text-align: right;    }</style><table border="1" class="dataframe">  <thead>    <tr style="text-align: right;">      <th></th>      <th>_r</th>      <th>name</th>      <th>target_id</th>      <th>ra</th>      <th>decl</th>      <th>roll_angle</th>      <th>start_time</th>      <th>stop_time</th>      <th>obs_segment</th>      <th>obsid</th>      <th>bat_exposure</th>      <th>xrt_exposure</th>      <th>xrt_expo_wt</th>      <th>xrt_expo_pc</th>      <th>uvot_exposure</th>      <th>ra_s</th>      <th>ra_apy</th>      <th>decl_s</th>      <th>decl_apy</th>    </tr>  </thead>  <tbody>    <tr>      <th>0</th>      <td>0.421999</td>      <td>GKPer</td>      <td>30842</td>      <td>52.793185</td>      <td>43.899291</td>      <td>280.915675</td>      <td>2007-01-17T03:10:01</td>      <td>2007-01-17T13:41:49</td>      <td>5</td>      <td>00030842005</td>      <td>6053</td>      <td>6078.284</td>      <td>60.784</td>      <td>6017.500</td>      <td>5862.453</td>      <td>+03h 31m 10.36s</td>      <td>52d47m35.466s</td>      <td>+43d 53m 57.4s</td>      <td>43d53m57.4476s</td>    </tr>    <tr>      <th>1</th>      <td>0.483022</td>      <td>GKPer</td>      <td>30842</td>      <td>52.811212</td>      <td>43.904125</td>      <td>284.011915</td>      <td>2007-01-09T08:32:01</td>      <td>2007-01-09T12:38:45</td>      <td>4</td>      <td>00030842004</td>      <td>4896</td>      <td>4846.696</td>      <td>25.133</td>      <td>4821.563</td>      <td>4844.257</td>      <td>+03h 31m 14.69s</td>      <td>52d48m40.3632s</td>      <td>+43d 54m 14.9s</td>      <td>43d54m14.85s</td>    </tr>    <tr>      <th>2</th>      <td>0.515095</td>      <td>GKPer</td>      <td>30842</td>      <td>52.788651</td>      <td>43.906818</td>      <td>266.451771</td>      <td>2007-02-08T03:47:01</td>      <td>2007-02-08T22:21:13</td>      <td>9</td>      <td>00030842009</td>      <td>5374</td>      <td>5278.844</td>      <td>28.914</td>      <td>5249.930</td>      <td>5271.033</td>      <td>+03h 31m 9.28s</td>      <td>52d47m19.1436s</td>      <td>+43d 54m 24.5s</td>      <td>43d54m24.5448s</td>    </tr>    <tr>      <th>3</th>      <td>0.916885</td>      <td>GKPer</td>      <td>30842</td>      <td>52.779428</td>      <td>43.907897</td>      <td>292.140501</td>      <td>2007-01-02T12:43:01</td>      <td>2007-01-02T16:47:21</td>      <td>3</td>      <td>00030842003</td>      <td>4788</td>      <td>4733.461</td>      <td>41.147</td>      <td>4692.314</td>      <td>4735.406</td>      <td>+03h 31m 7.06s</td>      <td>52d46m45.9408s</td>      <td>+43d 54m 28.4s</td>      <td>43d54m28.4292s</td>    </tr>    <tr>      <th>4</th>      <td>0.962148</td>      <td>GKPer</td>      <td>30842</td>      <td>52.778149</td>      <td>43.901410</td>      <td>269.888920</td>      <td>2007-02-04T14:50:01</td>      <td>2007-02-04T20:23:10</td>      <td>8</td>      <td>00030842008</td>      <td>4046</td>      <td>3979.563</td>      <td>43.122</td>      <td>3936.441</td>      <td>3978.030</td>      <td>+03h 31m 6.76s</td>      <td>52d46m41.3364s</td>      <td>+43d 54m 5.1s</td>      <td>43d54m05.076s</td>    </tr>    <tr>      <th>5</th>      <td>1.161197</td>      <td>GKPer</td>      <td>30842</td>      <td>52.773182</td>      <td>43.904518</td>      <td>276.237384</td>      <td>2007-01-23T02:08:01</td>      <td>2007-01-23T07:50:49</td>      <td>6</td>      <td>00030842006</td>      <td>5872</td>      <td>5806.444</td>      <td>27.112</td>      <td>5779.332</td>      <td>5804.662</td>      <td>+03h 31m 5.56s</td>      <td>52d46m23.4552s</td>      <td>+43d 54m 16.3s</td>      <td>43d54m16.2648s</td>    </tr>    <tr>      <th>6</th>      <td>1.498005</td>      <td>GK_Per</td>      <td>81445</td>      <td>52.829137</td>      <td>43.890741</td>      <td>63.483317</td>      <td>2015-09-09T09:14:58</td>      <td>2015-09-09T18:04:10</td>      <td>2</td>      <td>00081445002</td>      <td>4458</td>      <td>4419.383</td>      <td>0.040</td>      <td>4419.343</td>      <td>4350.644</td>      <td>+03h 31m 18.99s</td>      <td>52d49m44.8932s</td>      <td>+43d 53m 26.7s</td>      <td>43d53m26.6676s</td>    </tr>    <tr>      <th>7</th>      <td>1.589266</td>      <td>GKPer</td>      <td>30842</td>      <td>52.763626</td>      <td>43.900668</td>      <td>252.039706</td>      <td>2007-02-12T02:16:00</td>      <td>2007-02-12T14:23:37</td>      <td>11</td>      <td>00030842011</td>      <td>3159</td>      <td>3023.056</td>      <td>59.527</td>      <td>2963.529</td>      <td>3023.295</td>      <td>+03h 31m 3.27s</td>      <td>52d45m49.0536s</td>      <td>+43d 54m 2.4s</td>      <td>43d54m02.4048s</td>    </tr>    <tr>      <th>8</th>      <td>1.642341</td>      <td>GKPer</td>      <td>30842</td>      <td>52.770293</td>      <td>43.921326</td>      <td>308.921791</td>      <td>2006-12-20T16:12:19</td>      <td>2006-12-20T18:34:48</td>      <td>1</td>      <td>00030842001</td>      <td>4022</td>      <td>3980.145</td>      <td>33.504</td>      <td>3946.641</td>      <td>3988.765</td>      <td>+03h 31m 4.87s</td>      <td>52d46m13.0548s</td>      <td>+43d 55m 16.8s</td>      <td>43d55m16.7736s</td>    </tr>    <tr>      <th>9</th>      <td>1.798257</td>      <td>GKPer</td>      <td>30842</td>      <td>52.837858</td>      <td>43.916788</td>      <td>300.429716</td>      <td>2006-12-26T02:26:01</td>      <td>2006-12-26T08:07:50</td>      <td>2</td>      <td>00030842002</td>      <td>4607</td>      <td>4540.904</td>      <td>30.284</td>      <td>4510.620</td>      <td>4538.745</td>      <td>+03h 31m 21.09s</td>      <td>52d50m16.2888s</td>      <td>+43d 55m 0.4s</td>      <td>43d55m00.4368s</td>    </tr>    <tr>      <th>10</th>      <td>2.034272</td>      <td>GKPeroffset1</td>      <td>31653</td>      <td>52.802362</td>      <td>43.870434</td>      <td>238.001562</td>      <td>2010-04-01T02:27:00</td>      <td>2010-04-01T19:52:48</td>      <td>47</td>      <td>00031653047</td>      <td>3481</td>      <td>5341.812</td>      <td>5341.812</td>      <td>0.000</td>      <td>5288.652</td>      <td>+03h 31m 12.57s</td>      <td>52d48m08.5032s</td>      <td>+43d 52m 13.6s</td>      <td>43d52m13.5624s</td>    </tr>    <tr>      <th>11</th>      <td>2.234021</td>      <td>GKPeroffset1</td>      <td>31653</td>      <td>52.800838</td>      <td>43.867068</td>      <td>239.993197</td>      <td>2010-04-05T02:45:59</td>      <td>2010-04-05T20:13:48</td>      <td>49</td>      <td>00031653049</td>      <td>4562</td>      <td>5341.801</td>      <td>5341.801</td>      <td>0.000</td>      <td>5286.456</td>      <td>+03h 31m 12.20s</td>      <td>52d48m03.0168s</td>      <td>+43d 52m 1.4s</td>      <td>43d52m01.4448s</td>    </tr>    <tr>      <th>12</th>      <td>2.501833</td>      <td>GKPer</td>      <td>45767</td>      <td>52.743700</td>      <td>43.913840</td>      <td>249.208788</td>      <td>2013-03-20T01:02:59</td>      <td>2013-03-21T01:20:22</td>      <td>5</td>      <td>00045767005</td>      <td>4143</td>      <td>4121.740</td>      <td>63.538</td>      <td>4058.202</td>      <td>4087.774</td>      <td>+03h 30m 58.49s</td>      <td>52d44m37.32s</td>      <td>+43d 54m 49.8s</td>      <td>43d54m49.824s</td>    </tr>    <tr>      <th>13</th>      <td>2.570384</td>      <td>GKPer</td>      <td>30842</td>      <td>52.740645</td>      <td>43.906271</td>      <td>262.071536</td>      <td>2007-02-16T02:39:01</td>      <td>2007-02-16T08:20:54</td>      <td>12</td>      <td>00030842012</td>      <td>6303</td>      <td>6238.041</td>      <td>82.605</td>      <td>6155.436</td>      <td>6237.197</td>      <td>+03h 30m 57.75s</td>      <td>52d44m26.322s</td>      <td>+43d 54m 22.6s</td>      <td>43d54m22.5756s</td>    </tr>    <tr>      <th>14</th>      <td>2.606862</td>      <td>GKPer</td>      <td>30842</td>      <td>52.745736</td>      <td>43.923199</td>      <td>253.806039</td>      <td>2007-03-13T00:29:01</td>      <td>2007-03-13T11:01:02</td>      <td>19</td>      <td>00030842019</td>      <td>6106</td>      <td>5969.147</td>      <td>78.192</td>      <td>5890.955</td>      <td>5981.222</td>      <td>+03h 30m 58.98s</td>      <td>52d44m44.6496s</td>      <td>+43d 55m 23.5s</td>      <td>43d55m23.5164s</td>    </tr>    <tr>      <th>15</th>      <td>2.802018</td>      <td>GKPer</td>      <td>30842</td>      <td>52.745146</td>      <td>43.929141</td>      <td>260.414911</td>      <td>2007-02-26T00:25:01</td>      <td>2007-02-26T06:08:24</td>      <td>15</td>      <td>00030842015</td>      <td>6488</td>      <td>6403.276</td>      <td>32.808</td>      <td>6370.468</td>      <td>6418.423</td>      <td>+03h 30m 58.84s</td>      <td>52d44m42.5256s</td>      <td>+43d 55m 44.9s</td>      <td>43d55m44.9076s</td>    </tr>    <tr>      <th>16</th>      <td>2.875683</td>      <td>GKPer</td>      <td>30842</td>      <td>52.734551</td>      <td>43.912719</td>      <td>261.255083</td>      <td>2007-02-23T00:06:01</td>      <td>2007-02-23T02:36:36</td>      <td>14</td>      <td>00030842014</td>      <td>3277</td>      <td>3244.444</td>      <td>5.008</td>      <td>3239.436</td>      <td>3243.491</td>      <td>+03h 30m 56.29s</td>      <td>52d44m04.3836s</td>      <td>+43d 54m 45.8s</td>      <td>43d54m45.7884s</td>    </tr>    <tr>      <th>17</th>      <td>2.940585</td>      <td>GKPer</td>      <td>30842</td>      <td>52.732920</td>      <td>43.912266</td>      <td>255.973292</td>      <td>2007-03-06T04:39:01</td>      <td>2007-03-06T14:14:01</td>      <td>17</td>      <td>00030842017</td>      <td>7951</td>      <td>7846.457</td>      <td>51.297</td>      <td>7795.160</td>      <td>7848.622</td>      <td>+03h 30m 55.90s</td>      <td>52d43m58.512s</td>      <td>+43d 54m 44.2s</td>      <td>43d54m44.1576s</td>    </tr>    <tr>      <th>18</th>      <td>3.344602</td>      <td>GKPer</td>      <td>30842</td>      <td>52.726982</td>      <td>43.922663</td>      <td>254.061770</td>      <td>2007-03-09T00:16:01</td>      <td>2007-03-09T23:26:23</td>      <td>18</td>      <td>00030842018</td>      <td>4570</td>      <td>4311.634</td>      <td>111.419</td>      <td>4200.215</td>      <td>4228.598</td>      <td>+03h 30m 54.48s</td>      <td>52d43m37.1352s</td>      <td>+43d 55m 21.6s</td>      <td>43d55m21.5868s</td>    </tr>    <tr>      <th>19</th>      <td>3.541167</td>      <td>GKPer</td>      <td>30842</td>      <td>52.718735</td>      <td>43.897146</td>      <td>242.945235</td>      <td>2007-03-02T12:04:01</td>      <td>2007-03-02T22:36:04</td>      <td>16</td>      <td>00030842016</td>      <td>3410</td>      <td>3261.669</td>      <td>118.117</td>      <td>3143.552</td>      <td>3288.439</td>      <td>+03h 30m 52.50s</td>      <td>52d43m07.446s</td>      <td>+43d 53m 49.7s</td>      <td>43d53m49.7256s</td>    </tr>    <tr>      <th>20</th>      <td>5.582058</td>      <td>GKPer</td>      <td>30842</td>      <td>52.878237</td>      <td>43.978359</td>      <td>50.625546</td>      <td>2007-09-27T14:04:00</td>      <td>2007-09-28T01:29:45</td>      <td>20</td>      <td>00030842020</td>      <td>3089</td>      <td>3010.216</td>      <td>0.000</td>      <td>3010.216</td>      <td>0.000</td>      <td>+03h 31m 30.78s</td>      <td>52d52m41.6532s</td>      <td>+43d 58m 42.1s</td>      <td>43d58m42.0924s</td>    </tr>  </tbody></table></div>


<a id='extra'></a>
## Extra query settings

There are one or two further things to discuss: sorting the results, and controlling how many rows we get. Both of these can be done after the query is complete using `pandas` functions, or they can be done at query time. Let's start with sorting.

<a id='sorting'></a>
### Sorting results

By default, if you did a cone search the results are ordered by increasing distance from the cone centre. If you didn't do a cone search, they are ordered by however they come out of the database. To control this sorting, we use two variables in our class `sortCol` and `sortDir`. The former is the name of a column in the table (which we can get via `q.metadata`, as above), the latter is either "ASC" or "DESC", (for ascending or descending).

Let's have a quick demo, and while I'm here I'll show you that you can unlock a query, rather than fully resetting it, if you just want to change something and resubmit:


```python
q.unlock()
q.sortCol='xrt_exposure'
q.sortDir='DESC'
q.submit()
q.results
```

    Calling DB look-up for rows 0 -- 1000
    Resolved 'GK Per' as (52.80004119305, 43.90429720867) via SIMBAD
    Received 21 rows.





<div style='width: 95%; max-height: 200px; overflow: scroll;'><style scoped>    .dataframe tbody tr th:only-of-type {        vertical-align: middle;    }    .dataframe tbody tr th {        vertical-align: top;    }    .dataframe thead th {        text-align: right;    }</style><table border="1" class="dataframe">  <thead>    <tr style="text-align: right;">      <th></th>      <th>_r</th>      <th>name</th>      <th>target_id</th>      <th>ra</th>      <th>decl</th>      <th>roll_angle</th>      <th>start_time</th>      <th>stop_time</th>      <th>obs_segment</th>      <th>obsid</th>      <th>bat_exposure</th>      <th>xrt_exposure</th>      <th>xrt_expo_wt</th>      <th>xrt_expo_pc</th>      <th>uvot_exposure</th>      <th>ra_s</th>      <th>ra_apy</th>      <th>decl_s</th>      <th>decl_apy</th>    </tr>  </thead>  <tbody>    <tr>      <th>0</th>      <td>2.940585</td>      <td>GKPer</td>      <td>30842</td>      <td>52.732920</td>      <td>43.912266</td>      <td>255.973292</td>      <td>2007-03-06T04:39:01</td>      <td>2007-03-06T14:14:01</td>      <td>17</td>      <td>00030842017</td>      <td>7951</td>      <td>7846.457</td>      <td>51.297</td>      <td>7795.160</td>      <td>7848.622</td>      <td>+03h 30m 55.90s</td>      <td>52d43m58.512s</td>      <td>+43d 54m 44.2s</td>      <td>43d54m44.1576s</td>    </tr>    <tr>      <th>1</th>      <td>2.802018</td>      <td>GKPer</td>      <td>30842</td>      <td>52.745146</td>      <td>43.929141</td>      <td>260.414911</td>      <td>2007-02-26T00:25:01</td>      <td>2007-02-26T06:08:24</td>      <td>15</td>      <td>00030842015</td>      <td>6488</td>      <td>6403.276</td>      <td>32.808</td>      <td>6370.468</td>      <td>6418.423</td>      <td>+03h 30m 58.84s</td>      <td>52d44m42.5256s</td>      <td>+43d 55m 44.9s</td>      <td>43d55m44.9076s</td>    </tr>    <tr>      <th>2</th>      <td>2.570384</td>      <td>GKPer</td>      <td>30842</td>      <td>52.740645</td>      <td>43.906271</td>      <td>262.071536</td>      <td>2007-02-16T02:39:01</td>      <td>2007-02-16T08:20:54</td>      <td>12</td>      <td>00030842012</td>      <td>6303</td>      <td>6238.041</td>      <td>82.605</td>      <td>6155.436</td>      <td>6237.197</td>      <td>+03h 30m 57.75s</td>      <td>52d44m26.322s</td>      <td>+43d 54m 22.6s</td>      <td>43d54m22.5756s</td>    </tr>    <tr>      <th>3</th>      <td>0.421999</td>      <td>GKPer</td>      <td>30842</td>      <td>52.793185</td>      <td>43.899291</td>      <td>280.915675</td>      <td>2007-01-17T03:10:01</td>      <td>2007-01-17T13:41:49</td>      <td>5</td>      <td>00030842005</td>      <td>6053</td>      <td>6078.284</td>      <td>60.784</td>      <td>6017.500</td>      <td>5862.453</td>      <td>+03h 31m 10.36s</td>      <td>52d47m35.466s</td>      <td>+43d 53m 57.4s</td>      <td>43d53m57.4476s</td>    </tr>    <tr>      <th>4</th>      <td>2.606862</td>      <td>GKPer</td>      <td>30842</td>      <td>52.745736</td>      <td>43.923199</td>      <td>253.806039</td>      <td>2007-03-13T00:29:01</td>      <td>2007-03-13T11:01:02</td>      <td>19</td>      <td>00030842019</td>      <td>6106</td>      <td>5969.147</td>      <td>78.192</td>      <td>5890.955</td>      <td>5981.222</td>      <td>+03h 30m 58.98s</td>      <td>52d44m44.6496s</td>      <td>+43d 55m 23.5s</td>      <td>43d55m23.5164s</td>    </tr>    <tr>      <th>5</th>      <td>1.161197</td>      <td>GKPer</td>      <td>30842</td>      <td>52.773182</td>      <td>43.904518</td>      <td>276.237384</td>      <td>2007-01-23T02:08:01</td>      <td>2007-01-23T07:50:49</td>      <td>6</td>      <td>00030842006</td>      <td>5872</td>      <td>5806.444</td>      <td>27.112</td>      <td>5779.332</td>      <td>5804.662</td>      <td>+03h 31m 5.56s</td>      <td>52d46m23.4552s</td>      <td>+43d 54m 16.3s</td>      <td>43d54m16.2648s</td>    </tr>    <tr>      <th>6</th>      <td>2.034272</td>      <td>GKPeroffset1</td>      <td>31653</td>      <td>52.802362</td>      <td>43.870434</td>      <td>238.001562</td>      <td>2010-04-01T02:27:00</td>      <td>2010-04-01T19:52:48</td>      <td>47</td>      <td>00031653047</td>      <td>3481</td>      <td>5341.812</td>      <td>5341.812</td>      <td>0.000</td>      <td>5288.652</td>      <td>+03h 31m 12.57s</td>      <td>52d48m08.5032s</td>      <td>+43d 52m 13.6s</td>      <td>43d52m13.5624s</td>    </tr>    <tr>      <th>7</th>      <td>2.234021</td>      <td>GKPeroffset1</td>      <td>31653</td>      <td>52.800838</td>      <td>43.867068</td>      <td>239.993197</td>      <td>2010-04-05T02:45:59</td>      <td>2010-04-05T20:13:48</td>      <td>49</td>      <td>00031653049</td>      <td>4562</td>      <td>5341.801</td>      <td>5341.801</td>      <td>0.000</td>      <td>5286.456</td>      <td>+03h 31m 12.20s</td>      <td>52d48m03.0168s</td>      <td>+43d 52m 1.4s</td>      <td>43d52m01.4448s</td>    </tr>    <tr>      <th>8</th>      <td>0.515095</td>      <td>GKPer</td>      <td>30842</td>      <td>52.788651</td>      <td>43.906818</td>      <td>266.451771</td>      <td>2007-02-08T03:47:01</td>      <td>2007-02-08T22:21:13</td>      <td>9</td>      <td>00030842009</td>      <td>5374</td>      <td>5278.844</td>      <td>28.914</td>      <td>5249.930</td>      <td>5271.033</td>      <td>+03h 31m 9.28s</td>      <td>52d47m19.1436s</td>      <td>+43d 54m 24.5s</td>      <td>43d54m24.5448s</td>    </tr>    <tr>      <th>9</th>      <td>0.483022</td>      <td>GKPer</td>      <td>30842</td>      <td>52.811212</td>      <td>43.904125</td>      <td>284.011915</td>      <td>2007-01-09T08:32:01</td>      <td>2007-01-09T12:38:45</td>      <td>4</td>      <td>00030842004</td>      <td>4896</td>      <td>4846.696</td>      <td>25.133</td>      <td>4821.563</td>      <td>4844.257</td>      <td>+03h 31m 14.69s</td>      <td>52d48m40.3632s</td>      <td>+43d 54m 14.9s</td>      <td>43d54m14.85s</td>    </tr>    <tr>      <th>10</th>      <td>0.916885</td>      <td>GKPer</td>      <td>30842</td>      <td>52.779428</td>      <td>43.907897</td>      <td>292.140501</td>      <td>2007-01-02T12:43:01</td>      <td>2007-01-02T16:47:21</td>      <td>3</td>      <td>00030842003</td>      <td>4788</td>      <td>4733.461</td>      <td>41.147</td>      <td>4692.314</td>      <td>4735.406</td>      <td>+03h 31m 7.06s</td>      <td>52d46m45.9408s</td>      <td>+43d 54m 28.4s</td>      <td>43d54m28.4292s</td>    </tr>    <tr>      <th>11</th>      <td>1.798257</td>      <td>GKPer</td>      <td>30842</td>      <td>52.837858</td>      <td>43.916788</td>      <td>300.429716</td>      <td>2006-12-26T02:26:01</td>      <td>2006-12-26T08:07:50</td>      <td>2</td>      <td>00030842002</td>      <td>4607</td>      <td>4540.904</td>      <td>30.284</td>      <td>4510.620</td>      <td>4538.745</td>      <td>+03h 31m 21.09s</td>      <td>52d50m16.2888s</td>      <td>+43d 55m 0.4s</td>      <td>43d55m00.4368s</td>    </tr>    <tr>      <th>12</th>      <td>1.498005</td>      <td>GK_Per</td>      <td>81445</td>      <td>52.829137</td>      <td>43.890741</td>      <td>63.483317</td>      <td>2015-09-09T09:14:58</td>      <td>2015-09-09T18:04:10</td>      <td>2</td>      <td>00081445002</td>      <td>4458</td>      <td>4419.383</td>      <td>0.040</td>      <td>4419.343</td>      <td>4350.644</td>      <td>+03h 31m 18.99s</td>      <td>52d49m44.8932s</td>      <td>+43d 53m 26.7s</td>      <td>43d53m26.6676s</td>    </tr>    <tr>      <th>13</th>      <td>3.344602</td>      <td>GKPer</td>      <td>30842</td>      <td>52.726982</td>      <td>43.922663</td>      <td>254.061770</td>      <td>2007-03-09T00:16:01</td>      <td>2007-03-09T23:26:23</td>      <td>18</td>      <td>00030842018</td>      <td>4570</td>      <td>4311.634</td>      <td>111.419</td>      <td>4200.215</td>      <td>4228.598</td>      <td>+03h 30m 54.48s</td>      <td>52d43m37.1352s</td>      <td>+43d 55m 21.6s</td>      <td>43d55m21.5868s</td>    </tr>    <tr>      <th>14</th>      <td>2.501833</td>      <td>GKPer</td>      <td>45767</td>      <td>52.743700</td>      <td>43.913840</td>      <td>249.208788</td>      <td>2013-03-20T01:02:59</td>      <td>2013-03-21T01:20:22</td>      <td>5</td>      <td>00045767005</td>      <td>4143</td>      <td>4121.740</td>      <td>63.538</td>      <td>4058.202</td>      <td>4087.774</td>      <td>+03h 30m 58.49s</td>      <td>52d44m37.32s</td>      <td>+43d 54m 49.8s</td>      <td>43d54m49.824s</td>    </tr>    <tr>      <th>15</th>      <td>1.642341</td>      <td>GKPer</td>      <td>30842</td>      <td>52.770293</td>      <td>43.921326</td>      <td>308.921791</td>      <td>2006-12-20T16:12:19</td>      <td>2006-12-20T18:34:48</td>      <td>1</td>      <td>00030842001</td>      <td>4022</td>      <td>3980.145</td>      <td>33.504</td>      <td>3946.641</td>      <td>3988.765</td>      <td>+03h 31m 4.87s</td>      <td>52d46m13.0548s</td>      <td>+43d 55m 16.8s</td>      <td>43d55m16.7736s</td>    </tr>    <tr>      <th>16</th>      <td>0.962148</td>      <td>GKPer</td>      <td>30842</td>      <td>52.778149</td>      <td>43.901410</td>      <td>269.888920</td>      <td>2007-02-04T14:50:01</td>      <td>2007-02-04T20:23:10</td>      <td>8</td>      <td>00030842008</td>      <td>4046</td>      <td>3979.563</td>      <td>43.122</td>      <td>3936.441</td>      <td>3978.030</td>      <td>+03h 31m 6.76s</td>      <td>52d46m41.3364s</td>      <td>+43d 54m 5.1s</td>      <td>43d54m05.076s</td>    </tr>    <tr>      <th>17</th>      <td>3.541167</td>      <td>GKPer</td>      <td>30842</td>      <td>52.718735</td>      <td>43.897146</td>      <td>242.945235</td>      <td>2007-03-02T12:04:01</td>      <td>2007-03-02T22:36:04</td>      <td>16</td>      <td>00030842016</td>      <td>3410</td>      <td>3261.669</td>      <td>118.117</td>      <td>3143.552</td>      <td>3288.439</td>      <td>+03h 30m 52.50s</td>      <td>52d43m07.446s</td>      <td>+43d 53m 49.7s</td>      <td>43d53m49.7256s</td>    </tr>    <tr>      <th>18</th>      <td>2.875683</td>      <td>GKPer</td>      <td>30842</td>      <td>52.734551</td>      <td>43.912719</td>      <td>261.255083</td>      <td>2007-02-23T00:06:01</td>      <td>2007-02-23T02:36:36</td>      <td>14</td>      <td>00030842014</td>      <td>3277</td>      <td>3244.444</td>      <td>5.008</td>      <td>3239.436</td>      <td>3243.491</td>      <td>+03h 30m 56.29s</td>      <td>52d44m04.3836s</td>      <td>+43d 54m 45.8s</td>      <td>43d54m45.7884s</td>    </tr>    <tr>      <th>19</th>      <td>1.589266</td>      <td>GKPer</td>      <td>30842</td>      <td>52.763626</td>      <td>43.900668</td>      <td>252.039706</td>      <td>2007-02-12T02:16:00</td>      <td>2007-02-12T14:23:37</td>      <td>11</td>      <td>00030842011</td>      <td>3159</td>      <td>3023.056</td>      <td>59.527</td>      <td>2963.529</td>      <td>3023.295</td>      <td>+03h 31m 3.27s</td>      <td>52d45m49.0536s</td>      <td>+43d 54m 2.4s</td>      <td>43d54m02.4048s</td>    </tr>    <tr>      <th>20</th>      <td>5.582058</td>      <td>GKPer</td>      <td>30842</td>      <td>52.878237</td>      <td>43.978359</td>      <td>50.625546</td>      <td>2007-09-27T14:04:00</td>      <td>2007-09-28T01:29:45</td>      <td>20</td>      <td>00030842020</td>      <td>3089</td>      <td>3010.216</td>      <td>0.000</td>      <td>3010.216</td>      <td>0.000</td>      <td>+03h 31m 30.78s</td>      <td>52d52m41.6532s</td>      <td>+43d 58m 42.1s</td>      <td>43d58m42.0924s</td>    </tr>  </tbody></table></div>


As you can see, this time, the results are ordered by the "xrt_exposure" column, in descending order. Incidentally, you don't have to actually retrieve the column you sort on, if you don't want to!

<a id='numrows'></a>

### How many rows to get

The default behaviour of this module is to get all rows in the database that match your query. This can be a lot, and maybe you don't want them all. You can limit how many are returned using the `maxRows` variable:


```python
q.unlock()
q.maxRows=3
q.submit()
```

    Calling DB look-up for rows 0 -- 3
    Resolved 'GK Per' as (52.80004119305, 43.90429720867) via SIMBAD
    Received 3 rows.


This returned us the top three rows matching our query - and note that as we have (just a moment ago) said that our results should be ordered by descending XRT exposure, we should have got the three observations with the longest exposures.


```python
q.results
```




<div style='width: 95%; max-height: 200px; overflow: scroll;'><style scoped>    .dataframe tbody tr th:only-of-type {        vertical-align: middle;    }    .dataframe tbody tr th {        vertical-align: top;    }    .dataframe thead th {        text-align: right;    }</style><table border="1" class="dataframe">  <thead>    <tr style="text-align: right;">      <th></th>      <th>_r</th>      <th>name</th>      <th>target_id</th>      <th>ra</th>      <th>decl</th>      <th>roll_angle</th>      <th>start_time</th>      <th>stop_time</th>      <th>obs_segment</th>      <th>obsid</th>      <th>bat_exposure</th>      <th>xrt_exposure</th>      <th>xrt_expo_wt</th>      <th>xrt_expo_pc</th>      <th>uvot_exposure</th>      <th>ra_s</th>      <th>ra_apy</th>      <th>decl_s</th>      <th>decl_apy</th>    </tr>  </thead>  <tbody>    <tr>      <th>0</th>      <td>2.940585</td>      <td>GKPer</td>      <td>30842</td>      <td>52.732920</td>      <td>43.912266</td>      <td>255.973292</td>      <td>2007-03-06T04:39:01</td>      <td>2007-03-06T14:14:01</td>      <td>17</td>      <td>00030842017</td>      <td>7951</td>      <td>7846.457</td>      <td>51.297</td>      <td>7795.160</td>      <td>7848.622</td>      <td>+03h 30m 55.90s</td>      <td>52d43m58.512s</td>      <td>+43d 54m 44.2s</td>      <td>43d54m44.1576s</td>    </tr>    <tr>      <th>1</th>      <td>2.802018</td>      <td>GKPer</td>      <td>30842</td>      <td>52.745146</td>      <td>43.929141</td>      <td>260.414911</td>      <td>2007-02-26T00:25:01</td>      <td>2007-02-26T06:08:24</td>      <td>15</td>      <td>00030842015</td>      <td>6488</td>      <td>6403.276</td>      <td>32.808</td>      <td>6370.468</td>      <td>6418.423</td>      <td>+03h 30m 58.84s</td>      <td>52d44m42.5256s</td>      <td>+43d 55m 44.9s</td>      <td>43d55m44.9076s</td>    </tr>    <tr>      <th>2</th>      <td>2.570384</td>      <td>GKPer</td>      <td>30842</td>      <td>52.740645</td>      <td>43.906271</td>      <td>262.071536</td>      <td>2007-02-16T02:39:01</td>      <td>2007-02-16T08:20:54</td>      <td>12</td>      <td>00030842012</td>      <td>6303</td>      <td>6238.041</td>      <td>82.605</td>      <td>6155.436</td>      <td>6237.197</td>      <td>+03h 30m 57.75s</td>      <td>52d44m26.322s</td>      <td>+43d 54m 22.6s</td>      <td>43d54m22.5756s</td>    </tr>  </tbody></table></div>


We did!

I said a moment ago that by default *all* matching rows are returned, and this is true. Some of you may be wondering why, therefore, the output above repeatedly says: "Calling DB look-up for rows 0 -- 1000" (if you are not wondering this, skip to the next section). Was I lying about getting all rows?

No, I wasn't, and in general what I'm about to say won't matter, but it's here to satisfy your curiosity.

There is a limit to the amount of server resources a single query can consume. In practice this means that if you request some enormous query with lots of rows, the query will be terminated because it uses more memory than is permitted and you will get some unhelpful error (probably an HTTP 500 error). To avoid this, the Python module will never ask for more than 1,000 rows at a time. But this doesn't mean that you only get 1,000 rows; it just means that the Python back end will get your results in chunks, requesting the first 1,000 rows and then (if necessary) the next 1,000 etc., giving (non-silent) output such as:

Calling DB look-up for rows 0 -- 1000
Calling DB look-up for rows 1001 -- 2000
Calling DB look-up for rows 2001 -- 3000

The results of these calls will be stitched together for you and this entire process would be completely invisible if we hadn't said `silent=False`.

---

<a id='prods'></a>
## Retrieving products from a query

Having identified observations using a query, you may wish to download them. You can do this by calling the `downloadObsData()` function. This is literally just a wrapper the function of the same name in [the `data` module](data.md) and as already warned, I'm not going to redocument that here. Arguments are passed through to `data.downloadObsData()` as `**kwargs`, with just three exceptions. These exceptions apply to almost every data product function provided throughout the `query` module, so I will refer back to this section a few times on subsequent page. These exceptions are:

* You do not specify `silent` and `verbose`; these are properties of your query object, and are set from them.
* You do not supply the identifier of the object(s) you want the products for; the products are retrieved for the objects in your query's `results` table.
* There is an optional `subset` argument, which lets you specify a subset of the `results` table for which you want data products.

This last point we will return to [in a moment](#subsets)

First, let's do a simple demonstration of this. I will deliberately execute a query that doesn't get too many rows.


```python
q = uq.ObsQuery(silent=False)
q.addConeSearch(name='GRB 210205A', radius=300)
q.submit()
q.results
```

    Resetting query details
    Need to get the metadata to check the query is valid.
    Calling DB look-up for rows 0 -- 1000
    Resolved 'GRB 210205A' as (347.219333, 56.296528) via SIMBAD
    Received 2 rows.





<div style='width: 95%; max-height: 200px; overflow: scroll;'><style scoped>    .dataframe tbody tr th:only-of-type {        vertical-align: middle;    }    .dataframe tbody tr th {        vertical-align: top;    }    .dataframe thead th {        text-align: right;    }</style><table border="1" class="dataframe">  <thead>    <tr style="text-align: right;">      <th></th>      <th>_r</th>      <th>name</th>      <th>target_id</th>      <th>ra</th>      <th>decl</th>      <th>roll_angle</th>      <th>start_time</th>      <th>stop_time</th>      <th>obs_segment</th>      <th>obsid</th>      <th>bat_exposure</th>      <th>xrt_exposure</th>      <th>xrt_expo_wt</th>      <th>xrt_expo_pc</th>      <th>uvot_exposure</th>      <th>ra_s</th>      <th>ra_apy</th>      <th>decl_s</th>      <th>decl_apy</th>    </tr>  </thead>  <tbody>    <tr>      <th>0</th>      <td>84.722734</td>      <td>Burst (347.221, 56.294)</td>      <td>1030629</td>      <td>347.229229</td>      <td>56.319413</td>      <td>197.285029</td>      <td>2021-02-05T13:54:35</td>      <td>2021-02-05T22:16:56</td>      <td>1</td>      <td>01030629001</td>      <td>7906.000</td>      <td>7866.813</td>      <td>0.00</td>      <td>7866.813</td>      <td>7786.218</td>      <td>+23h 08m 55.01s</td>      <td>347d13m45.2244s</td>      <td>+56d 19m 9.9s</td>      <td>56d19m09.8868s</td>    </tr>    <tr>      <th>1</th>      <td>158.399615</td>      <td>Burst (347.221, 56.294)</td>      <td>1030629</td>      <td>347.274472</td>      <td>56.328161</td>      <td>207.713073</td>      <td>2021-02-05T10:53:19</td>      <td>2021-02-05T12:40:56</td>      <td>0</td>      <td>01030629000</td>      <td>4833.061</td>      <td>1725.085</td>      <td>5.02</td>      <td>1714.987</td>      <td>1686.866</td>      <td>+23h 09m 5.87s</td>      <td>347d16m28.0992s</td>      <td>+56d 19m 41.4s</td>      <td>56d19m41.3796s</td>    </tr>  </tbody></table></div>


As you can see, this gave us two rows, and we can save the observations simply enough.


```python
q.downloadObsData(destDir='/tmp/APIDemo_download1',
                 instruments=('BAT', 'XRT'),
                 getTDRSS=True)
```

    Making directory /tmp/APIDemo_download1
    Downloading 2 datasets
    Making directory /tmp/APIDemo_download1/01030629001
    Making directory /tmp/APIDemo_download1/01030629001/bat/
    Making directory /tmp/APIDemo_download1/01030629001/bat/hk/
    Making directory /tmp/APIDemo_download1/01030629001/bat/masktag/
    Making directory /tmp/APIDemo_download1/01030629001/bat/rate/
    Making directory /tmp/APIDemo_download1/01030629001/bat/survey/
    Making directory /tmp/APIDemo_download1/01030629001/xrt/
    Making directory /tmp/APIDemo_download1/01030629001/xrt/event/
    Making directory /tmp/APIDemo_download1/01030629001/xrt/hk/
    Making directory /tmp/APIDemo_download1/01030629001/auxil/



    Downloading 01030629001:   0%|          | 0/46 [00:00<?, ?files/s]


    Making directory /tmp/APIDemo_download1/01030629000
    Making directory /tmp/APIDemo_download1/01030629000/bat/
    Making directory /tmp/APIDemo_download1/01030629000/bat/event/
    Making directory /tmp/APIDemo_download1/01030629000/bat/hk/
    Making directory /tmp/APIDemo_download1/01030629000/bat/masktag/
    Making directory /tmp/APIDemo_download1/01030629000/bat/products/
    Making directory /tmp/APIDemo_download1/01030629000/bat/rate/
    Making directory /tmp/APIDemo_download1/01030629000/bat/survey/
    Making directory /tmp/APIDemo_download1/01030629000/xrt/
    Making directory /tmp/APIDemo_download1/01030629000/xrt/event/
    Making directory /tmp/APIDemo_download1/01030629000/xrt/hk/
    Making directory /tmp/APIDemo_download1/01030629000/auxil/
    Making directory /tmp/APIDemo_download1/01030629000/tdrss/



    Downloading 01030629000:   0%|          | 0/90 [00:00<?, ?files/s]


The arguments I supplied to `downloadObsData()` are the standard arguments for `data.downloadObsData()` which are [documented here](data.md#obsid).

One thing that is worth noting is that, since `downloadObsData()` uses the observation identifier to work out which data you are asking for, if your query did not retrieve the relevant column, this function would fail. If you are manually selecting columns and want to ensure you have the necessary column you can always look at the metadata (described above). If the table in question contains observation identifiers then the metadata will include "IsObsCol", which will be 1 for the relevant column.

<a id='subsets'></a>
### Getting products for only some rows

After performing a query you may realise that you don't want to get data for all of the rows, but only some of them. You could repeat the query, of course, with extra filtering, but this would be a bit wasteful. The `subset` parameter solves this; it exists for all functions for getting products via the `query` module, and allows you to define a subset of rows for which products should be retrieved.

The argument itself takes a `pandas Series` of `bool`s, identifying the rows, which sounds complicated, but actually you just need to give it a `pandas` filter expression. It is beyond the scope of this documentation to describe those in detail, but the examples below should give you a primer.

First, I'm going to do a cone search around GK Per, ordering by exposure (longest first)


```python
q = uq.ObsQuery(silent=False)
q.addConeSearch(name='GK Per', radius=300)
q.sortCol = 'xrt_exposure'
q.sortDir='DESC'
q.submit()
q.results
```

    Resetting query details
    Need to get the metadata.
    Calling DB look-up for rows 0 -- 1000
    Resolved 'GK Per' as (52.80004119305, 43.90429720867) via SIMBAD
    Received 145 rows.





<div style='width: 95%; max-height: 200px; overflow: scroll;'><style scoped>    .dataframe tbody tr th:only-of-type {        vertical-align: middle;    }    .dataframe tbody tr th {        vertical-align: top;    }    .dataframe thead th {        text-align: right;    }</style><table border="1" class="dataframe">  <thead>    <tr style="text-align: right;">      <th></th>      <th>_r</th>      <th>name</th>      <th>target_id</th>      <th>ra</th>      <th>decl</th>      <th>roll_angle</th>      <th>start_time</th>      <th>stop_time</th>      <th>obs_segment</th>      <th>obsid</th>      <th>bat_exposure</th>      <th>xrt_exposure</th>      <th>xrt_expo_wt</th>      <th>xrt_expo_pc</th>      <th>uvot_exposure</th>      <th>ra_s</th>      <th>ra_apy</th>      <th>decl_s</th>      <th>decl_apy</th>    </tr>  </thead>  <tbody>    <tr>      <th>0</th>      <td>176.435074</td>      <td>GKPer</td>      <td>30842</td>      <td>52.732920</td>      <td>43.912266</td>      <td>255.973292</td>      <td>2007-03-06T04:39:01</td>      <td>2007-03-06T14:14:01</td>      <td>17</td>      <td>00030842017</td>      <td>7951</td>      <td>7846.457</td>      <td>51.297</td>      <td>7795.160</td>      <td>7848.622</td>      <td>+03h 30m 55.90s</td>      <td>52d43m58.512s</td>      <td>+43d 54m 44.2s</td>      <td>43d54m44.1576s</td>    </tr>    <tr>      <th>1</th>      <td>168.121066</td>      <td>GKPer</td>      <td>30842</td>      <td>52.745146</td>      <td>43.929141</td>      <td>260.414911</td>      <td>2007-02-26T00:25:01</td>      <td>2007-02-26T06:08:24</td>      <td>15</td>      <td>00030842015</td>      <td>6488</td>      <td>6403.276</td>      <td>32.808</td>      <td>6370.468</td>      <td>6418.423</td>      <td>+03h 30m 58.84s</td>      <td>52d44m42.5256s</td>      <td>+43d 55m 44.9s</td>      <td>43d55m44.9076s</td>    </tr>    <tr>      <th>2</th>      <td>154.223024</td>      <td>GKPer</td>      <td>30842</td>      <td>52.740645</td>      <td>43.906271</td>      <td>262.071536</td>      <td>2007-02-16T02:39:01</td>      <td>2007-02-16T08:20:54</td>      <td>12</td>      <td>00030842012</td>      <td>6303</td>      <td>6238.041</td>      <td>82.605</td>      <td>6155.436</td>      <td>6237.197</td>      <td>+03h 30m 57.75s</td>      <td>52d44m26.322s</td>      <td>+43d 54m 22.6s</td>      <td>43d54m22.5756s</td>    </tr>    <tr>      <th>3</th>      <td>25.319939</td>      <td>GKPer</td>      <td>30842</td>      <td>52.793185</td>      <td>43.899291</td>      <td>280.915675</td>      <td>2007-01-17T03:10:01</td>      <td>2007-01-17T13:41:49</td>      <td>5</td>      <td>00030842005</td>      <td>6053</td>      <td>6078.284</td>      <td>60.784</td>      <td>6017.500</td>      <td>5862.453</td>      <td>+03h 31m 10.36s</td>      <td>52d47m35.466s</td>      <td>+43d 53m 57.4s</td>      <td>43d53m57.4476s</td>    </tr>    <tr>      <th>4</th>      <td>156.411729</td>      <td>GKPer</td>      <td>30842</td>      <td>52.745736</td>      <td>43.923199</td>      <td>253.806039</td>      <td>2007-03-13T00:29:01</td>      <td>2007-03-13T11:01:02</td>      <td>19</td>      <td>00030842019</td>      <td>6106</td>      <td>5969.147</td>      <td>78.192</td>      <td>5890.955</td>      <td>5981.222</td>      <td>+03h 30m 58.98s</td>      <td>52d44m44.6496s</td>      <td>+43d 55m 23.5s</td>      <td>43d55m23.5164s</td>    </tr>    <tr>      <th>...</th>      <td>...</td>      <td>...</td>      <td>...</td>      <td>...</td>      <td>...</td>      <td>...</td>      <td>...</td>      <td>...</td>      <td>...</td>      <td>...</td>      <td>...</td>      <td>...</td>      <td>...</td>      <td>...</td>      <td>...</td>      <td>...</td>      <td>...</td>      <td>...</td>      <td>...</td>    </tr>    <tr>      <th>140</th>      <td>105.896403</td>      <td>GKPeroffset1</td>      <td>31653</td>      <td>52.809250</td>      <td>43.875640</td>      <td>239.062783</td>      <td>2010-03-22T22:23:00</td>      <td>2010-03-22T23:17:16</td>      <td>32</td>      <td>00031653032</td>      <td>0</td>      <td>42.338</td>      <td>4.109</td>      <td>38.229</td>      <td>42.565</td>      <td>+03h 31m 14.22s</td>      <td>52d48m33.3s</td>      <td>+43d 52m 32.3s</td>      <td>43d52m32.304s</td>    </tr>    <tr>      <th>141</th>      <td>17.510511</td>      <td>GKPeroffset1</td>      <td>31653</td>      <td>52.793651</td>      <td>43.905866</td>      <td>239.071668</td>      <td>2010-03-12T11:49:59</td>      <td>2010-03-12T12:44:19</td>      <td>11</td>      <td>00031653011</td>      <td>301</td>      <td>39.563</td>      <td>1.963</td>      <td>37.600</td>      <td>39.575</td>      <td>+03h 31m 10.48s</td>      <td>52d47m37.1436s</td>      <td>+43d 54m 21.1s</td>      <td>43d54m21.1176s</td>    </tr>    <tr>      <th>142</th>      <td>116.995543</td>      <td>GKPer</td>      <td>30842</td>      <td>52.833519</td>      <td>43.926082</td>      <td>255.065851</td>      <td>2010-03-09T00:08:00</td>      <td>2010-03-09T01:01:34</td>      <td>26</td>      <td>00030842026</td>      <td>300</td>      <td>26.660</td>      <td>4.104</td>      <td>22.556</td>      <td>24.239</td>      <td>+03h 31m 20.04s</td>      <td>52d50m00.6684s</td>      <td>+43d 55m 33.9s</td>      <td>43d55m33.8952s</td>    </tr>    <tr>      <th>143</th>      <td>117.981049</td>      <td>GKPer</td>      <td>30842</td>      <td>52.836633</td>      <td>43.923770</td>      <td>255.063174</td>      <td>2010-03-09T21:01:00</td>      <td>2010-03-09T21:54:33</td>      <td>30</td>      <td>00030842030</td>      <td>300</td>      <td>26.239</td>      <td>13.712</td>      <td>12.527</td>      <td>25.243</td>      <td>+03h 31m 20.79s</td>      <td>52d50m11.8788s</td>      <td>+43d 55m 25.6s</td>      <td>43d55m25.572s</td>    </tr>    <tr>      <th>144</th>      <td>73.054432</td>      <td>GKPeroffset1</td>      <td>31653</td>      <td>52.792369</td>      <td>43.923823</td>      <td>240.067049</td>      <td>2010-04-05T02:43:00</td>      <td>2010-04-05T19:44:47</td>      <td>48</td>      <td>00031653048</td>      <td>900</td>      <td>14.457</td>      <td>14.457</td>      <td>0.000</td>      <td>11.585</td>      <td>+03h 31m 10.17s</td>      <td>52d47m32.5284s</td>      <td>+43d 55m 25.8s</td>      <td>43d55m25.7628s</td>    </tr>  </tbody></table><p>145 rows × 19 columns</p></div>


Now, looking at this, I want to get only those rows that have more than 6ks of XRT data. That is, those rows where `q.results['xrt_exposure']>6000`, and that is my subset definition:


```python
q.downloadObsData(destDir='/tmp/APIDemo_download2',
                  subset=q.results['xrt_exposure']>6000,
                  instruments=('XRT',),
                  getAuxil=False)
```

    Making directory /tmp/APIDemo_download2
    Downloading 4 datasets
    Making directory /tmp/APIDemo_download2/00030842017
    Making directory /tmp/APIDemo_download2/00030842017/xrt/
    Making directory /tmp/APIDemo_download2/00030842017/xrt/event/
    Making directory /tmp/APIDemo_download2/00030842017/xrt/hk/
    Making directory /tmp/APIDemo_download2/00030842017/xrt/ssin/



    Downloading 00030842017:   0%|          | 0/109 [00:00<?, ?files/s]


    Making directory /tmp/APIDemo_download2/00030842015
    Making directory /tmp/APIDemo_download2/00030842015/xrt/
    Making directory /tmp/APIDemo_download2/00030842015/xrt/event/
    Making directory /tmp/APIDemo_download2/00030842015/xrt/hk/
    Making directory /tmp/APIDemo_download2/00030842015/xrt/ssin/



    Downloading 00030842015:   0%|          | 0/99 [00:00<?, ?files/s]


    Making directory /tmp/APIDemo_download2/00030842012
    Making directory /tmp/APIDemo_download2/00030842012/xrt/
    Making directory /tmp/APIDemo_download2/00030842012/xrt/event/
    Making directory /tmp/APIDemo_download2/00030842012/xrt/hk/
    Making directory /tmp/APIDemo_download2/00030842012/xrt/ssin/



    Downloading 00030842012:   0%|          | 0/99 [00:00<?, ?files/s]


    Making directory /tmp/APIDemo_download2/00030842005
    Making directory /tmp/APIDemo_download2/00030842005/xrt/
    Making directory /tmp/APIDemo_download2/00030842005/xrt/event/
    Making directory /tmp/APIDemo_download2/00030842005/xrt/hk/
    Making directory /tmp/APIDemo_download2/00030842005/xrt/ssin/



    Downloading 00030842005:   0%|          | 0/114 [00:00<?, ?files/s]


If you want to check your filter expression before actually using it, you can use the `.loc` property of a `DataFrame` like this:


```python
q.results.loc[q.results['xrt_exposure']>6000]
```




<div style='width: 95%; max-height: 200px; overflow: scroll;'><style scoped>    .dataframe tbody tr th:only-of-type {        vertical-align: middle;    }    .dataframe tbody tr th {        vertical-align: top;    }    .dataframe thead th {        text-align: right;    }</style><table border="1" class="dataframe">  <thead>    <tr style="text-align: right;">      <th></th>      <th>_r</th>      <th>name</th>      <th>target_id</th>      <th>ra</th>      <th>decl</th>      <th>roll_angle</th>      <th>start_time</th>      <th>stop_time</th>      <th>obs_segment</th>      <th>obsid</th>      <th>bat_exposure</th>      <th>xrt_exposure</th>      <th>xrt_expo_wt</th>      <th>xrt_expo_pc</th>      <th>uvot_exposure</th>      <th>ra_s</th>      <th>ra_apy</th>      <th>decl_s</th>      <th>decl_apy</th>    </tr>  </thead>  <tbody>    <tr>      <th>0</th>      <td>176.435074</td>      <td>GKPer</td>      <td>30842</td>      <td>52.732920</td>      <td>43.912266</td>      <td>255.973292</td>      <td>2007-03-06T04:39:01</td>      <td>2007-03-06T14:14:01</td>      <td>17</td>      <td>00030842017</td>      <td>7951</td>      <td>7846.457</td>      <td>51.297</td>      <td>7795.160</td>      <td>7848.622</td>      <td>+03h 30m 55.90s</td>      <td>52d43m58.512s</td>      <td>+43d 54m 44.2s</td>      <td>43d54m44.1576s</td>    </tr>    <tr>      <th>1</th>      <td>168.121066</td>      <td>GKPer</td>      <td>30842</td>      <td>52.745146</td>      <td>43.929141</td>      <td>260.414911</td>      <td>2007-02-26T00:25:01</td>      <td>2007-02-26T06:08:24</td>      <td>15</td>      <td>00030842015</td>      <td>6488</td>      <td>6403.276</td>      <td>32.808</td>      <td>6370.468</td>      <td>6418.423</td>      <td>+03h 30m 58.84s</td>      <td>52d44m42.5256s</td>      <td>+43d 55m 44.9s</td>      <td>43d55m44.9076s</td>    </tr>    <tr>      <th>2</th>      <td>154.223024</td>      <td>GKPer</td>      <td>30842</td>      <td>52.740645</td>      <td>43.906271</td>      <td>262.071536</td>      <td>2007-02-16T02:39:01</td>      <td>2007-02-16T08:20:54</td>      <td>12</td>      <td>00030842012</td>      <td>6303</td>      <td>6238.041</td>      <td>82.605</td>      <td>6155.436</td>      <td>6237.197</td>      <td>+03h 30m 57.75s</td>      <td>52d44m26.322s</td>      <td>+43d 54m 22.6s</td>      <td>43d54m22.5756s</td>    </tr>    <tr>      <th>3</th>      <td>25.319939</td>      <td>GKPer</td>      <td>30842</td>      <td>52.793185</td>      <td>43.899291</td>      <td>280.915675</td>      <td>2007-01-17T03:10:01</td>      <td>2007-01-17T13:41:49</td>      <td>5</td>      <td>00030842005</td>      <td>6053</td>      <td>6078.284</td>      <td>60.784</td>      <td>6017.500</td>      <td>5862.453</td>      <td>+03h 31m 10.36s</td>      <td>52d47m35.466s</td>      <td>+43d 53m 57.4s</td>      <td>43d53m57.4476s</td>    </tr>  </tbody></table></div>


And you can see that the `DataFrame` we got back contains only the rows we wanted.

I'll give a few more examples of creating subsets, and rather then fill up your `/tmp` area by downloading, I'll define them as variables and print them using `.loc`, but you can just put my examples straight into the `subset` argument of `downloadObsData`. I'll include such code but commented out, below.

First, let's show you how to apply multiple filters because this *always* take me 3 attempts to get right. Let's say we only want results with more than 6ks of XRT exposure, but less than 7ks.


```python
subset = (q.results['xrt_exposure']>6000)&(q.results['xrt_exposure']<7000)
q.results.loc[subset]
# Uncomment the following if you want:

# q.downloadObsData(destDir='/tmp/APIDemo_download3',
#                   subset=(q.results['xrt_exposure']>6000)&(q.results['xrt_exposure']<7000),
#                   instruments=('XRT',),
#                   getAuxil=False)

```


<div style='width: 95%; max-height: 200px; overflow: scroll;'><style scoped>    .dataframe tbody tr th:only-of-type {        vertical-align: middle;    }    .dataframe tbody tr th {        vertical-align: top;    }    .dataframe thead th {        text-align: right;    }</style><table border="1" class="dataframe">  <thead>    <tr style="text-align: right;">      <th></th>      <th>_r</th>      <th>name</th>      <th>target_id</th>      <th>ra</th>      <th>decl</th>      <th>roll_angle</th>      <th>start_time</th>      <th>stop_time</th>      <th>obs_segment</th>      <th>obsid</th>      <th>bat_exposure</th>      <th>xrt_exposure</th>      <th>xrt_expo_wt</th>      <th>xrt_expo_pc</th>      <th>uvot_exposure</th>      <th>ra_s</th>      <th>ra_apy</th>      <th>decl_s</th>      <th>decl_apy</th>    </tr>  </thead>  <tbody>    <tr>      <th>1</th>      <td>168.121066</td>      <td>GKPer</td>      <td>30842</td>      <td>52.745146</td>      <td>43.929141</td>      <td>260.414911</td>      <td>2007-02-26T00:25:01</td>      <td>2007-02-26T06:08:24</td>      <td>15</td>      <td>00030842015</td>      <td>6488</td>      <td>6403.276</td>      <td>32.808</td>      <td>6370.468</td>      <td>6418.423</td>      <td>+03h 30m 58.84s</td>      <td>52d44m42.5256s</td>      <td>+43d 55m 44.9s</td>      <td>43d55m44.9076s</td>    </tr>    <tr>      <th>2</th>      <td>154.223024</td>      <td>GKPer</td>      <td>30842</td>      <td>52.740645</td>      <td>43.906271</td>      <td>262.071536</td>      <td>2007-02-16T02:39:01</td>      <td>2007-02-16T08:20:54</td>      <td>12</td>      <td>00030842012</td>      <td>6303</td>      <td>6238.041</td>      <td>82.605</td>      <td>6155.436</td>      <td>6237.197</td>      <td>+03h 30m 57.75s</td>      <td>52d44m26.322s</td>      <td>+43d 54m 22.6s</td>      <td>43d54m22.5756s</td>    </tr>    <tr>      <th>3</th>      <td>25.319939</td>      <td>GKPer</td>      <td>30842</td>      <td>52.793185</td>      <td>43.899291</td>      <td>280.915675</td>      <td>2007-01-17T03:10:01</td>      <td>2007-01-17T13:41:49</td>      <td>5</td>      <td>00030842005</td>      <td>6053</td>      <td>6078.284</td>      <td>60.784</td>      <td>6017.500</td>      <td>5862.453</td>      <td>+03h 31m 10.36s</td>      <td>52d47m35.466s</td>      <td>+43d 53m 57.4s</td>      <td>43d53m57.4476s</td>    </tr>  </tbody></table></div>


And lastly, the `isin` function which is really handy as well. This lets us make a subset by giving some values we want a column to contain.So, for example, imagine I only wanted to download the data in the above for those cases with a "target_id" of 81445, 45767 or 81637. I could do that as follows:


```python
myTargs = (81445, 45767, 81637)
subset=q.results['target_id'].isin(myTargs)
q.results.loc[q.results['target_id'].isin(myTargs)]
# q.downloadObsData(destDir='/tmp/APIDemo_download4',
#                   subset=q.results['target_id'].isin(myTargs),
#                   instruments=('XRT',),
#                   getAuxil=False)

```




<div style='width: 95%; max-height: 200px; overflow: scroll;'><style scoped>    .dataframe tbody tr th:only-of-type {        vertical-align: middle;    }    .dataframe tbody tr th {        vertical-align: top;    }    .dataframe thead th {        text-align: right;    }</style><table border="1" class="dataframe">  <thead>    <tr style="text-align: right;">      <th></th>      <th>_r</th>      <th>name</th>      <th>target_id</th>      <th>ra</th>      <th>decl</th>      <th>roll_angle</th>      <th>start_time</th>      <th>stop_time</th>      <th>obs_segment</th>      <th>obsid</th>      <th>bat_exposure</th>      <th>xrt_exposure</th>      <th>xrt_expo_wt</th>      <th>xrt_expo_pc</th>      <th>uvot_exposure</th>      <th>ra_s</th>      <th>ra_apy</th>      <th>decl_s</th>      <th>decl_apy</th>    </tr>  </thead>  <tbody>    <tr>      <th>12</th>      <td>89.880318</td>      <td>GK_Per</td>      <td>81445</td>      <td>52.829137</td>      <td>43.890741</td>      <td>63.483317</td>      <td>2015-09-09T09:14:58</td>      <td>2015-09-09T18:04:10</td>      <td>2</td>      <td>00081445002</td>      <td>4458</td>      <td>4419.383</td>      <td>0.040</td>      <td>4419.343</td>      <td>4350.644</td>      <td>+03h 31m 18.99s</td>      <td>52d49m44.8932s</td>      <td>+43d 53m 26.7s</td>      <td>43d53m26.6676s</td>    </tr>    <tr>      <th>14</th>      <td>150.109990</td>      <td>GKPer</td>      <td>45767</td>      <td>52.743700</td>      <td>43.913840</td>      <td>249.208788</td>      <td>2013-03-20T01:02:59</td>      <td>2013-03-21T01:20:22</td>      <td>5</td>      <td>00045767005</td>      <td>4143</td>      <td>4121.740</td>      <td>63.538</td>      <td>4058.202</td>      <td>4087.774</td>      <td>+03h 30m 58.49s</td>      <td>52d44m37.32s</td>      <td>+43d 54m 49.8s</td>      <td>43d54m49.824s</td>    </tr>    <tr>      <th>23</th>      <td>34.471666</td>      <td>GK_Per</td>      <td>81637</td>      <td>52.812729</td>      <td>43.901448</td>      <td>59.655334</td>      <td>2015-09-08T20:24:58</td>      <td>2015-09-08T22:15:56</td>      <td>1</td>      <td>00081637001</td>      <td>2047</td>      <td>2336.794</td>      <td>0.000</td>      <td>2336.794</td>      <td>2317.685</td>      <td>+03h 31m 15.05s</td>      <td>52d48m45.8244s</td>      <td>+43d 54m 5.2s</td>      <td>43d54m05.2128s</td>    </tr>    <tr>      <th>25</th>      <td>35.612521</td>      <td>GKPer</td>      <td>45767</td>      <td>52.787061</td>      <td>43.901074</td>      <td>87.297491</td>      <td>2012-07-07T06:29:59</td>      <td>2012-07-07T21:44:45</td>      <td>2</td>      <td>00045767002</td>      <td>0</td>      <td>2056.139</td>      <td>0.169</td>      <td>2055.970</td>      <td>2046.231</td>      <td>+03h 31m 8.89s</td>      <td>52d47m13.4196s</td>      <td>+43d 54m 3.9s</td>      <td>43d54m03.8664s</td>    </tr>    <tr>      <th>34</th>      <td>117.912554</td>      <td>GK_Per</td>      <td>81445</td>      <td>52.754590</td>      <td>43.904928</td>      <td>243.739529</td>      <td>2015-03-31T19:32:59</td>      <td>2015-03-31T21:43:07</td>      <td>1</td>      <td>00081445001</td>      <td>1899</td>      <td>1894.012</td>      <td>1894.012</td>      <td>0.000</td>      <td>1859.323</td>      <td>+03h 31m 1.10s</td>      <td>52d45m16.524s</td>      <td>+43d 54m 17.7s</td>      <td>43d54m17.7408s</td>    </tr>    <tr>      <th>88</th>      <td>30.286534</td>      <td>GKPer</td>      <td>45767</td>      <td>52.793330</td>      <td>43.897413</td>      <td>84.556936</td>      <td>2012-07-10T00:12:59</td>      <td>2012-07-10T21:55:42</td>      <td>4</td>      <td>00045767004</td>      <td>240</td>      <td>992.861</td>      <td>0.000</td>      <td>992.861</td>      <td>960.151</td>      <td>+03h 31m 10.40s</td>      <td>52d47m35.988s</td>      <td>+43d 53m 50.7s</td>      <td>43d53m50.6868s</td>    </tr>    <tr>      <th>94</th>      <td>43.622898</td>      <td>GKPer</td>      <td>45767</td>      <td>52.802583</td>      <td>43.892319</td>      <td>87.346896</td>      <td>2012-07-09T01:47:59</td>      <td>2012-07-09T02:53:33</td>      <td>3</td>      <td>00045767003</td>      <td>0</td>      <td>977.932</td>      <td>0.093</td>      <td>977.839</td>      <td>966.009</td>      <td>+03h 31m 12.62s</td>      <td>52d48m09.2988s</td>      <td>+43d 53m 32.3s</td>      <td>43d53m32.3484s</td>    </tr>  </tbody></table></div>


Astute readers will have realised that this effectively takes place of the `IN` operator in SQL, which is not supported by the `addFilter` command (largely for security reasons).
