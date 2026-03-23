import pandas as pd
from cowidev.testing import CountryTestBase


class Slovakia(CountryTestBase):
    location: str = "Slovakia"
    units: str = "tests performed"
    source_label: str = "Ministry of Health"
    notes: str = "Ministry of Health via https://github.com/Institut-Zdravotnych-Analyz"
    source_url: str = "https://github.com/Institut-Zdravotnych-Analyz/covid19-data/raw/main/DailyStats/OpenData_Slovakia_Covid_DailyStats.csv"
    source_url_ref: str = "https://github.com/Institut-Zdravotnych-Analyz/covid19-data"
    rename_columns: dict = {"Datum": "Date"}

    def read(self) -> pd.DataFrame:
        """Read data from source"""
        df = pd.read_csv(
            self.source_url,
            sep=";",
            usecols=["Datum", "Dennych.PCR.testov", "AgTests", "Dennych.PCR.prirastkov", "AgPosit"],
        )
        return df

    def pipe_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipes metrics"""
        df = df.sort_values("Date")
        return df.assign(
            **{
                "positive": df["Dennych.PCR.prirastkov"].fillna(0) + df["AgPosit"].fillna(0),
                "Daily change in cumulative total": df["Dennych.PCR.testov"].fillna(0) + df["AgTests"].fillna(0),
            }
        )

    def pipe_pr(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate positive rate"""
        return df.assign(
            **{
                "Positive rate": df.positive.rolling(7)
                .mean()
                .div(df["Daily change in cumulative total"].rolling(7).mean())
                .round(3)
            }
        )

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline for data"""
        return df.pipe(self.pipe_rename_columns).pipe(self.pipe_metrics).pipe(self.pipe_pr).pipe(self.pipe_metadata)

    def export(self):
        """Export data to CSV"""
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Slovakia().export()
