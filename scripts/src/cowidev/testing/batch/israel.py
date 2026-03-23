import pandas as pd


from cowidev.testing import CountryTestBase
from cowidev.utils import clean_date_series


class Israel(CountryTestBase):
    location = "Israel"
    source_url = {
        "tests" : "https://datadashboardapi.health.gov.il/api/queries/testResultsPerDate",
        "positive" : "https://datadashboardapi.health.gov.il/api/queries/infectedPerDate",
        }
    units = "people tested"
    source_label = "Israel Ministry of Health"
    source_url_ref = "https://datadashboard.health.gov.il/COVID-19/general"
    rename_columns = {
        "date": "Date",
        "amountPersonTested": "Daily change in cumulative total",
        "amount": "positive",
    }
    

    def read(self):
        """Reads data from the source"""
        positive = pd.read_json(self.source_url["positive"])[["date", "amount"]]
        positive = positive[positive.date >= "2020-02-20T00:00:00.000Z"]
        df = pd.read_json(self.source_url["tests"])[["date", "amountPersonTested"]]
        df = df.merge(positive, on="date", how="outer")
        return df
    
    def pipe_pr(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculates the positive rate"""
        return df.assign(
            **{
                "Positive rate": df.positive.rolling(7)
                .sum()
                .div(df["Daily change in cumulative total"].rolling(7).sum())
                .round(3).fillna(0)
            }
        )

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline for the data"""
        df = df.pipe(self.pipe_rename_columns).pipe(self.pipe_pr).pipe(self.pipe_metadata)
        df = df.assign(Date=clean_date_series(df.Date))
        return df

    def export(self):
        """Export to CSV"""
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Israel().export()
