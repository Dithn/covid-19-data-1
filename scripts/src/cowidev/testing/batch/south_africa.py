import pandas as pd

from cowidev.testing import CountryTestBase
from cowidev.utils import clean_date_series


class SouthAfrica(CountryTestBase):
    location: str = "South Africa"
    source_url: str = "https://raw.githubusercontent.com/dsfsi/covid19za/master/data/covid19za_timeline_testing.csv"
    units: str = "people tested"
    source_label: str = "National Institute for Communicable Diseases (NICD)"
    source_url_ref: str = "https://github.com/dsfsi/covid19za"
    notes: str = "Made available by the University of Pretoria on Github"
    rename_columns = {
        "YYYYMMDD": "Date",
        "cumulative_tests": "Cumulative total",
    }

    def read(self):
        return pd.read_csv(self.source_url, usecols=["YYYYMMDD", "cumulative_tests"], parse_dates=["YYYYMMDD"])

    def pipe_add_datapoint(self, df: pd.DataFrame) -> pd.DataFrame:
        # Hard-coded first point for 7 February 2020, missing from GitHub
        datapoint = {
            "Date": "2020-02-07",
            "Country": self.location,
            "Units": self.units,
            "Cumulative total": 42,
            "Source label": self.source_label,
            "Source URL": "https://www.nicd.ac.za/novel-coronavirus-update",
            "Notes": pd.NA,
        }
        return df.append(datapoint, ignore_index=True)

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        df = (
            df.pipe(self.pipe_rename_columns)
            .pipe(pipe_drop_nan)
            .pipe(pipe_metrics)
            .pipe(pipe_date)
            .pipe(self.pipe_metadata)
            .pipe(self.pipe_add_datapoint)
        )
        return df

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def pipe_drop_nan(df: pd.DataFrame):
    return df.dropna(subset=["Cumulative total"])


def pipe_metrics(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("Date", as_index=False).agg(**{"Cumulative total": ("Cumulative total", min)})


def pipe_date(df: pd.DataFrame) -> pd.DataFrame:
    return df.assign(Date=clean_date_series(df.Date, "%Y-%m-%d"))


def main():
    SouthAfrica().export()
