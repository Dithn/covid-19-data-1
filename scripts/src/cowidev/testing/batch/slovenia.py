import pandas as pd

from cowidev.testing import CountryTestBase
from cowidev.utils import clean_date
from cowidev.utils.web import request_json


class Slovenia(CountryTestBase):
    location: str = "Slovenia"
    units: str = "tests performed"
    source_label: str = "National Institute of Public Health"
    notes: str = "National Institute of Public Health via Sledilnik"
    source_url: str = "https://api.sledilnik.org/api/lab-tests"
    source_url_ref: str = "https://covid-19.sledilnik.org/en/data"
    rename_columns: dict = {
        "total.performed.today": "pcr",
        "data.hagt.performed.today": "ag",
        "total.positive.today": "positive_pcr",
        "data.hagt.positive.today": "positive_ag",
    }

    def read(self) -> pd.DataFrame:
        """Read data from source"""
        df = pd.json_normalize(request_json(self.source_url))
        return df

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipes Date"""
        return df.assign(
            Date=df.apply(
                lambda x: clean_date("{0} {1} {2}".format(x["year"], x["month"], x["day"]), "%Y.0 %m.0 %d.0"), axis=1
            ),
        )

    def pipe_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipes metrics"""
        pcr_only = df.assign(
            **{
                "positive": df.positive_pcr.fillna(0),
                "Daily change in cumulative total": df.pcr.fillna(0),
            }
        ).truncate(after=df[df["Date"] == "2022-01-31"].index[0])

        pcr_and_antigen = df.assign(
            **{
                "positive": df.positive_pcr.fillna(0) + df.positive_ag.fillna(0),
                "Daily change in cumulative total": df.pcr.fillna(0) + df.ag.fillna(0),
            }
        ).truncate(before=df[df["Date"] == "2022-02-01"].index[0])

        df = pd.concat([pcr_only, pcr_and_antigen])
        return df

    def pipe_pr(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate positive rate"""
        return df.assign(
            **{
                "Positive rate": df.positive.rolling(7)
                .sum()
                .div(df["Daily change in cumulative total"].rolling(7).sum())
                .round(3)
            }
        )

    def pipe_filter(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter data"""
        return df[df["Daily change in cumulative total"] > 0]

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline for data"""
        return (
            df.pipe(self.pipe_rename_columns)
            .pipe(self.pipe_date)
            .pipe(self.pipe_metrics)
            .pipe(self.pipe_pr)
            .pipe(self.pipe_filter)
            .pipe(self.pipe_metadata)
        )

    def export(self):
        """Export data to CSV"""
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Slovenia().export()
