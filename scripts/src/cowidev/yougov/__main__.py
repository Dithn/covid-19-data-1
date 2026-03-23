"""
THIS SCRIPT HAS BEEN DEPRECATED.


Please refer to https://github.com/owid/covid-19-data/blob/master/public/data/DATA.md for more details.
"""

import os
import json
import datetime
import requests

from tqdm import tqdm
import numpy as np
import pandas as pd

from cowidev import PATHS
from cowidev.utils.clean.dates import DATE_FORMAT


DEBUG = False
DATASET_NAME = "YouGov-Imperial COVID-19 Behavior Tracker"

# MIN_RESPONSES: country-date-question observations with less than this
# many valid responses will be dropped. If "None", no observations will
# be dropped.
MIN_RESPONSES = 100

# FREQ: temporal level at which to aggregate the individual survey
# responses, passed as the `freq` argument to
# pandas.Series.dt.to_period. Must conform to a valid Pandas offset
# string (e.g. 'M' = "month", "W" = "week").
FREQ = "M"

# ZERO_DAY: reference date for internal yearIsDay Grapher usage.
ZERO_DAY = "2020-01-21"

# File paths
PROJECT_DIR = PATHS.PROJECT_DIR

INPUT_PATH = os.path.join(PROJECT_DIR, "scripts", "input", "yougov")
OUTPUT_PATH = os.path.join(PROJECT_DIR, "scripts", "grapher")
MAPPING_PATH = os.path.join(INPUT_PATH, "mapping.csv")
MAPPING_VALUES_PATH = os.path.join(INPUT_PATH, "mapped_values.json")

MAPPING = pd.read_csv(MAPPING_PATH, na_values=None)
MAPPING["label"] = MAPPING["label"].str.lower()
with open(MAPPING_VALUES_PATH, "r") as f:
    MAPPED_VALUES = json.load(f)


class YouGov:
    def __init__(self, output_path: str, debug: bool = False):
        self.source_url = "https://github.com/YouGov-Data/covid-19-tracker/raw/master"
        self.debug = debug
        self.output_path = output_path
        self.dataset_name = DATASET_NAME

    @property
    def output_csv_path(self):
        return os.path.join(self.output_path, f"{self.dataset_name}.csv")

    @property
    def output_csv_path_composite(self):
        return os.path.join(self.output_path, f"{self.dataset_name}, composite variables.csv")

    def _get_source_url_country(self, country, extension):
        return f"{self.source_url}/data/{country}.{extension}"

    @property
    def source_url_master(self):
        return f"{self.source_url}/countries.csv"

    @property
    def list_countries(self):
        """Get list of countries to download."""
        # Get list of countries
        countries = list(pd.read_csv(self.source_url_master, header=None)[0])
        if self.debug:
            return countries[:3]
        return countries

    def read(self):
        """Read data. Reads multiple countries and concatenates them into one file."""
        # Load countries
        all_data = []
        for country in tqdm(self.list_countries):
            tqdm.write(country)
            df = self.read_country(country)
            all_data.append(df)
        # Build DataFrame
        df = pd.concat(all_data, axis=0)
        if df.columns.nunique() != df.columns.shape[0]:
            raise ValueError("There are one or more duplicate columns, which may cause unexpected errors.")
        return df

    def read_country(self, country):
        """Read individual country data."""
        # Load df from web
        extensions = ["csv", "zip"]
        df = None
        for ext in extensions:
            url = self._get_source_url_country(country, ext)
            if requests.get(url).ok:
                df = self._read_country_from_web(url, ext)
        if df is None:
            raise ValueError(f"No file found for {country}")
        # Parse date field
        df = df.assign(country=country)
        df.columns = df.columns.str.lower()
        return df

    def _read_country_from_web(self, source_url_country, extension):
        """Given URL, reads individual country data."""
        if extension == "csv":
            extension = None
        elif extension != "zip":
            raise ValueError("Invalid extension. Accepted are 'csv' and 'zip'.")
        return pd.read_csv(
            source_url_country,
            low_memory=False,
            na_values=[
                "",
                "Not sure",
                " ",
                "Prefer not to say",
                "Don't know",
                98,
                "Don't Know",
                "Not applicable - I have already contracted Coronavirus (COVID-19)",
                "Not applicable - I have already contracted Coronavirus",
            ],
            compression=extension,
        )

    def pipeline_csv(self, df: pd.DataFrame):
        df = (
            df.pipe(_format_date)
            .pipe(_subset_and_rename_columns)
            .pipe(_preprocess_cols)
            .pipe(_derive_cols)
            .pipe(_standardize_entities)
            .pipe(_aggregate)
        )
        df_comp = _create_composite_cols(df)
        if df_comp is not None:
            df_comp = df_comp.pipe(_rename_columns).pipe(_reorder_columns)
        df = df.pipe(_round).pipe(_rename_columns).pipe(_reorder_columns)
        return df, df_comp

    def export(self):
        df = self.read()
        df, df_comp = df.pipe(self.pipeline_csv)

        # Export
        if df_comp is not None:
            df_comp.to_csv(self.output_csv_path_composite, index=False)
        df.to_csv(self.output_csv_path, index=False)


def _format_date(df: pd.DataFrame):
    df.loc[:, "date"] = pd.to_datetime(df.endtime, format="%d/%m/%Y %H:%M", errors="coerce")
    mask = df.date.isnull()
    df.loc[mask, "date"] = pd.to_datetime(df[mask]["date"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
    return df


def _subset_and_rename_columns(df):
    """keeps only the survey questions with keep=True in mapping.csv and
    renames columns.
    Note: we do not use `df.rename(columns={...})` because for some columns we
        derive multiple variables.
    """
    assert MAPPING.keep.isin([True, False]).all(), 'All values in "keep" column of `MAPPING` must be True or False.'
    assert (
        MAPPING["code_name"].duplicated().sum() == 0
    ), "All rows in the `code_name` field of mapping.csv must be unique."
    index_cols = ["country", "date"]
    df2 = df[index_cols]
    for row in MAPPING[MAPPING.keep & ~MAPPING.derived].itertuples():
        df2.loc[:, row.code_name] = df[row.label]
    df2 = df2.dropna(subset=["date"])
    return df2


def _preprocess_cols(df):
    for row in MAPPING[MAPPING.preprocess.notnull()].itertuples():
        if row.code_name in df.columns:
            df.loc[:, row.code_name] = df[row.code_name].replace(MAPPED_VALUES[row.preprocess])
            uniq_values = set(MAPPED_VALUES[row.preprocess].values())
            assert (
                df.loc[:, row.code_name].drop_duplicates().dropna().isin(uniq_values).all()
            ), f"One or more non-NaN values in {row.code_name} are not in {uniq_values}"
    return df


def _derive_cols(df):
    derived_variables_to_keep = MAPPING[MAPPING["derived"] & MAPPING["keep"]].code_name.unique().tolist()
    if "covid_vaccinated_or_willing" in derived_variables_to_keep:
        # constructs the covid_vaccinated_or_willing variable
        # pd.crosstab(df['vac'].fillna(-1), df['vac_1'].fillna(-1))
        vac_min_val = min(
            MAPPED_VALUES[
                MAPPING.loc[
                    MAPPING["code_name"] == "covid_vaccine_received_one_or_two_doses",
                    "preprocess",
                ].squeeze()
            ].values()
        )
        vac_max_val = max(
            MAPPED_VALUES[
                MAPPING.loc[
                    MAPPING["code_name"] == "covid_vaccine_received_one_or_two_doses",
                    "preprocess",
                ].squeeze()
            ].values()
        )
        vac_1_max_val = max(
            MAPPED_VALUES[
                MAPPING.loc[
                    MAPPING["code_name"] == "willingness_covid_vaccinate_this_week",
                    "preprocess",
                ].squeeze()
            ].values()
        )

        assert not (
            (df["covid_vaccine_received_one_or_two_doses"] == vac_max_val)
            & df["willingness_covid_vaccinate_this_week"].notnull()
        ).any(), (
            "Expected all vaccinated respondents to NOT be asked whether they would "
            "get vaccinated, but found at least one vaccinated respondent who was "
            "asked the latter question."
        )
        assert not (
            (df["covid_vaccine_received_one_or_two_doses"] == vac_min_val)
            & df["willingness_covid_vaccinate_this_week"].isnull()
        ).any(), (
            "Expected all unvaccinated respondents to be asked whether they would "
            "get vaccinated, but found at least one unvaccinated respondent who was "
            "not asked the latter question."
        )

        df.loc[:, "covid_vaccinated_or_willing"] = (
            (df["covid_vaccine_received_one_or_two_doses"] == vac_max_val)
            | (df["willingness_covid_vaccinate_this_week"] == vac_1_max_val)
        ).astype(int) * vac_max_val
        df.loc[
            df["covid_vaccine_received_one_or_two_doses"].isnull()
            & df["willingness_covid_vaccinate_this_week"].isnull(),
            "covid_vaccinated_or_willing",
        ] = np.nan

    return df


def _standardize_entities(df):
    df.loc[:, "entity"] = df.country.apply(lambda x: x.replace("-", " ").title())
    df = df.drop(columns=["country"])
    return df


def _aggregate(df):
    s_period = df["date"].dt.to_period(FREQ)
    if FREQ == "M":
        df.loc[:, "date_mid"] = s_period.dt.start_time.dt.date + datetime.timedelta(days=14)
    else:
        df.loc[:, "date_mid"] = (s_period.dt.start_time + (s_period.dt.end_time - s_period.dt.start_time) / 2).dt.date
    today = datetime.datetime.utcnow().date()
    if df["date_mid"].max() > today:
        df.loc[:, "date_mid"] = df["date_mid"].replace({df["date_mid"].max(): today})

    questions = [q for q in MAPPING.code_name.tolist() if q in df.columns]

    # computes the mean for each country-date-question observation
    # (returned in long format)
    df_means = (
        df.groupby(["entity", "date_mid"])[questions]
        .mean()
        .rename_axis("question", axis=1)
        .stack()
        .rename("mean")
        .to_frame()
    )

    # counts the number of non-NaN responses for each country-date-question
    # observation (returned in long format)
    df_counts = (
        df.groupby(["entity", "date_mid"])[questions]
        .apply(lambda gp: gp.notnull().sum())
        .rename_axis("question", axis=1)
        .stack()
        .rename("num_responses")
        .to_frame()
    )

    df_agg = pd.merge(
        df_means,
        df_counts,
        left_index=True,
        right_index=True,
        how="outer",
        validate="1:1",
    )

    if MIN_RESPONSES:
        df_agg = df_agg[df_agg["num_responses"] >= MIN_RESPONSES]

    # converts dataframe back to wide format.
    df_agg = df_agg.unstack().reset_index()
    new_columns = []
    for lvl0, lvl1 in df_agg.columns:
        if lvl1:
            if lvl0 == "num_responses":
                col = f"{lvl1}__{lvl0}"
            else:
                col = lvl1
        else:
            col = lvl0
        new_columns.append(col)
    df_agg.columns = new_columns
    df_agg.rename(columns={"date_mid": "date"}, inplace=True)

    # constructs date variable for internal Grapher usage.
    df_agg.loc[:, "date_internal_use"] = (
        df_agg["date"] - datetime.datetime.strptime(ZERO_DAY, DATE_FORMAT).date()
    ).dt.days
    df_agg.drop("date", axis=1, inplace=True)

    return df_agg


def _create_composite_cols(df):
    ffill_limit = 7
    vac_var_id = 145610
    try:
        res = requests.get(f"https://ourworldindata.org/grapher/data/variables/{vac_var_id}.json")
        assert res.ok
        vac_data = json.loads(res.content)
        var_name = vac_data["variables"][f"{vac_var_id}"]["name"]
        assert (
            ZERO_DAY == vac_data["variables"][f"{vac_var_id}"]["display"]["zeroDay"]
        ), "Zero days do not match. Data merge will not be correct."
        df_vac = pd.DataFrame(
            {
                "date": vac_data["variables"][f"{vac_var_id}"]["years"],
                "entity": [
                    vac_data["entityKey"][f"{ent}"]["name"]
                    for ent in vac_data["variables"][f"{vac_var_id}"]["entities"]
                ],
                var_name: vac_data["variables"][f"{vac_var_id}"]["values"],
            }
        ).sort_values(["entity", "date"], ascending=True)
        date_range = list(range(df_vac["date"].min(), df_vac["date"].max() + 1))
        df_vac[df_vac["entity"] == "United States"].set_index("date").reindex(date_range)
        df_vac = (
            df_vac.groupby("entity")
            .apply(lambda gp: gp.set_index("date").reindex(date_range))
            .drop("entity", axis=1)
            .reset_index()
            .sort_values(["entity", "date"])
        )
        df_vac[var_name] = df_vac.groupby("entity")[var_name].apply(lambda gp: gp.ffill(limit=ffill_limit)).dropna()
        df_vac.dropna(subset=[var_name], inplace=True)

        vac_entities = df_vac["entity"].unique()
        yougov_entities_not_found = [ent for ent in df["entity"].drop_duplicates() if ent not in vac_entities]
        assert len(yougov_entities_not_found) < (df["entity"].drop_duplicates().shape[0] * 0.1), (
            "Expected nearly all YouGov entities to be in vaccination data, but "
            "failed to find >10% of YouGov entities in the vaccination data. "
            f"Entities not found: {yougov_entities_not_found}"
        )

        will_cols = [
            "willingness_covid_vaccinate_this_week",
            "unwillingness_covid_vaccinate_this_week",
            "uncertain_covid_vaccinate_this_week",
        ]
        df_temp = pd.merge(
            df[
                [
                    "entity",
                    "date_internal_use",
                ]
                + will_cols
            ],
            df_vac[["entity", "date", var_name]],
            left_on=["entity", "date_internal_use"],
            right_on=["entity", "date"],
            how="inner",
            validate="1:1",
        )
        df_temp.dropna(subset=will_cols, inplace=True)
        df_temp[var_name] = df_temp[var_name].round(2)

        # converts willingness to get vaccinated variables to a percentage of the
        # overall population, instead of percentage of the unvaccinated population.
        df_temp["willingness_covid_vaccinate_this_week_pct_pop"] = (
            (100 - df_temp[var_name]) * (df_temp["willingness_covid_vaccinate_this_week"] / 100)
        ).round(2)
        df_temp["unwillingness_covid_vaccinate_this_week_pct_pop"] = (
            (100 - df_temp[var_name]) * (df_temp["unwillingness_covid_vaccinate_this_week"] / 100)
        ).round(2)
        df_temp["uncertain_covid_vaccinate_this_week_pct_pop"] = (
            (100 - df_temp[var_name]) * (df_temp["uncertain_covid_vaccinate_this_week"] / 100)
        ).round(2)

        cols = [
            var_name,
            "willingness_covid_vaccinate_this_week_pct_pop",
            "unwillingness_covid_vaccinate_this_week_pct_pop",
            "uncertain_covid_vaccinate_this_week_pct_pop",
        ]

        assert all(
            df_temp[cols].sum(axis=1, min_count=len(cols)).dropna().round(1) == 100
        ), f"Expected {cols} to sum to *nearly* 100 for every entity-date observation, prior to rounding adjustment."

        # adjusts one variable to ensure sum of all cols equals exactly
        # 100. Otherwise, rounding errors may lead the sum to be
        # slightly off (e.g. 99.99).
        df_temp[f"{cols[-1]}_adjusted"] = (100 - df_temp[cols[:-1]].sum(axis=1)).round(2)
        assert all((df_temp[cols[-1]] - df_temp[f"{cols[-1]}_adjusted"]).abs() < 0.1), (
            f"Expected rounding adjustment of {cols[-1]} to be minor (< 0.1), "
            "but adjustment was larger than this for one or more entity-date "
            "observations."
        )
        assert all(
            df_temp[cols[:-1] + [f"{cols[-1]}_adjusted"]].sum(axis=1, min_count=len(cols)).dropna().round(2) == 100
        ), f"Expected {cols} to sum to exactly 100 for every entity-date observation, after rounding adjustment."
        df_temp[cols[-1]] = df_temp[f"{cols[-1]}_adjusted"]

        df_temp = df_temp[
            [
                "entity",
                "date_internal_use",
                var_name,
                "willingness_covid_vaccinate_this_week_pct_pop",
                "unwillingness_covid_vaccinate_this_week_pct_pop",
                "uncertain_covid_vaccinate_this_week_pct_pop",
            ]
        ]

    except Exception as e:
        df_temp = None
        print(f"Failed to construct composite variables. Error: {e}")

    return df_temp


def _round(df):
    index_cols = ["entity", "date_internal_use"]
    df = df.set_index(index_cols).round(1).reset_index()
    return df


def _rename_columns(df):
    # renames index columns for use in `update_db`.
    df.rename(columns={"entity": "Country", "date_internal_use": "Year"}, inplace=True)
    return df


def _reorder_columns(df):
    index_cols = ["Country", "Year"]
    data_cols = sorted([col for col in df.columns if col not in index_cols])
    df = df[index_cols + data_cols]
    return df


def main():
    YouGov(output_path=OUTPUT_PATH, debug=DEBUG).export()


if __name__ == "__main__":
    main()
