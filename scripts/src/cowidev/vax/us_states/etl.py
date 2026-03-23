import os
import json
from glob import glob

import requests
import pandas as pd

from cowidev import PATHS
from cowidev.vax.utils.utils import make_monotonic


class USStatesETL:
    source_url: str = "https://covid.cdc.gov/covid-data-tracker/COVIDData/getAjaxData?id=vaccination_data"
    cdc_data_path: str = PATHS.INTERNAL_INPUT_CDC_VAX_DIR

    def extract(self):
        self._download_data()
        return self._read_data()

    def _download_data(self):
        data = json.loads(requests.get(self.source_url).content)
        df = pd.DataFrame.from_records(data["vaccination_data"])
        assert len(df) > 0
        df.to_csv(os.path.join(self.cdc_data_path, f"cdc_data_{df.Date.max()}.csv"), index=False)

    def _read_data(self):
        files = glob(os.path.join(self.cdc_data_path, "cdc_data_*.csv"))
        data = [*map(self._read_file, files)]
        return pd.concat(data, ignore_index=True)

    def _read_file(self, filepath):
        df = pd.read_csv(filepath, na_values=[0.0, 0])
        # Each variable present in VARIABLE_MATCHING.keys() will be created based on the variables in
        # VARIABLE_MATCHING.values() by order of priority. If none of the vars can be found, the variable
        # is created as pd.NA
        variable_matching = {
            "total_distributed": ["Doses_Distributed"],
            "total_vaccinations": ["Doses_Administered"],
            "people_vaccinated": ["Administered_Dose1_Recip", "Administered_Dose1"],
            "people_fully_vaccinated": [
                "Series_Complete_Yes",
                "Administered_Dose2_Recip",
                "Administered_Dose2",
            ],
            "total_boosters": ["additional_doses"],
            "total_boosters_2": ["Second_Booster"],
            "total_boosters_biv": ["Bivalent_Booster"],
            "single_shots": ["Series_Complete_Janssen"],
        }
        # Mapping
        for k, v in variable_matching.items():
            for cdc_variable in v:
                if cdc_variable in df.columns:
                    # if k == "total_boosters":
                    #     print(k, cdc_variable, filepath)
                    df = df.rename(columns={cdc_variable: k})
                    break
            if k not in df.columns:
                df[k] = pd.NA
        # Order columns
        df = df[["Date", "LongName", "Census2019"] + [*variable_matching.keys()]]
        return df

    def transform(self, df: pd.DataFrame):
        return (
            df.pipe(pipe_rename_cols)
            .pipe(pipe_total_boosters)
            .pipe(pipe_monotonic_by_state)
            .pipe(pipe_per_capita)
            .pipe(pipe_smoothed)
            .pipe(pipe_usage)
            .drop(columns=["Census2019"])
            .sort_values(["location", "date"])
            .pipe(pipe_select_columns)
            .pipe(pipe_checks)
        )

    def load(self, df: pd.DataFrame, output_path: str) -> None:
        # Export data
        df.to_csv(output_path, index=False)

    def run(self, output_path: str):
        data = self.extract()
        df = self.transform(data)
        self.load(df, output_path)


def pipe_total_boosters(df: pd.DataFrame):
    dfg = df.groupby("location")
    dfs = []
    for df_ in dfg:
        df_ = df_[1].sort_values("date")
        df_ = df_.assign(
            total_boosters=df_["total_vaccinations"]
            - df_["people_vaccinated"]
            - df_["people_fully_vaccinated"]
            + df_["single_shots"].ffill()
        )
        dfs.append(df_)
    df = pd.concat(dfs, ignore_index=True)
    df.loc[df.date < "2021-08-27", "total_boosters"] = pd.NA
    df.loc[df.total_boosters < 0, "total_boosters"] = pd.NA
    return df


def pipe_rename_cols(df):
    col_dict = {
        "Date": "date",
        "LongName": "location",
    }
    return df.rename(columns=col_dict)


def pipe_per_capita(df):
    df["people_fully_vaccinated_per_hundred"] = df.people_fully_vaccinated.div(df.Census2019).mul(100)
    df["total_vaccinations_per_hundred"] = df.total_vaccinations.div(df.Census2019).mul(100)
    df["people_vaccinated_per_hundred"] = df.people_vaccinated.div(df.Census2019).mul(100)
    df["distributed_per_hundred"] = df.total_distributed.div(df.Census2019).mul(100)
    df["total_boosters_per_hundred"] = df.total_boosters.div(df.Census2019).mul(100)
    for var in df.columns:
        if "per_hundred" in var:
            df.loc[df[var].notnull(), var] = df.loc[df[var].notnull(), var].astype(float).round(2)
    return df


def pipe_smoothed(df):
    df = df.sort_values(["date", "location"])
    df["date"] = pd.to_datetime(df["date"])
    df = df.groupby("location", as_index=False).apply(_smooth_state)
    return df


def _smooth_state(df):
    df = df.set_index("date").resample("1D").asfreq().reset_index().sort_values("date")
    df[["location", "Census2019"]] = df[["location", "Census2019"]].ffill()
    interpolated_totals = df["total_vaccinations"].interpolate("linear")
    df["daily_vaccinations"] = (
        (interpolated_totals - interpolated_totals.shift(1)).rolling(7, min_periods=1).mean().round()
    )
    df["daily_vaccinations_raw"] = df.total_vaccinations - df.total_vaccinations.shift(1)
    df["daily_vaccinations_per_million"] = df["daily_vaccinations"].mul(1000000).div(df["Census2019"]).round()
    return df


def pipe_usage(df):
    df["share_doses_used"] = df["total_vaccinations"].div(df["total_distributed"]).round(3)
    return df


def pipe_monotonic_by_state(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("location").apply(make_monotonic, max_removed_rows=None).reset_index(drop=True)


def pipe_select_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df[
        [
            "date",
            "location",
            "total_vaccinations",
            "total_distributed",
            "people_vaccinated",
            "people_fully_vaccinated_per_hundred",
            "total_vaccinations_per_hundred",
            "people_fully_vaccinated",
            "people_vaccinated_per_hundred",
            "distributed_per_hundred",
            "daily_vaccinations_raw",
            "daily_vaccinations",
            "daily_vaccinations_per_million",
            "share_doses_used",
            "total_boosters",
            "total_boosters_per_hundred",
        ]
    ]


def pipe_checks(df: pd.DataFrame) -> pd.DataFrame:
    assert len(df) == len(df[["date", "location"]].drop_duplicates())
    return df


def run_etl(output_path: str):
    etl = USStatesETL()
    etl.run(output_path)


if __name__ == "__main__":
    run_etl("here.csv")
