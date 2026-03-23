from datetime import datetime

import pandas as pd
from cowidev.testing import CountryTestBase
from cowidev.utils.clean.dates import localdate
from cowidev.utils.web import get_soup


class Suriname(CountryTestBase):
    location: str = "Suriname"
    units: str = "tests performed"
    source_label: str = "Directorate National Security"
    source_url: str = "https://covid-19.sr/"
    source_url_ref: str = "https://covid-19.sr/"

    def read(self) -> pd.DataFrame:
        """Read data from source"""
        body = str(get_soup(self.source_url))

        # Get count
        count = 0
        if "Totaal Testen" in body:
            count = int(body.split("Totaal Testen")[0].split('data-counter-value="')[-1].split('"')[0])
        # Get negative results
        negative = 0
        if "Totaal negatieve" in body:
            negative = int(body.split("Totaal negatieve")[0].split('data-counter-value="')[-1].split('"')[0])

        df = pd.DataFrame(
            {
                "Date": [localdate("America/Paramaribo")],
                "Daily change in cumulative total": [count],
                "positive": [count - negative],
            }
        )
        return df

    def pipe_pr(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Positive Rate"""
        df["Positive rate"] = (
            df["positive"].rolling(7).sum().div(df["Daily change in cumulative total"].rolling(7).sum()).round(3)
        ).fillna(0)
        return df

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline for data processing"""
        return (
            df.pipe(self.pipe_metadata)
            .pipe(self.pipe_merge_current)
            .pipe(self.pipe_pr)
            .drop_duplicates(subset=["Daily change in cumulative total", "positive"], keep="first")
        )

    def export(self):
        """Export data to csv"""
        df = self.read().pipe(self.pipeline)
        # self.export_datafile(df, float_format="%.5f")
        self.export_datafile(df, extra_cols=["positive"])


def main():
    Suriname().export()
