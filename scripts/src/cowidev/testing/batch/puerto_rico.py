import pandas as pd

from cowidev.testing import CountryTestBase
from cowidev.utils import clean_date_series


class PuertoRico(CountryTestBase):
    location = "Puerto Rico"
    source_url = "https://healthdata.gov/api/views/j8mb-icvb/rows.csv"
    source_url_ref = "https://healthdata.gov/dataset/COVID-19-Diagnostic-Laboratory-Testing-PCR-Testing/j8mb-icvb"
    source_label = "Department of Health & Human Services"
    units = "tests performed"
    rename_columns = {"date": "Date"}

    def read(self):
        df = pd.read_csv(
            self.source_url,
            usecols=["date", "state_name", "new_results_reported", "overall_outcome"],
            parse_dates=["date"],
        )
        return df

    def pipe_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        # daily change in positive tests
        pos = (
            df[(df["overall_outcome"] == "Positive") & (df["state_name"] == "Puerto Rico")]
            .groupby("Date", as_index=False)
            .agg(**{"Daily change in positive total": ("new_results_reported", sum)})
        ).sort_values("Date")

        # daily change in total tests
        df = (
            df[df["state_name"] == "Puerto Rico"]
            .groupby(["Date"], as_index=False)
            .agg(**{"Daily change in cumulative total": ("new_results_reported", sum)})
        ).sort_values("Date")

        # generate positive rate
        df["Positive rate"] = (
            (pos["Daily change in positive total"].rolling(7).mean())
            / (df["Daily change in cumulative total"].rolling(7).mean())
        ).round(3)
        df["Positive rate"][df["Date"] < "2020-03-24"] = pd.NA

        df = df[df["Daily change in cumulative total"] != 0]
        return df

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(Date=clean_date_series(df.Date, "%Y-%m-%d"))

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.pipe(self.pipe_rename_columns).pipe(self.pipe_metrics).pipe(self.pipe_date).pipe(self.pipe_metadata)
        return df

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    PuertoRico().export()
