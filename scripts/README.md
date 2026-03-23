# Development
[![Data](https://img.shields.io/badge/go_to-public_data-purple)](../../../public/data/)
[![documentation](https://img.shields.io/badge/documentation-0055ff)](https://docs.owid.io/projects/covid)

Here you will find all the different scripts and tools that we use to generate [the
complete dataset](https://github.com/owid/covid-19-data/tree/master/public/data). Most of the pipelines have been
integrated into our [`cowidev`](src/cowidev) library. For more details, please visit the official [documentation](https://docs.owid.io/projects/covid)


## Directory overview
|Folder|Description                  |
|------|-----------------------------|
|[`docs/`](docs)|Sphinx documentation source files. See it [live](https://docs.owid.io/projects/covid/).|
|[`grapher/`](grapher)|Internal OWID files to power our [_grapher_](https://ourworldindata.org/owid-grapher) visualizations.|
|[`input/`](input)|External files used to compute derived metrics, such as X-per capita, and aggregate groups, such as 'Asia', etc.|
|[`output/`](output)|Temporary files. Only for development purposes. Use it at your own risk.|
|[`src/cowidev/`](src/cowidev)|`cowidev` library. It contains the code for almost all project's pipelines.|
|[`scripts`](scripts)|Legacy folder. Contains some parts of the code, such as the COVID-19 testing collection scripts. The code is a mixture of R and Python scripts.|
|[`config.yaml`](config.yaml)|Data pipeline configuration file. The default values should be working.|

Our data pipeline exports its outputs to [`public/data`](../public/data).


## Data pipeline
Our data pipeline is built from several pipelines (e.g. vaccinations, testing, etc.), which are executed independently.
for an overview, refer to [our documentation](https://docs.owid.io/projects/covid/en/latest/data-pipeline.html)


## Contribute
We welcome contributions for all of our processes. There are two types of contributions:

- **Maintenance/Enhancements**: Improve processes currently available in the library (e.g. add a new country scrapper for
  the vaccinations data).
- **New features**: Create a new process in the library.

For more details, read our [contribution guideline](https://docs.owid.io/projects/covid/en/latest/contribute.html). 
