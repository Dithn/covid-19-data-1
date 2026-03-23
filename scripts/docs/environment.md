# Setting up the development environment

This document explains all the necessary steps to set up your environment and work with this project correctly.

Perhaps you want to set up the environment to help us out, or to learn how we work, or because you want to set up a
similar workflow. In any case, we appreciate the time you are taking here 😀.

- [Python](#python)
- [Install project library](#install-project-library)
- [Set environment variables](#set-environment-variables)
- [Configuration file](#configuration-file)
- [Secrets file](#secrets-file)
- [Questions?](#questions)

## Python

This project uses Python for most of its processes. We have tested the code in Python 3.9 and 3.10. We recommend
creating a [virtual environment](https://docs.python.org/3/library/venv.html) and installing all dependencies there.
Something like:

```bash
# Create
python -m venv venv

# Activate
. venv/bin/activate
```

## Download the project

First thing is to download the project. If you just want to run the code, clone it from the official repository:

```bash
git clone https://github.com/owid/covid-19-data.git
```

Note that the project is quite significant in size, so you may want to use a [shallow clone](https://git-scm.com/docs/git-clone>):

```bash
git clone --depth 1 --no-single-branch https://github.com/owid/covid-19-data.git
```

If you want to **contribute** consider [forking the repository](https://docs.github.com/en/get-started/quickstart/fork-a-repo) instead.

## Install project library

This project is built around the python library `cowidev`, which we are developing to help us
maintain and improve our COVID-19 data pipeline. We recommend using `pip` in [editable mode](https://pip.pypa.io/en/stable/cli/pip_install/#editable-installs). For this, you need to be in `scripts/` folder, next to the `setup.py` file:

```bash
cd scripts
pip install -e .
```

If the installation went well, running `cowid` in your terminal will execute but raise an `EnvironmentError` error.

## Set environment variables

To run the pipeline, you need to create three environment variables: `OWID_COVID_PROJECT_DIR`, `OWID_COVID_CONFIG` and
`OWID_COVID_SECRETS`. The last two variables point to files that we will create in the following sections.

| Variable                 | Description                                                                                                                                                                                                                                                                                 |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `OWID_COVID_PROJECT_DIR` | Path to the local project directory, e.g. `/Users/username/projects/covid-19-data/`                                                                                                                                                                                                         |
| `OWID_COVID_CONFIG`      | Path to the data pipeline [configuration file](#configuration-file). This file provides the default configuration values for the pipeline. Our team uses [`config.yaml`](https://github.com/owid/covid-19-data/blob/master/scripts/config.yaml), which you can use and adapt to your needs. |
| `OWID_COVID_SECRETS`     | Path to the data pipeline [secrets file](#secrets-file).                                                                                                                                                                                                                                    |

You need to add these variables to your shell config file (i.e. `.bashrc`, `.bash_profile` or `.zshrc`), e.g.:

```
export OWID_COVID_PROJECT_DIR=/Users/username/projects/covid-19-data
export OWID_COVID_CONFIG=${OWID_COVID_PROJECT_DIR}/scripts/config.yaml
export OWID_COVID_SECRETS=${OWID_COVID_PROJECT_DIR}/scripts/secrets.yaml
```

Note that this is an example and you are free to choose other paths as long as they point to the correct files. More on
the `config.yaml` and `secrets.yaml` file below.

## Configuration file

The configuration file is required to run the COVID-19 vaccination and testing data pipelines (might be
extended to other pipelines). Please find below a sample with its structure. You can also check [the one we use](https://github.com/owid/covid-19-data/blob/master/scripts/config.yaml).

Note that all fields are required, even if left empty.

```yaml
execution:
  parallel: # Use parallelization (bool)
  njobs: # Number of threads when parallel=True (int)

pipeline:
  # Vaccination data pipeline
  vaccinations:
    # Get step
    get:
      countries: # Countries to collect data for (list)
      skip_countries: # Countries to skip data collection for (list)
    # Process step
    process:
      skip_complete: # Countries to skip data processing (list)
      skip_monotonic_check:
      skip_anomaly_check: # Skip anomaly checks for these countries, dates and metrics (dict)
        Australia: # Country name, Australia left as an example (list)
          - date: # Date to avoid check for (str YYYY-MM-DD)
            metrics: # Metric to avoid check for (str)
    # Generate step
    generate:
    # Export step
    export:

  # Testing data pipeline
  testing:
    # Get step
    get:
      countries: # Countries to collect data for (list)
      skip_countries: # Countries to skip data collection for (list)
    # Process step
    process:
    # Generate step
    generate:
    # Export step
    export:

  # Hospitalization data pipeline
  hospitalizations:
    # Generate step
    generate:
      # Countries to include
      countries:
      # Countries to skip
      skip_countries:
```

## Secrets file

We use the secrets file to update internal flows with the pipeline's output (fields `vax` and `test`). While there
are many fields, **contributors may only need set one field: `google.clients_secrets`**, which is needed to interact with Google Drive /
Google Sheets based sources (more on how to get it [here](#how-can-i-get-the-google-client-secrets-json-file)).

Note that this file is not shared, as it may contain sensitive data.

```yaml
# Google configuration (dict)
google:
  client_secrets: # Path to google client_secrets.json file
  mail: # Email (str), OPTIONAL

scraperapi:
  token: # Token for https://www.scraperapi.com/ services (free plan)

slack:
  token: # Token to send messages to slack

# Vaccination configuration (dict), OPTIONAL
vaccinations:
  post: # OWID Vaccination internal post link (str)
  sheet_id: # OWID Vaccination internal spredsheet ID, where manual imports happen (str)

# Testing configuration (dict), OPTIONAL
testing:
  post: # OWID Testing internal post link (str)
  sheet_id: # OWID Testing internal spredsheet ID, where manual imports happen (str)
  sheet_id_attempted: # OWID Extra Testing internal spredsheet ID, where attempted countries are listed (str)

# Twitter configuration (dict), OPTIONAL
twitter:
  consumer_key: # Consumer key (str)
  consumer_secret: # Consumer secret (str)
  access_secret: # Access secret (str)
  access_token: # Acces token (str)
```

### How can I get the google `client_secrets.json` file?

The value of `google.client_secrets` should point to the JSON file downloaded from Google Cloud Platform that contains
your personal Google credentials. To obtain it, you can follow [`gsheets` documentation](https://gsheets.readthedocs.io/en/stable/#quickstart):

> Log into the [Google Developers Console](https://console.developers.google.com/) with the Google account whose
> spreadsheets you want to access. Create (or select) a project and enable the **Drive API** and **Sheets API** (under
> Google Apps APIs).
>
> Go to the Credentials for your project and create **New credentials** > **OAuth client ID** > of type **Other**. In
> the list of your **OAuth 2.0 client IDs** click **Download JSON** for the Client ID you just created.

We recommend saving the downloaded file in a safe directory, with a simplified name, e.g.
`~/.config/owid/client_secrets.json`.

### What is `scraperapi.token`?

Scraper API is a service with a friendly proxy that allows you to access any HTML without being blocked. Four our
pipeline you need to [register](https://www.scraperapi.com/) and get their TOKEN. The free plan should be OK!

## Verify installation

Once you have installed the library, configured the configuration and secrets files accordingly along with the
environment variables you should be able to run:

```
~ cowid --help
Usage: cowid [OPTIONS] COMMAND [ARGS]...

  COVID-19 Data pipeline tool by Our World in Data.

Options:
  --parallel / --no-parallel  Parallelize process.  [default: parallel]
  --n-jobs INTEGER            Number of threads to use.  [default: -2]
  -S, --server / --no-server  Only critical log and final message to slack.
                              [default: no-server]
  --help                      Show this message and exit.

Commands:
  megafile    COVID-19 data integration pipeline (former megafile)
  test        COVID-19 Testing data pipeline.
  vax         COVID-19 Vaccination data pipeline.
  hosp        COVID-19 Hospitalization data pipeline.
  casedeath   COVID-19 Cases/Deaths data pipeline.
  variants    COVID-19 Variants data pipeline.
  xm          COVID-19 Excess Mortality data pipeline.
  sweden      COVID-19 Sweden data pipeline.
  uk-nations  COVID-19 UK Nations data pipeline.
  check       COVID-19 data pipeline checks.
```

## Questions?

Raise an [issue](https://github.com/owid/covid-19-data/issues), we are happy to help!
