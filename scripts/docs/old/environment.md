### ⚠️ This document is still being writen

# Environment
In this document we explain all the necessary steps to correctly set up your environment and work with this project. 

Perhaps you want to set up the environment to help us out, or to learn how we work, or because you want to set up a
similar workflow. In any case, we really appreciate the time you are taking here 😀.

- [Python](#python)
- [Install project library](#install-project-library)
- [Set environment variables](#set-environment-variables)
- [Pipeline configuration file](#pipeline-configuration-file)
- [Pipeline secrets file](#pipeline-secrets-file)
- [FAQs](#FAQs)

## Python
This project uses Python for most of its processes. The code has been tested in Python 3.9 and 3.10. We recommend
creating a [virtual environment](https://docs.python.org/3/library/venv.html) and installing all dependencies there.
Something like:

```bash
# Create
python -m venv venv

# Activate
. venv/bin/activate
```

## Install project library
This project is built around the python library [`cowidev`](../src/cowidev/), which are currently developing to help us
maintain and improve our _COVID-19 data pipeline_. To install the library, we recommend using `pip` in [editable mode](https://pip.pypa.io/en/stable/cli/pip_install/#editable-installs). For this, you need to be in `scripts/` folder, next to the `setup.py` file:

```bash
cd scripts
pip install -e .
```

## Set environment variables
To run the pipeline, you need to create three environment variables: 

- `OWID_COVID_PROJECT_DIR`: Path to the local project directory, e.g. `/Users/username/projects/covid-19-data/`
- `OWID_COVID_CONFIG`: Path to the data pipeline configuration file (`yaml` format). This file provides the default configuration values for the pipeline. Our team uses [`config.yaml`](../config.yaml), which you can use and adapt to your needs.
- `OWID_COVID_SECRETS`: Path to the data pipeline secrets file (`yaml` format).

You can add the environment variables by adding the following lines to your shell config file (e.g. `.bashrc` or `.bash_profile`):

```
export OWID_COVID_PROJECT_DIR=/Users/username/projects/covid-19-data
export OWID_COVID_CONFIG=${OWID_COVID_PROJECT_DIR}/scripts/config.yaml
export OWID_COVID_SECRETS=${OWID_COVID_PROJECT_DIR}/scripts/secrets.yaml
```

Note that this is an example and you are free to choose other paths as long as they point to the respective files.

## Pipeline configuration file
The configuration file is required to correctly run the COVID-19 vaccination and testing data pipelines (might be
extended to other pipelines). Find below a sample with its structure, you can also check [the one we use](../config_new.yaml). 

Note that all fields are required, even if left empty.

```yaml
pipeline:

  # Vaccination data pipeline
  vaccinations:
    # Get step
    get:
      parallel:  # Use parallelization (bool)
      countries:  # Countries to collect data for (list)
      njobs:  # Number of threads when parallel=True (int)
      skip_countries:  # Countries to skip data collection for (list)
    # Process step
    process:
      skip_complete:  # Countries to skip data processing (list)
      skip_monotonic_check:
      skip_anomaly_check:  # Skip anomaly checks for these countries, dates and metrics (dict)
        Australia:  # Country name, Australia left as an example (list)
          - date:  # Date to avoid check for (str YYYY-MM-DD)
            metrics:  # Metric to avoid check for (str)
    # Generate step
    generate:
    # Export step
    export:

  # Testing data pipeline
  testing:
    # Get step
    get:
      parallel:  # Use parallelization (bool)
      countries:  # Countries to collect data for (list)
      njobs:  # Number of threads when parallel=True (int)
      skip_countries:  # Countries to skip data collection for (list)
    # Process step
    process:
    # Generate step
    generate:
    # Export step
    export:
```

## Pipeline secrets file
We use the secrets file to update internal flows with the output of the pipeline (fields `vax` and `test`). **There is only one mandatory field: `google.clients_secrets`**, which is needed to interact with Google Drive / Google Sheets based sources (more on how to get it [here](#how-can-i-get-the-google-client_secretsjson-file)).

Note that this file is not shared, as it may contain sensitive data.

```yaml
# Google configuration (dict)
google:
  client_secrets:  # Path to google client_secrets.json file
  mail:  # Email (str), OPTIONAL

# Vaccination configuration (dict), OPTIONAL
vax:
  post:  # OWID Vaccination internal post link (str)
  sheet_id:  # OWID Vaccination internal spredsheet ID, where manual imports happen (str)

# Testing configuration (dict), OPTIONAL
test:
  post:  # OWID Testing internal post link (str)
  sheet_id:  # OWID Testing internal spredsheet ID, where manual imports happen (str)
  sheet_id_extra:  # OWID Extra Testing internal spredsheet ID, where attempted countries are listed (str)

# Twitter configuration (dict), OPTIONAL
twitter:
  consumer_key:  # Consumer key (str)
  consumer_secret:  # Consumer secret (str)
  access_secret:  # Access secret (str)
  access_token:  # Acces token (str)
```


## FAQs
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
`~/.config/owid/clients_secrets.json`.

### More questions?
Raise an [issue](https://github.com/owid/covid-19-data/issues), we are happy to help!