import pandas as pd

from cowidev.utils.web import request_json
from cowidev.utils.clean import clean_date_series, clean_count
from cowidev.testing import CountryTestBase


class Norway(CountryTestBase):
    location: str = "Norway"
    units: str = "people tested"
    source_label: str = "Norwegian Institute of Public Health"
    source_url: str = "https://www.fhi.no/api/chartdata/api/90789"
    source_url_ref: str = (
        "https://www.fhi.no/en/id/infectious-diseases/coronavirus/daily-reports/daily-reports-COVID19"
    )

    def read(self) -> pd.DataFrame:
        """Reads data from source."""
        data = request_json(self.source_url)
        df = pd.DataFrame(data[1:], columns=data[0])
        return df

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cleans date column"""
        return df.assign(Date=clean_date_series(df["Date"], "%Y-%m-%d"))

    def pipe_metrics(self, df: pd.DataFrame):
        """Pipes metrics"""
        df = df.assign(
            **{"Daily change in cumulative total": df.Negative.apply(clean_count) + df.Positive.apply(clean_count)}
        )
        return df[df["Daily change in cumulative total"] > 0].drop_duplicates(subset="Date", keep="last")

    def pipe_pr(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipes pr"""
        return df.assign(**{"Positive rate": df.Percent.div(100).round(3)})

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """pipeline for data"""
        return (
            df.pipe(self.pipe_date)
            .pipe(self.pipe_metrics)
            .pipe(self.pipe_pr)
            .pipe(self.pipe_metadata)
            .sort_values("Date")
        )

    def export(self):
        """Exports data to csv"""
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Norway().export()
