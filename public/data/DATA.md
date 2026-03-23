# Data

**⚠️ This file is currently under construction. ⚠️**

Our COVID-19 data is being migrated into our [catalog](https://docs.owid.io/projects/etl/api/).

## Install our catalog package

```bash
pip install owid-catalog
```

## Usage and preview

Our data is identified by URIs, and for COVID data these go like:

```
data://garden/covid/latest/{DATASET_NAME}/{TABLE_NAME}
```

where:

- `DATASET_NAME` is the name of the dataset (e.g. `case_death`)
- `TABLE_NAME` is the name of the table (e.g. `case_death`)

[→ Learn more about our URIs](https://docs.owid.io/projects/etl/architecture/design/uri/?h=uri#path-for-data)

**Notes**:

- A dataset can be a collection of tables (equivalent to DataFrames). For instance, there might be several files (or DataFrames) in our 'Vaccination' dataset (e.g. global data, US data, etc.).
- Our excess mortality dataset is currently under the namespace `excess_mortality`, i.e. with URIs `data://garden/excess_mortality/latest/{DATASET_NAME}/{TABLE_NAME}`.

### Check all our COVID data

Simply run:

```python
from owid import catalog

# Preview list of available datasets (each row = dataset)
catalogs.find(namespace="covid")

# You can load any dataset (using the row of the above-returned table)
tb = catalogs.find(namespace="covid").iloc[3].load()
```

## Load data

Use an `uri` from the table below[^1].

[^1]: more items are being added to this table shortly.

| **Data category**                | **URI**                                                                                |
| -------------------------------- | -------------------------------------------------------------------------------------- |
| Cases and deaths                 | `garden/covid/latest/cases_deaths/cases_deaths`                                        |
| Excess Mortality                 | `garden/excess_mortality/latest/excess_mortality/excess_mortality`                     |
| Excess Mortality (The Exonomist) | `garden/excess_mortality/latest/excess_mortality_economist/excess_mortality_economist` |
| Hospitalisations                 | `garden/covid/latest/hospital/hospital/`                                               |
| Google Mobility                  | `garden/covid/latest/google_mobility/google_mobility`                                  |
| Policy Response (OxCGRT)         | `garden/covid/latest/oxcgrt_policy/oxcgrt_policy`                                      |
| Indicator decoupling             | `garden/covid/latest/decoupling/decoupling`                                            |
| YouGov                           | `garden/covid/latest/yougov/yougov`                                                    |
| YouGov (Composite)               | `garden/covid/latest/yougov/yougov_composite`                                          |
| Vaccinations (US)                | `garden/covid/latest/vaccinations_us/vaccinations_us`                                  |
| Testing                          | `garden/covid/latest/testing/testing`                                                  |
| Sequencing / Variants            | `garden/covid/latest/sequence/sequence`                                                |
| Decoupling                       | `garden/covid/latest/decoupling/decoupling`                                            |
| Sweden confirmed deaths          | `garden/covid/latest/sweden_covid/sweden_covid/`                                       |
| UK COVID Data                    | `garden/covid/latest/uk_covid/uk_covid/`                                               |

and run the following code:

```python
from owid import catalog

rc = catalog.RemoteCatalog()
uri = "..."
df = rc[uri]
```

## Access metadata

Note that objects `df` are not pure pandas DataFrames, but rather `owid.catalog.Table` datasets, which behave like DataFrames but also contain metadata. You can access metadata like this:

```python
# Table metadata
df.metadata
# Column (or indicator) metadata
df[column_name].metadata
```

[→ Learn more about our metadata](https://docs.owid.io/projects/etl/architecture/metadata/)
