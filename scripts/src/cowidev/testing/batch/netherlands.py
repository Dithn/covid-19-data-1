import pandas as pd
from cowidev.utils.web import request_json
from cowidev.testing import CountryTestBase


class Netherlands(CountryTestBase):
    location = "Netherlands"
    units = "tests performed"
    source_label = "Dutch National Institute for Public Health and the Environment"
    source_url = "https://data.rivm.nl/covid-19/COVID-19_uitgevoerde_testen.json"
    source_url_ref = "https://data.rivm.nl/covid-19/"
    notes = pd.NA
    rename_columns = {"Date_of_statistics": "Date", "Tested_with_result": "Daily change in cumulative total"}

    def read(self) -> pd.DataFrame:
        data = request_json(self.source_url)
        df = pd.DataFrame.from_records(
            data, columns=["Date_of_statistics", "Tested_with_result", "Security_region_name", "Tested_positive"]
        )
        df = df.groupby("Date_of_statistics").sum().reset_index()
        return df

    def pipe_positive_rate(self, df: pd.DataFrame):
        df["Positive rate"] = (
            (df["Tested_positive"].rolling(7).mean()).div((df["Tested_with_result"].rolling(7).mean())).round(3)
        )
        return df

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.pipe(self.pipe_positive_rate).pipe(self.pipe_rename_columns).pipe(self.pipe_metadata)

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Netherlands().export()
