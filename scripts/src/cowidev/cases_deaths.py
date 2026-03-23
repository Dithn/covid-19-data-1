"""Collect Cases/Deaths data"""
from cowidev import PATHS
from cowidev.utils.utils import export_timestamp
from cowidev.utils.catalog import load_table_from_catalog
import os
from termcolor import colored
import pandas as pd


def generate_dataset(logger, server_mode):
    """Generate Cases/Deaths dataset."""
    # Load data from ETL catalog
    tb = load_table_from_catalog(namespace="covid", dataset="cases_deaths", table="cases_deaths")

    # Process
    tb = process_data(tb)

    # Export data
    export_files(tb, logger)

    # logger.info("Generating subnational file…")
    # create_subnational()

    # Export timestamp
    export_timestamp(PATHS.DATA_TIMESTAMP_CASES_DEATHS_FILE)


def process_data(tb):
    # Round values (3)
    cols = [
        "weekly_pct_growth_cases",
        "weekly_pct_growth_deaths",
        "biweekly_pct_growth_cases",
        "biweekly_pct_growth_deaths",
        "new_cases_per_million",
        "new_deaths_per_million",
        "total_cases_per_million",
        "total_deaths_per_million",
        "weekly_cases_per_million",
        "weekly_deaths_per_million",
        "biweekly_cases_per_million",
        "biweekly_deaths_per_million",
        "new_cases_7_day_avg_right",
        "new_deaths_7_day_avg_right",
        "new_cases_per_million_7_day_avg_right",
        "new_deaths_per_million_7_day_avg_right",
        "cfr",
        "cfr_100_cases",
    ]
    tb[cols] = tb[cols].round(3)
    # Reset index
    tb = tb.reset_index()
    # Rename columns
    tb = tb.rename(columns={"country": "location"})
    return tb

def export_files(df, logger):
    # The rest of the CSVs
    succeed = _export_files(df, PATHS.DATA_CASES_DEATHS_DIR)
    if succeed:
        logger.info(
            "Successfully exported CSVs to %s\n" % colored(os.path.abspath(PATHS.DATA_CASES_DEATHS_DIR), "magenta")
        )
    else:
        logger.error("Case/Death export failed.\n")
        raise ValueError("Case/Death export failed.")


def _export_files(tb, output_path):
    # Exclude certain regional aggregates
    excluded_aggregates = {
        'Antarctica',
        'Asia excl. China',
        'World excl. China',
        'World excl. China and South Korea',
        'World excl. China, South Korea, Japan and Singapore'
    }
    tb = tb[~tb["location"].isin(excluded_aggregates)]

    # full_data.csv
    full_data_cols = [
        "date",
        "location",
        "new_cases",
        "new_deaths",
        "total_cases",
        "total_deaths",
        "weekly_cases",
        "weekly_deaths",
        "biweekly_cases",
        "biweekly_deaths",
    ]

    col_metrics = [col for col in full_data_cols if col not in ["date", "location"]]
    df = pd.DataFrame(tb[full_data_cols].dropna(subset=col_metrics, how="all"))
    df.to_csv(
        os.path.join(output_path, "full_data.csv"), index=False
    )

    # Pivot variables (wide format)
    for col_name in col_metrics:
        for suffix in ["", "_per_million"]:
            indicator_name = f"{col_name}{suffix}"
            tb_pivot = tb.pivot(index="date", columns="location", values=indicator_name)
            # move World to first column
            cols = tb_pivot.columns.tolist()
            cols.insert(0, cols.pop(cols.index("World")))
            df = pd.DataFrame(tb_pivot[cols])
            df.to_csv(os.path.join(output_path, f"{indicator_name}.csv"))
    return True
