### ⚠️ This document is still being writen
# Comand tools
This project provides the command tool `cowid`, which eases the process of running multiple processes. Before using the
tool, make sure that you have [correctly setup you working environment](envornment.md).

## Introduction
`cowid` can be understood as an aggregator of command tools. The idea is that you can pass it a command for each data
_pipeline_ (testing, vaccinations, etc.). Additionally, there are subcommands, which can be seen as _steps_ of a certain
pipeline. Finally, these steps accept options (or arguments) which may vary in each case. 

In a nutshell, we can see the tool as a three-layer command:

```
cowid COMMAND SUBCOMMAND [OPTIONS]
```

So for instance, to run step `get` of the testing pipeline you can run:

```
cowid test get
```

To see all the available commands (i.e. pipelines) you can run `cowid --help`. Moreover, `cowid test --help` will display
all subcommands (steps) available for the testing pipeline. Finally, all options for get step of the testing pipeline
can be shown via `cowid test get --help`.


## Available options

### `cowid test`
COVID-19 Testing data pipeline.

#### `cowid test get`
Scrape testing data from primary sources.

```
cowid test get [OPTIONS] [COUNTRIES]...

Runs scraping scripts to collect the data from the primary sources of
COUNTRIES. Data is exported to project folder scripts/output/testing/. By
default, all countries are scraped.

Options:
--parallel / --no-parallel  Parallelize process.  [default: parallel]
--n-jobs INTEGER            Number of threads to use.  [default: -2]
-s, --skip-countries TEXT   List of countries to skip (comma-separated)
--help                      Show this message and exit.
```

##### Example
Scrape data for Australia.

```
cowid test get australia
```

## Configuration
To correctly run `cowid` you need to set up a [configuration file](environment.md#pipeline-configuration-file). 

The default values for OPTIONS are those specified in the configuration file. The configuration file is a YAML file with
the pipeline settings. We provide
a default config file in the project folder [`scripts/config.yaml`](../config_new.yaml).

OPTIONS passed via command line will overwrite those from configuration file.