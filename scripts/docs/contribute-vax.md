# How to contribute to our vaccination data

We welcome contributions to our vaccination dataset! Note that due to the nature of our pipeline, **we cannot accept
pull requests for countries for which our processes are manual**. To see which countries have manual processes check [this file](https://github.com/owid/covid-19-data/blob/master/scripts/output/vaccinations/automation_state.csv).

## Content
- [About our vaccination dataset](#about-our-vaccination-dataset)
  - [General dataset](#general-dataset)
  - [Manufacturer dataset](#manufacturer-dataset)
  - [Age group dataset](#age-group-dataset)
- [Report new data values](#report-new-data-values)
- [Add new country automations](#add-new-country-automations)
  - [Contribute to general dataset](#contribute-to-general-dataset)
  - [Contribute to manufacturer or age group dataset](#contribute-to-manufacturer-or-age-group-dataset)
- [Criteria to accept pull requests](#criteria-to-accept-pull-requests)

## About our vaccination dataset
Read this section to better understand the vaccination data that we are currently collecting.

We currently produce three vaccination datasets: 

- **General data**: People vaccinated and doses administered. ([`vaccinations.csv`](https://github.com/owid/covid-19-data/blob/master/public/data/vaccinations/vaccinations.csv))
- **Manufacturer data**: Doses administered by manufacturer. ([`vaccinations-by-age-group.csv`](https://github.com/owid/covid-19-data/blob/master/public/data/vaccinations/vaccinations-by-age-group.csv))
- **Age group data**: People vaccinated (all stages) by age group. ([`vaccinations-by-manufacturer.csv`](https://github.com/owid/covid-19-data/blob/master/public/data/vaccinations/vaccinations-by-manufacturer.csv))

### General dataset

|location|date      |vaccine                                                        |source_url                                                                                   |total_vaccinations|people_vaccinated|people_fully_vaccinated|total_boosters|
|--------|----------|---------------------------------------------------------------|---------------------------------------------------------------------------------------------|------------------|-----------------|-----------------------|--------------|
|Cambodia|2021-09-10|Johnson&Johnson, Oxford/AstraZeneca, Sinopharm/Beijing, Sinovac|https://www.facebook.com/MinistryofHealthofCambodia/photos/a.930887636950343/4376835072355565|20554497          |11406989         |9350408                |742293        |


Where metrics:

- `total_vaccinations`
- `people_vaccinated`
- `people_fully_vaccinated`
- `total_boosters`

are defined [here](https://github.com/owid/covid-19-data/tree/master/public/data#vaccinations). Additionally the
remaining fields:

- `location`: Name of the country/territory
- `date`: Date of reported figures.
- `vaccine`: Vaccines used, comma-separated. See accepted names
  [here](https://github.com/owid/covid-19-data/blob/ad2d0d4f5ee6f5a49a118807fb24360c4ddaea26/scripts/src/cowidev/vax/utils/checks.py#L7-L30).
 
Note that for some countries, some metrics can't be reported as these are not be available. This is not ideal but it is OK.

### Manufacturer dataset
Along with the main data, we include vaccine data broken down by manufacturer for some countries where this data is available.

Each row in the data gives the cumulative number of doses administered for a given date and vaccine manufacturer.

#### Fields
- `date`: Date in format YYYY-MM-DD
- `vaccine`: Vaccine manufacturer name. Our convention for vaccine names can be found
  [here](https://github.com/owid/covid-19-data/blob/ad2d0d4f5ee6f5a49a118807fb24360c4ddaea26/scripts/src/cowidev/vax/utils/checks.py#L7-L30).
  As new vaccines emerge, new conventions will be defined.
- `location`: Country/region/territory name.
- `total_vaccinations`: Cumulative number of administered doses up to `date` for given `vaccine`.


#### Example
|date      |vaccine           |location|total_vaccinations |
|----------|------------------|------------------|---------|
|...|...           |...            |...|
|2021-06-01|Moderna           |Lithuania            |151261|
|2021-06-01|Oxford/AstraZeneca|Lithuania            |333733|
|2021-06-01|Johnson&Johnson   |Lithuania             |34974|
|2021-06-01|Pfizer/BioNTech   |Lithuania           |1133371|
|...|...           |...            |...|

#### Notes
We only include manufacturer data for countries for which the process can be automated. No manual reports are currently
being accepted. This is to ensure scalability of the project.


### Age group dataset

We include vaccine data broken down by age groups for some countries where the data is available.

Each row in the data gives the percentage of people within an age group that have received at least one dose. Note that
currently there is no standard for which age groups are accepted, as each country may define different ones. As a
general rule, we try to have groups in 10 years chunks but this is optional.

**Note that the reported metric is relative, and not absolute.**
#### Fields
- `date`: Date in format YYYY-MM-DD.
- `age_group_min`: Lower bound of the age group.
- `age_group_max`: Upper bound of the age group (included).
- `location`: Country/region/territory name.
- `people_vaccinated_per_hundred`: Percentage of people within the age group that have received at least one dose.
- `people_fully_vaccinated_per_hundred`: Percentage of people within the age group that have been fully vaccinated.
- `people_with_booster_per_hundred`: Percentage of people within the age group that have received at least one booster.

#### Example

|location|date      |age_group_min|age_group_max|people_vaccinated_per_hundred|people_fully_vaccinated_per_hundred|people_with_booster_per_hundred|
|--------|----------|-------------|-------------|-----------------------------|-----------------------------------|-------------------------------|
|...|...           |...            |...|...|...|...|
|Slovakia|2021-12-03|18 |24 |50.41|46.65|1.3  |
|Slovakia|2021-12-03|25 |49 |51.31|48.26|3.52 |
|Slovakia|2021-12-03|50 |59 |60.24|57.6 |6.14 |
|Slovakia|2021-12-03|60 |69 |67.12|65.14|16.05|
|Slovakia|2021-12-03|70 |79 |77.86|75.99|36.14|
|Slovakia|2021-12-03|80 |   |63.5 |61.1 |27.39|
|...|...           |...            |...|...|...|...|

#### Notes
We only include age group data for countries for which the process can be automated. No manual reports are currently
being accepted. This is to ensure scalability of the project.

## Report new data values

To report new values for a country/location, first check if the imports for that country/territory are automated. You
can check column `automated` in [this file](https://github.com/owid/covid-19-data/blob/master/scripts/output/vaccinations/automation_state.csv).

- If the country imports are automated (`TRUE` value in file above), new values might be added in next
  update. **Only report new values if the data is missing for more than 48 hours!** Report the new data as a [pull request](https://github.com/owid/covid-19-data/compare).
- If the country imports are not automated, i.e. data is manually added, (`FALSE` value in file above) you can report
  new data in any of the following ways:
  - Open a [new issue](https://github.com/owid/covid-19-data/issues/new), reporting the data and the corresponding
    source.
  - If you plan to contribute regularly to a specific country/location, consider opening a dedicated issue. This way,
    we can easily back-track the data addded for that country/location.
  - If this seems too complicated, alternatively, you may simply add a comment to thread
[#230](https://github.com/owid/covid-19-data/issues/230). 

### Notes
- We only accept official sources or news correctly citing official sources.
- We only accept manual reports for country aggregate vaccination data. That is, we currently do not include
  manufacturer and age vaccination data if no automation is provided.

## Add new country automations
To automate the data import for a country, make sure that:
- The source is reliable.
- The source provides data in a format that can be easily read:
    - As a file (e.g. csv, json, xls, etc.)
    - As plain text in source HTML, which can be easily scraped.

### Contribute to general dataset
Next, follow the steps below:

1. Decide if the import is batch (i.e. all the timeseries) or incremental (last value). See the scripts in
   [`src/cowidev/vax/batch`](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/vax/batch) and [`src/cowidev/vax/incremental`](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/vax/incremental) for more details. **Note: Batch is
   prefered over Incremental**.
2. Create a script and place it based on decision in step 1 either in [`src/cowidev/vax/batch`](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/vax/batch) or
   [`src/cowidev/vax/incremental`](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/vax/incremental). Note that each source is different and there is no single pattern that
   works for all sources.

3. Feel free to add [manufacturer](#manufacturer-dataset)/[age data](#age-group-dataset) if you are automating a **batch
   script** and the data is available.
4. Test that it is working and that it is stable. For this you need to have the [library
   installed](environment). Run
    ```
    cowid vax get [country-name]
    ``` 
5. Issue a pull request and wait for a review.

Find below some scripts for reference based on the source file format and the mode (batch or incremental):

| Mode        | CSV   | JSON          | API/JSON  | Excel       | PDF                       | HTML                       | HTML (news feed) |
|-------------|-------|---------------|-----------|-------------|---------------------------|----------------------------|------------------|
| **Batch**       | [Peru](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/vax/batch/peru.py) (+AM), [Romania](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/vax/batch/romania.py) (+M)  | [Hong Kong](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/vax/batch/hong_kong.py)     | [Lithuania](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/vax/batch/lithuania.py), [Israel](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/vax/batch/israel.py) (+A), [Zimbabwe](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/vax/batch/zimbabwe.py)| [Luxembourg](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/vax/batch/luxembourg.py), [New Zealand](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/vax/batch/new_zealand.py), [South Korea](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/vax/batch/south_korea.py) (+A) |                           |                            |                  |
| **Incremental** | [Finland](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/vax/incremental/finland.py) | [Macao](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/vax/incremental/macao.py) | [Argentina](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/vax/incremental/argentina.py), [Poland](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/vax/incremental/poland.py) |   [Spain](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/vax/incremental/spain.py)   | [Taiwan](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/vax/incremental/taiwan.py), [Azerbaijan](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/vax/incremental/azerbaijan.py), [Kenya](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/vax/incremental/kenya.py) | [Bulgaria](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/vax/incremental/bulgaria.py), [Equatorial Guinea](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/vax/incremental/equatorial_guinea.py) | [Albania](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/vax/incremental/albania.py), [Monaco](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/vax/incremental/monaco.py)   |

_*(+M): Also collects manufacturer data, (+A): Also collects age group data, (+AM): Also collects both manufacturer and
age group data._


Additionally, there are some special scripts which collect data from several countries:
  - From WHO: See [`who.py`](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/vax/incremental/who.py) and
    [list of countries](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/vax/utils/orgs/who_config.yaml).
  - From Africa CDC: See
    [`africacdc.py`](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/vax/incremental/africacdc.py) and
    [list of countries](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/vax/utils/orgs/acdc_config.yaml).
  - From PAHO: See
    [`paho.py`](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/vax/incremental/paho.py)  and
    [list of countries](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/vax/utils/orgs/paho_config.yaml).
  - From ECDC: See [`ecdc.py`](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/vax/batch/ecdc.py) and
    [list of countries](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/vax/utils/orgs/ecdc_config.yaml).
  - From SPC: See [`spc.py`](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/vax/batch/spc.py) and
    [list of countries](https://github.com/owid/covid-19-data/blob/master/scripts/src/cowidev/vax/utils/orgs/spc_config.yaml).


More details: [#230](https://github.com/owid/covid-19-data/issues/230),
[#250](https://github.com/owid/covid-19-data/issues/250)

### Contribute to manufacturer or age group dataset
We only accept scripts that collect the full time series (no support for incremental updates) when it comes to
manufacturer and age group vaccination data.

Review all the steps in the [previous section](#Contribute-to-general-dataset) to better understand how to add this
data. Also, refer to section [_About our vaccination dataset_](#About-our-vaccination-dataset) for more details about
the fortmat of this datasets.

## Criteria to accept pull requests
Due to how our pipeline operates at the moment, pull requests are only accepted under certain conditions. These include,
but are not limited to, the following:

- Code improvements / bug fixes. As an example, you can take [#465](https://github.com/owid/covid-19-data/pull/465).
- Updates on the data for countries with automated data imports and incremental processes (this countries are found
  [here](../../src/cowidev/vax/incremental)). For this case, you can create a PR modifying the corresponding file in [output
  folder](https://github.com/owid/covid-19-data/tree/master/scripts/output/vaccinations). Create the pull
  request only if the daily update already ran but did not update the corresponding country.

You can of course, and we appreciate it very much, create pull requests for other cases.

Note that files in [public folder](https://github.com/owid/covid-19-data/tree/master/public) are not to be manually modified.
