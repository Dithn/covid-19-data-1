import pandas as pd

from cowidev import PATHS
from cowidev.utils.clean import clean_date_series
from cowidev.utils.web.download import read_csv_from_url

METADATA_BASE = {
    "source_url": "https://opendata.ecdc.europa.eu/covid19/hospitalicuadmissionrates/csv/data.csv",
    "source_url_ref": "https://www.ecdc.europa.eu/en/publications-data/download-data-hospital-and-icu-admission-rates-and-current-occupancy-covid-19",
    "source_name": "European Centre for Disease Prevention and Control",
}


POPULATION = pd.read_csv(
    PATHS.INTERNAL_INPUT_UN_POPULATION_FILE,
    usecols=["entity", "population"],
)
EXCLUDED_COUNTRIES = [
    "Austria",
    "Belgium",
    "Czechia",
    "Denmark",
    "Finland",
    "France",
    "Germany",
    "Italy",
    "Netherlands",
    "Portugal",
    "Spain",
    "Sweden",
]


def download_data():
    df = pd.read_csv(
        METADATA_BASE["source_url"], usecols=["country", "indicator", "date", "value", "year_week"],
    )
    df = df[-df.country.isin(EXCLUDED_COUNTRIES)]
    df = df.drop_duplicates()
    df = df.rename(columns={"country": "entity"})
    return df


def update_metadata(df):
    entities = df.entity.unique()
    METADATA = [{**METADATA_BASE, **{"entity": entity}} for entity in entities]
    return METADATA


def pipe_remove_duplicates(df):
    return df.drop_duplicates(subset=["entity", "indicator", "date"], keep=False)


def pipe_undo_100k(df):
    df = pd.merge(df, POPULATION, on="entity", how="left")
    assert df[df.population.isna()].shape[0] == 0, "Country missing from population file"
    df.loc[df["indicator"].str.contains(" per 100k"), "value"] = df["value"].div(100000).mul(df["population"])
    df.loc[:, "indicator"] = df["indicator"].str.replace(" per 100k", "")
    return df


def pipe_week_to_date(df):
    df["date"] = clean_date_series(df.date, "%Y-%m-%d")
    if df.date.dtypes == "int64":
        df["date"] = clean_date_series(df.date, "%Y%m%d")
    daily_records = df[df["indicator"].str.contains("Daily")]
    date_week_mapping = daily_records[["year_week", "date"]].groupby("year_week", as_index=False).max()
    weekly_records = df[df["indicator"].str.contains("Weekly")].drop(columns="date")
    weekly_records = pd.merge(weekly_records, date_week_mapping, on="year_week")
    df = pd.concat([daily_records, weekly_records]).drop(columns="year_week")
    return df


def main():
    df = download_data()
    METADATA = update_metadata(df)
    df = df.pipe(pipe_remove_duplicates).pipe(pipe_undo_100k).pipe(pipe_week_to_date).drop(columns=["population"])
    return df, METADATA


if __name__ == "__main__":
    main()
