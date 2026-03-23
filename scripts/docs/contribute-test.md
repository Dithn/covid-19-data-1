# How to contribute to our testing data
**On 23 June 2022, we stopped adding new datapoints to our COVID-19 testing dataset. We continue to update all other metrics in our COVID-19 dataset. You can read more [here](https://github.com/owid/covid-19-data/discussions/2667)**

We welcome contributions to our testing dataset! 

Automated countries can be found under the [`cowidev.testing`](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/testing) folder. Some countries have a _batch_ collection process while others an _incremental_ one.

- **batch**: The complete timeseries is updated at every execution. This process is preferred, as it means the source can correct past data.
- **incremental**: Only the last data point is added. 

The code consists of a mixture of Python and R scripts. As we try to slowly move our entire code base to Python, we currently only accept contributions written in Python.

### Content
- [Add a new country](#add-a-new-country)
    - [Steps to contribute](#steps-to-contribute)
- [Criteria to accept pull requests](#criteria-to-accept-pull-requests)
- [Metrics collected](#metrics-collected)
    - [Prioritisation of metrics](#prioritisation-of-metrics)

## Add a new country
To automate the data import process for a country, make sure that:
- The source is reliable.
- The source provides data in a format that can be easily read:
    - As a file (e.g. csv, json, xls, etc.)
    - As plain text in source HTML, which can be easily scraped.

### Steps to contribute
1. Decide if the import is batch (i.e. the entire time series) or incremental (last value). See the scripts in
   [`cowidev.testing.batch`](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/testing/batch) and [`cowidev.testing.incremental`](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/testing/incremental) for more details. **Note: Batch is preferred over incremental**.
2. Create a script in the right location, based on your decision at step 1: either in [`cowidev.testing.batch`](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/testing/batch) or
   [`cowidev.testing.incremental`](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/testing/incremental). Note that each source is different and there is no single pattern that works for all sources, however you can take some inspiration from the scripts below:
    - Batch imports:
        - CSV: [France](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/testing/batch/france.py)
        - API/JSON: [Portugal](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/testing/batch/portugal.py)
        - HTML: [Bosnia & Herzegovina](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/testing/batch/bosnia_herzegovina.py)
        - HTML, with JS: [Turkey](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/testing/batch/turkey.py)
    - Incremental imports:
        - CSV: [Equatorial Guinea](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/testing/incremental/equatorial_guinea.py)
        - HTML: [Bahrain](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/testing/incremental/bahrain.py)
3. Make sure that you are collecting the right metrics (for more details, read the [Metrics collected](#metrics-collected) section).
4. Test that the script works and is stable. For this you need to have the [library
   installed](environment). Run
    ```
    cowid test get [country-name]
    ``` 
5. Create a pull request with your code.


## Criteria to accept pull requests
- Limit your pull request to a single country or a single feature.
- We welcome code improvements/bug fixes. As an example, you can read [#465](https://github.com/owid/covid-19-data/pull/465).

You can of course, and we appreciate it very much, create pull requests for other cases.

Note that files in the [public folder](https://github.com/owid/covid-19-data/tree/master/public) are not to be modified via
pull requests.

## Metrics collected
For each country we collect metadata variables such as:

- `Country`: Name of the country or territory
- `Date`: Date of the reported data
- `Units`: Units of the reported data. This can be _just one_ of `people tested`, `tests performed` and `samples tested`. That is, a country file can't contain  mixed units.
    - `people tested`: Number of people tested.
    - `tests performed`: Number of tests performed. A single person can be tested more than once in a given day.
    - `samples tested`: Number of samples tested. In some cases, more than one sample may be required to
      perform a given test.
- `Source URL`: URL of the source.
- `Source label`: Name of the source.
- `Notes`: Additional notes (optional).

In addition, we may collect one or all of the following two metrics:

- `Cumulative total`: Cumulative number of people tested, tests performed or samples tested (depending on `Units`).
- `Daily change in cumulative total`: Daily number of new people tested, tests performed or samples tested (depending
  on `Units`).

Please read the [following section](#prioritisation-of-metrics)  to understand better which metric is preferred in each case.	 
 
Finally, if we deem it appropriate, we also estimate the positive rate (`Positive rate`). This is done whenever we
consider that the data provided by Johns Hopkins University on confirmed cases might not be usable for this purpose (for example because the country doesn't report its cases every day of the week).

### Prioritisation of metrics

#### `Cumulative total` vs `Daily change in cumulative total`
1. The ideal situation is to collect `Cumulative total`. From it, we can infer intermediate totals (with a linear
   forward-fill) and create the 7-day average daily series. So in this situation, our dataset will have Cumulative total
   and 7-day, **which is perfect**.
    
    - Examples: [`greece.py`](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/testing/incremental/greece.py), [`italy.py`](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/testing/batch/italy.py), [`brazil.py`](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/testing/batch/brazil.py)
2. The second-best situation, if there is no `Cumulative total`, is to collect `Daily change in cumulative total` every
   day instead. If the daily number is _really_ present each day, then our script will calculate the 7-day average.

   - Examples: [`chile.py`](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/testing/batch/chile.py), [`albania.py`](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/testing/incremental/albania.py)
3. The "worst" situation is to have an irregular series of Daily change in cumulative total. This is basically of little
   use, because we can't calculate any cumulative total (because some days are missing) and we also can't calculate the
   7-day average (because some days are missing).
   
   - Examples: [`moldova.py`](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/testing/incremental/moldova.py)

#### `Positive rate`
Examples: [`argentina.py`](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/testing/batch/argentina.py), [`france.py`](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/testing/batch/france.py)
