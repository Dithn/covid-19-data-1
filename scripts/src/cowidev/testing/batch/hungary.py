import pandas as pd

from cowidev.testing import CountryTestBase
from cowidev.utils.gdrive import GSheetApi
from cowidev.utils.clean import clean_date_series


class Hungary(CountryTestBase):
    location = "Hungary"
    units = "tests performed"
    source_label = "Government of Hungary"
    source_url_ref = "https://atlo.team/koronamonitor/"
    notes = "Made available by Atlo.team"
    rename_columns = {
        "Dátum": "Date",
        "Új mintavételek száma": "Daily change in cumulative total",
    }

    def read(self) -> pd.DataFrame:
        api = GSheetApi()
        sheet = api.get_worksheet("1e4VEZL1xvsALoOIq9V2SQuICeQrT5MtWfBm32ad7i8Q", "koronahun")
        df = sheet.to_frame()
        return df

    def pipe_filter(self, df):
        return df[(df["Daily change in cumulative total"] != 0) & ~df["Daily change in cumulative total"].isna()]

    def pipe_date(self, df):
        return df.assign(Date=clean_date_series(df["Date"], "%Y-%m-%d"))

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.pipe(self.pipe_rename_columns).pipe(self.pipe_filter).pipe(self.pipe_date).pipe(self.pipe_metadata)

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df, float_format="%.5f")


def main():
    Hungary().export()
