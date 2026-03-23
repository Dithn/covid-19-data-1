### ⚠️ This document is still being writen


# Vaccination update automation
[![Python 3"](https://img.shields.io/badge/python-3.7|3.8|3.9-blue.svg?&logo=python&logoColor=yellow)](https://www.python.org/downloads/release/python-3)
[![Contribute](https://img.shields.io/badge/-contribute-0055ff)](CONTRIBUTE.md)
[![Data](https://img.shields.io/badge/public-data-purple)](../../../public/data/)


Vaccination data is updated on a daily basis. For some countries, the update is done by means of an automated process,
while others require some manual work. To keep track of the currently automated processes, check [this
table](../../output/vaccinations/automation_state.csv). 

### Content
1. [Vaccination pipeline files](#1-vaccination-pipeline-files)
2. [Development environment](#2-development-environment)
3. [The data pipeline](#3-the-data-pipeline)
4. [Other functions](#4-other-functions)
5. [Contribute](CONTRIBUTE.md)
6. [FAQs](#6-faqs)

## 1. Vaccination pipeline files
This directory contains the following files:


| File name      | Description |
| ----------- | ----------- |
| [`output/vaccinations/`](../../output/vaccinations/)      | Temporary automated imports are placed here.       |
| [`src/cowidev/vax/`](../../src/cowidev/vax)      | Scripts to automate country data imports.       |
| [`config.yaml`](config.yaml)      | Data pipeline configuration.       |
| [`MANIFEST.in`](MANIFEST.IN), [`setup.py`](setup.py), [`requirements.txt`](requirements.txt), [`requirements-flake.txt`](requirements-flake.txt)      |     Library development related files   |
| [`automation_state.csv`](../../output/vaccinations/automation_state.csv)      |     Lists if country process is automated (TRUE) or not (FALSE).   |
| [`source_table.html`](source_table.html)      | HTML table with country source URLs. Shown at [OWID's website](https://ourworldindata.org/covid-vaccinations#source-information-country-by-country).       |
| [`vax_update.sh.template`](vax_update.sh.template)      | Template to push vaccination update changes.       |

_*Only most relevant files have been listed_ 


## 2. Development environment
<details closed>
<summary>Show steps ...</summary>
Follow the steps below to correctly set up your virtual environment.

### Configuration file
A valid _configuration file_ is required to run the vaccination pipeline. In addition, you must have environment
variable `{OWID_COVID_VAX_CONFIG_FILE}` pointing to the aforementioned _configuration file_. We currently use
[config.yaml](../../config.yaml). This file contains data used throughout the different pipeline stages.

```yaml
global:
  project_dir: !ENV ${OWID_COVID_PROJECT_DIR}
  credentials: !ENV ${OWID_COVID_VAX_CREDENTIALS_FILE}
pipeline:
  get-data:
    parallel: True
    countries:
    njobs: -2
    skip_countries:
      - Colombia
  process-data:
    skip_complete:
    skip_monotonic_check:
      Northern Ireland:
        - date: 2021-04-29
          metrics: people_vaccinated
    skip_anomaly_check:
      Bahrain:
        - date: 2021-03-06
          metrics: total_vaccinations
      Bolivia:
        - date: 2021-03-06
          metrics: people_vaccinated
      Brazil:
        - date: 2021-01-21
          metrics: 
           - total_vaccinations
           - people_vaccinated
  generate-dataset:
```

Our current configuration requires to previously set environment variables `${OWID_COVID_PROJECT_DIR}` and
`${OWID_COVID_VAX_CREDENTIALS_FILE}`. We recommend defining them in `~/.bashrc` or `/.bash_profile`. For instance:

```sh
export OWID_COVID_PROJECT_DIR=/Users/username/projects/covid-19-data
export OWID_COVID_VAX_CREDENTIALS_FILE=${OWID_COVID_PROJECT_DIR}/scripts/vax_dataset_config.json
```

### Credentials file
The environment variable `${OWID_COVID_VAX_CREDENTIALS_FILE}` corresponds to the path to the credentials file. This is internal. Google-related fields require a valid OAuth JSON credentials file (see [gsheets
  documentation](https://gsheets.readthedocs.io/en/stable/#quickstart)). The file should have the following structure:
```json
{
    "greece_api_token": "[GREECE_API_TOKEN]",
    "owid_cloud_table_post": "[OWID_CLOUD_TABLE_POST]",
    "google_credentials": "[CREDENTIALS_JSON_PATH]",
    "google_spreadsheet_vax_id": "[SHEET_ID]",
    "twitter_consumer_key": "[TWITTER_CONSUMER_KEY]",
    "twitter_consumer_secret": "[TWITTER_CONSUMER_SECRET]"
}
```

### Check the style
We use [flake8](https://flake8.pycqa.org/en/latest/) to check the style of our code. The configuration lives in file 
[tox.ini](../../tox.ini). To check the style, simply run

```sh
$ tox
```
**Note**: This requires tox to be installed (`$ pip install tox`)
</details>

## 3. The data pipeline
To update the data, prior to running the code, make sure to correctly [set up the development environment](#2-development-environment).

### Manual data updates

Check for new updates and manually add them in the internal spreadsheet:
- See this repo's [pull requests](https://github.com/owid/covid-19-data/pulls) and [issues](https://github.com/owid/covid-19-data/issues).
- Look for new data based on previously-used source URLs.

### Automated process
Once all manual processes have been finished, it  is time to leverage the tool `cowid-vax`. The automation step is
further broken into 4 sub-steps, which we explain below. While these can all be run at once, we recommend running them
one by one. Prior to running these, make sure you are correctly using your [configuration file](#configuration-file).

*Note*: you can use [vax_update.sh.template](../../vax_update.sh.template) as an example of how to run the data pipeline
automated step.

#### Data pipeline configuration
**This section is being re-factored, in an attempt to improve credentials and configuration files.**
To correctly use the configuration in your [config.yaml](../../config.yaml), you can:
  - Set environment variable `${OWID_COVID_VAX_CONFIG_FILE}` to file's path.
  - Save configuration under `~/.config/cowid/config.yaml` and run.
  - Run `$ cowid-vax --config config.yaml`, explicitly specifying the path to the config file.
If above was not possible, use arguments passed via the command call, i.e. `--parallel`, `--countries`, etc.


<details closed>
<summary markdown='span'>For more details run: cowid-vax --help</summary>

```txt
usage: cowid-vax [-h] [-c COUNTRIES] [-p] [-j NJOBS] [-s] [--config CONFIG] [--credentials CREDENTIALS] [--checkr]
                 {get-data,process-data,generate-dataset,export,all}

Execute COVID-19 vaccination data collection pipeline.

positional arguments:
  {get-data,process-data,generate-dataset,export,all}
                        Choose a step: i) `get-data` will run automated scripts, 2) `process-data` will get csvs generated in
                        1 and collect all data from spreadsheet, 3) `generate-dataset` generate the output files, 4) `export`
                        to generate all final files, 5) `all` will run all steps sequentially.

optional arguments:
  -h, --help            show this help message and exit
  -c COUNTRIES, --countries COUNTRIES
                        Run for a specific country. For a list of countries use commas to separate them (only in mode get-
                        data)E.g.: peru, norway. Special keywords: 'all' to run all countries, 'incremental' to run
                        incrementalupdates, 'batch' to run batch updates. Defaults to all countries. (default: all)
  -p, --parallel        Execution done in parallel (only in mode get-data). (default: False)
  -j NJOBS, --njobs NJOBS
                        Number of jobs for parallel processing. Check Parallel class in joblib library for more info (only in
                        mode get-data). (default: -2)
  -s, --show-config     Display configuration parameters at the beginning of the execution. (default: False)
  --config CONFIG       Path to config file (YAML). Will look for file in path given by environment variable
                        `$OWID_COVID_VAX_CONFIG_FILE`. If not set, will default to ~/.config/cowid/config.yaml (default:
                        /Users/lucasrodes/repos/covid-19-data/scripts/scripts/vaccinations/config.yaml)
  --credentials CREDENTIALS
                        Path to credentials file (JSON). If a config file is being used, the value ther will be prioritized.
                        (default: vax_dataset_config.json)
  --checkr              Compare results from generate-dataset with results obtained with former generate_dataset.R script.It
                        requires that the R script is previously run (without removing temporary files vax & metadata)!
                        (default: False)

```
</details>

#### Get the data

Run: 

```
$ cowid-vax get
```
This step runs the scrips for [batch](../../src/cowidev/vax/batch) and [incremental](../../src/cowidev/vax/incremental) updates. It will then generate
individual country files and save them in [`output`](output/vaccinations/main_data/).

*Note:* This step might crash for some countries, as the automation scripts might no longer (or temporarily) work
(e.g. due to changes in the source). Try to keep the scripts up to date.
#### Process the data

Run: 

```
$ cowid-vax process
```

Collect manually updated data from the spreadsheet and data generated in (1). Process this data, and generate public country data in
  [`country_data`](../../../public/data/vaccinations/country_data/), as well as temporary files 
  `vaccinations.preliminary.csv` and `metadata.preliminary.csv`.

#### Generate the dataset

Run: 

```
$ cowid-vax generate
```

Generate pipeline output files.

#### Export final files and update website

Run: 

```
$ cowid-vax export
```

Final pipeline step. This updates few more output files. Also, this opens OWID's vaccination website, in order to update
the table references (HTML is automatically copied to clipboard).

#### Generated files
Once the automation is successfully executed, the following files and directories are updated:

| File name      | Description |
| ----------- | ----------- |
| [`vaccinations.csv`](../../../public/data/vaccinations/vaccinations.csv)      | Main output with vaccination data of all countries.       |
| [`vaccinations.json`](../../../public/data/vaccinations/vaccinations.json)   | Same as `vaccinations.csv` but in JSON format.        |
| [`vaccinations-by-manufacturer.csv`](../../../public/data/vaccinations/vaccinations-by-manufacturer.csv)   | Secondary output with vaccination by manufacturer for a select number of countries.        |
| [`country_data/`](../../../public/data/vaccinations/country_data/)   | Individual country CSV files.        |
| [`locations.csv`](../../../public/data/vaccinations/locations.csv)   | Country-level metadata.        |
| [`source_table.csv`](../../output/vaccinations/source_table.html)   | HTML table with country source URLs. Shown at [OWID's website](https://ourworldindata.org/covid-vaccinations#source-information-country-by-country)        |
| [`automation_state.csv`](../../output/vaccinations/automation_state.csv)   | Lists if country process is automated (TRUE) or not (FALSE).        |
| [`COVID-19 - Vaccinations.csv`](../../grapher/COVID-19%20-%20Vaccinations.csv)   | Internal file for OWID grapher on vaccinations.        |
| [`COVID-19 - Vaccinations by manufacturer.csv`](../../grapher/COVID-19%20-%20Vaccinations%20by%20manufacturer.csv)   | Internal file for OWID grapher on vaccinations by manufacturer.        |


#### Notes

You can run several steps at once, e.g.

```sh
$ cowid-vax get process
```

## 4. Other functions
### Tracking
It is extremely useful to get some insights on which data are we tracking (and which are we not). This can be done with
the tool `cowid vax track`. Find below some use cases.

*Note*: Use uption `--to-csv` to export results as csv files (a default filename is used).

<details closed>
<summary><strong>Which countries are missing?</strong></summary>
Run 

```
$ cowid vax track countries-missing
```
Countries are given from most to least populated.
</details>

<details closed>
<summary><strong>Which countries have been updated unfrequently?</strong></summary>
Get the list of countries sorted by least frequently updated. The update frequency is defined by the ratio between the 
number of days with an update and the number of days of observation (i.e. days since first update).

```
$ cowid vax track countries-least-updatedfreq
```

Countries are given from least to most frequently updated.
</details>

<details closed>
<summary><strong>Which countries haven't been updated for some time?</strong></summary>
Get the list of countries and their last update by running:

```
$ cowid vax track countries-last-updated
```

Countries are given from least to most recently updated.
</details>

<details closed>
<summary><strong>Which countries have been updated few times?</strong></summary>
Get the list of countries least updated (in absolute counts):

```
$ cowid vax track countries-least-updated
```

Countries are given from least to most frequently updated.
</details>

<details closed>
<summary><strong>Which vaccines are missing?</strong></summary>
Get the list of countries with missing vaccines:

```
$ cowid vax track vaccines-missing
```

Countries are given from the one with the least to the one with he most number of untracked vaccines.
</details>


## 5. Contribute
We welcome contributions! Read more in [CONTRIBUTE](CONTRIBUTE.md)
## 6. FAQs

### Any question or suggestion?
Kindly open an [issue](https://github.com/owid/covid-19-data/issues/new). If you have a technical proposal, feel free to
open a [pull request](https://github.com/owid/covid-19-data/compare)

### An automation no longer works (internal)
If you detect that an automation is no longer working, and the process seems like it can't be fixed at the moment:
- Set its state to `automated = FALSE` in the `LOCATIONS` tab of the internal spreadsheet.
- Add a new tab in the spreadsheet to manually input the country data. Make sure to include the historical data from the [`output`](../../output) file.
- Delete the automation script and automated CSV output to avoid confusion.
