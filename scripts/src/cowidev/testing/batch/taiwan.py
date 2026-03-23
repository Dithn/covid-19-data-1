import pandas as pd

from cowidev.testing import CountryTestBase
from cowidev.utils import clean_date_series


class Taiwan(CountryTestBase):
    location: str = "Taiwan"
    units: str = "people tested"
    source_label: str = "Taiwan CDC Open Data Portal"
    source_url: str = "https://od.cdc.gov.tw/eic/covid19/covid19_tw_specimen.csv"
    source_url_ref: str = "https://data.cdc.gov.tw/en/dataset/daily-cases-suspected-sars-cov-2-infection_tested"
    rename_columns: dict = {
        "通報日": "Date",
        "Total": "Daily change in cumulative total",
    }

    def read(self) -> pd.DataFrame:
        """Read data from source"""
        df = pd.read_csv(self.source_url, usecols=["通報日", "Total"])
        return df

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert date to datetime"""
        return df.assign(Date=clean_date_series(df["Date"], "%Y/%m/%d"))

    def pipe_filter(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter data"""
        df = df[~df["Daily change in cumulative total"].isna() & df["Daily change in cumulative total"] > 0]
        return df

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline for data"""
        return df.pipe(self.pipe_rename_columns).pipe(self.pipe_date).pipe(self.pipe_filter).pipe(self.pipe_metadata)

    def export(self):
        """Export data to CSV"""
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Taiwan().export()
