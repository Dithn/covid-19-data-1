import pandas as pd

from cowidev.utils.web import request_json
from cowidev.utils.clean import clean_date_series
from cowidev.testing import CountryTestBase


class India(CountryTestBase):
    location = "India"
    units = "samples tested"
    source_label = "Indian Council of Medical Research"
    source_url = "https://raw.githubusercontent.com/datameet/covid19/master/data/icmr_testing_status.json"
    source_url_ref = "https://github.com/datameet/covid19"
    notes = "Made available by DataMeet on GitHub"
    rename_columns = {"report_time": "Date", "samples": "Cumulative total"}

    def read(self) -> pd.DataFrame:
        data = request_json(self.source_url)
        data = [x["value"] for x in data["rows"]]
        df = pd.DataFrame.from_records(data, columns=["report_time", "samples"])  # Load only columns needed
        df["report_time"] = clean_date_series(df["report_time"], "%Y-%m-%dT%H:%M:%S.%f%z")  # Clean date
        return df

    def pipe_filter_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.drop_duplicates(subset="Cumulative total")
            .drop_duplicates(subset="Date")
            .drop(df[df["Date"] == "2021-09-02"].index)
        )

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.pipe(self.pipe_rename_columns).pipe(self.pipe_filter_rows).pipe(self.pipe_metadata)

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    India().export()
