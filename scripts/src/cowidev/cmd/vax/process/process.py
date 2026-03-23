import os
from datetime import datetime

import pandas as pd
from pandas.core.base import DataError
from pandas.errors import ParserError
import click

from cowidev import PATHS
from cowidev.utils.params import CONFIG
from cowidev.utils.utils import export_timestamp, get_traceback
from cowidev.cmd.vax.process.utils import process_location
from cowidev.cmd.commons.utils import StepReport


@click.command(name="process", short_help="Step 2: Process scraped vaccination data from primary sources.")
@click.pass_context
def click_vax_process(ctx):
    """Process data in folder scripts/output/vaccinations/.

    By default, the default values for OPTIONS are those specified in the configuration file. The configuration file is
    a YAML file with the pipeline settings. Note that the environment variable `OWID_COVID_CONFIG` must be pointing to
    this file. We provide a default config file in the project folder scripts/config.yaml.

    OPTIONS passed via command line will overwrite those from configuration file.

    Example:
    Process all country data.

        cowid vax process
    """

    report_msg = main_process_data(
        path_input_files=PATHS.INTERNAL_OUTPUT_VAX_MAIN_DIR,
        path_output_files=PATHS.DATA_VAX_COUNTRY_DIR,
        path_output_meta=PATHS.INTERNAL_OUTPUT_VAX_META_FILE,
        column_location="location",
        process_location=process_location,
        path_output_status=PATHS.INTERNAL_OUTPUT_VAX_STATUS_PROCESS,
        path_output_status_ts=PATHS.INTERNAL_OUTPUT_VAX_STATUS_PROCESS_TS,
        log_header="VAX",
        skip_complete=CONFIG.pipeline.vaccinations.process.skip_complete,
        skip_monotonic=CONFIG.pipeline.vaccinations.process.skip_monotonic_check,
        skip_anomaly=CONFIG.pipeline.vaccinations.process.skip_anomaly_check,
        logger=ctx.obj["logger"],
    )
    if ctx.obj["server"]:
        report_msg.to_slack()
        print(report_msg)


def main_process_data(
    path_input_files: str,
    path_output_files: str,
    path_output_meta: str,
    column_location: str,
    process_location: callable,
    path_output_status: str,
    path_output_status_ts: str,
    log_header: str,
    logger,
    skip_complete: list = None,
    skip_monotonic: dict = {},
    skip_anomaly: dict = {},
):
    # TODO: Generalize
    logger.info("-- Processing data... --")
    # Get data from sheets (i.e. manual data)
    logger.info("Getting data from vax metadata...")
    df_countries = pd.read_csv(PATHS.INTERNAL_INPUT_VAX_COUNTRIES_FILE)
    # Get automated-country data
    logger.info("Getting data from internal output...")
    locations = df_countries.loc[:, "location"].tolist()
    filepaths = [os.path.join(path_input_files, f"{location}.csv") for location in locations]
    dfs = [read_csv(filepath) for filepath in filepaths]
    # Concatenate list of dataframes

    # Check that no location is present in both manual and automated data
    # _check_no_overlapping_manual_auto(dfs_manual, dfs_auto)

    # vax = [v for v in vax if v.location.iloc[0] == "Pakistan"]  # DEBUG
    # Process locations
    def _process_location_and_move_file(df):
        if column_location not in df:
            raise ValueError(f"Column `{column_location}` missing. df: {df.tail(5)}")
        country = df.loc[0, column_location]
        if country.lower() not in skip_complete:
            # Process dataframe
            monotonic_check_skip = skip_monotonic.get(df.loc[0, column_location], [])
            anomaly_check_skip = skip_anomaly.get(df.loc[0, column_location], [])
            try:
                df = process_location(df, monotonic_check_skip, anomaly_check_skip)
            except Exception as err:
                success = False
                error_msg = get_traceback(err)
                error_short_msg = str(err)
                logger.error(f"{log_header} - {country}: FAILED ❌ {err}")
            except:
                success = False
                error_msg = "Error"
            else:
                # Export
                df.to_csv(os.path.join(path_output_files, f"{country}.csv"), index=False)
                logger.info(f"{log_header} - {country}: SUCCESS ✅")
                success = True
                error_msg = error_short_msg = ""
            finally:
                return {
                    "location": country,
                    "success": success,
                    "skipped": False,
                    "error": error_msg,
                    "error_short": error_short_msg,
                    "timestamp": datetime.utcnow().replace(microsecond=0).isoformat(),
                }
        else:
            logger.info(f"{country}: SKIPPED 🚧")
            return {
                "location": country,
                "success": None,
                "skipped": True,
                "error": "",
                "timestamp": datetime.utcnow().replace(microsecond=0).isoformat(),
            }
        # return {"location": country, "error": ""}

    logger.info("Processing and exporting data...")
    # Process all countries
    df_status = pd.DataFrame([_process_location_and_move_file(df) for df in dfs]).set_index("location")

    # Export metadata
    df_countries = df_countries[df_countries["include"]].sort_values(by="location")
    _check_metadata(df_countries)
    df_countries.to_csv(path_output_meta, index=False)
    logger.info("Exported ✅")

    # Export status
    df_status.to_csv(path_output_status)
    export_timestamp(path_output_status_ts)
    # print_eoe()
    report_msg = _build_server_message(df_status, domain="Vaccinations")
    return report_msg


def _build_server_message(df_status, domain):
    if (df_status.success == False).any():
        dix_failed = df_status.loc[df_status.success == False, "error_short"].to_dict()
        module_error_log = ""
        for module, error in dix_failed.items():
            module_error_log += f"* {module}\n {error}\n"
            module_error_log += "--------------------------------------------------------\n\n"
        module_list = ", ".join(dix_failed.keys())
        title = f"{domain} - [process] step failed"
        text = f"Modules failed: {len(dix_failed)}\n{module_list}\n\n```{module_error_log}```"
        type = "warning"
    else:
        title = f"{domain} - [process] step run successfully"
        text = "All modules executed successfully"
        type = "success"
    return StepReport(
        title=title,
        text=text,
        type=type,
    )


def read_csv(filepath):
    try:
        return pd.read_csv(filepath)
    except:
        raise ParserError(f"Error tokenizing data from file {filepath}")


def _check_no_overlapping_manual_auto(dfs_manual, dfs_auto):
    locations_manual = set([df.location[0] for df in dfs_manual])
    locations_auto = set([df.location[0] for df in dfs_auto])
    locations_common = locations_auto.intersection(locations_manual)
    if len(locations_common) > 0:
        raise DataError(f"The following locations have data in both output/main_data and GSheet: {locations_common}")


def _check_metadata(df: pd.DataFrame):
    """Check metadata LOCATIONS tab has valid format."""
    # Check columns
    cols_stable = [
        "location",
        "source_name",
        "automated",
        "include",
    ]
    cols_extra = [
        "1d_approved",
        "1d_used",
        "1d_codeready",
        "WHO_from",
        "WHO_to",
    ]
    cols = cols_stable + cols_extra
    cols_missing = [col for col in cols if col not in df.columns]
    cols_wrong = [col for col in df.columns if col not in cols]
    if cols_missing:
        raise ValueError(f"LOCATIONS missing column(s): {cols_missing}.")
    if cols_wrong:
        raise ValueError(f"LOCATIONS has invalid column(s): {cols_wrong}.")
    # Check duplicated rows
    location_counts = df.location.value_counts()
    if (location_counts > 1).any(None):
        locations_dup = location_counts[location_counts > 1].index.tolist()
        raise ValueError(f"Duplicated location(s) found in LOCATIONS. Check {locations_dup}")
    if df[cols_stable].isnull().any(None):
        raise ValueError("Check LOCATIONS. Some fields missing (empty / NaNs)")
    # Ensure booleanity of columns automated, include
    if not df.automated.isin([True, False]).all():
        vals = df.automated.unique()
        raise ValueError(f"LOCATIONS column `automated` should only contain TRUE/FALSE. Check {vals}")
    if not df.include.isin([True, False]).all():
        vals = df.include.unique()
        raise ValueError(f"LOCATIONS column `include` should only contain TRUE/FALSE. Check {vals}")