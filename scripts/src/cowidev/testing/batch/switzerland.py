import pandas as pd

from cowidev.testing import CountryTestBase
from cowidev.utils.web import request_json
from cowidev.utils.web.download import read_csv_from_url


class Switzerland(CountryTestBase):
    location: str = "Switzerland"
    units: str = "tests performed"
    source_label: str = "Federal Office of Public Health"
    source_url_ref: str = "https://opendata.swiss/en/dataset/covid-19-schweiz"
    source_url: str = "https://www.covid19.admin.ch/api/data/context"
    rename_columns: str = {
        "datum": "Date",
        "entries": "Daily change in cumulative total",
    }

    def read(self):
        """Read data from source"""
        url = self._get_related_url_from_source(self.source_url)
        df = read_csv_from_url(url, usecols=["datum", "entries", "entries_pos", "geoRegion"])
        return df

    def _get_related_url_from_source(self, source_url: str) -> str:
        """Get related url from source"""
        response = request_json(source_url)
        url = response["sources"]["individual"]["csv"]["daily"]["testPcrAntigen"]
        return url

    def pipe_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process metrics"""
        df = df[df.geoRegion == "CH"]
        df = df.groupby("Date", as_index=False).sum()
        df["Positive rate"] = (
            df.entries_pos.rolling(7).sum().div(df["Daily change in cumulative total"].rolling(7).sum()).round(3)
        )
        df = df[df["Daily change in cumulative total"] > 0].drop(columns=["entries_pos"])
        return df

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline"""
        return df.pipe(self.pipe_rename_columns).pipe(self.pipe_metrics).pipe(self.pipe_metadata)

    def export(self):
        """Export data to csv"""
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Switzerland().export()
