import pandas as pd

from cowidev.testing import CountryTestBase
from cowidev.testing.utils import make_monotonic
from cowidev.utils import clean_date_series, clean_count
from cowidev.utils.web.download import read_csv_from_url


class Australia(CountryTestBase):
    location: str = "Australia"
    units: str = "tests performed"
    notes: str = "Made available by CovidbaseAU"
    source_url: str = "https://covidbaseau.com/historical/COVID-19%20Tests%20Australia.csv"
    source_url_ref: str = "https://covidbaseau.com/tests/"
    source_label: str = "Australian Government Department of Health"
    rename_columns: str = {
        "Total": "Cumulative total",
        # "Daily": "Positive rate",
    }

    def read(self) -> pd.DataFrame:
        df = read_csv_from_url(
            self.source_url,
            header=1,
            usecols=[
                "Date",
                "Total",
                # "Daily",
            ],
        )
        df.drop(df.tail(1).index, inplace=True)
        return df

    def pipe_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.drop(df[df["Cumulative total"] == "-"].index)
        return df.assign(
            **{
                "Cumulative total": df["Cumulative total"].apply(clean_count),
            }
        )

    def pipe_pr(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.drop(df[df["Positive rate"] == "-"].index)
        df["Positive rate"] = (pd.to_numeric(df["Positive rate"].str.replace("%", "")) / 100).round(3)
        return df

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(Date=clean_date_series(df["Date"], "%d %b %y"))

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.pipe(self.pipe_rename_columns)
            .pipe(self.pipe_metrics)
            # .pipe(self.pipe_pr)
            .pipe(self.pipe_date)
            .pipe(self.pipe_metadata)
            .pipe(make_monotonic)
            .sort_values("Date")
            .drop_duplicates(subset=["Cumulative total"], keep="first")
        )

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Australia().export()
