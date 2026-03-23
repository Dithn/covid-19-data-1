import pandas as pd

from cowidev.testing import CountryTestBase


class Estonia(CountryTestBase):
    location: str = "Estonia"
    source_url = "https://opendata.digilugu.ee/opendata_covid19_test_county_all.csv"
    source_url_ref = "https://www.terviseamet.ee/et/koroonaviirus/avaandmed"
    source_label = "Estonian Health Board"
    units = "tests performed"
    rename_columns = {"StatisticsDate": "Date", "TotalTests": "Cumulative total"}

    def read(self):
        return pd.read_csv(self.source_url, usecols=["StatisticsDate", "TotalTests"])

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.groupby("StatisticsDate", as_index=False).sum().sort_values("StatisticsDate")
        return df.pipe(self.pipe_rename_columns).pipe(self.pipe_metadata)

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Estonia().export()
