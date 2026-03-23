import re
import json

import pandas as pd

from cowidev.testing import CountryTestBase
from cowidev.utils.web import get_soup
from cowidev.utils.clean import clean_date_series, clean_count


class Armenia(CountryTestBase):
    location: str = "Armenia"
    units: str = "tests performed"
    source_label: str = "National Center for Disease Control"
    source_url_ref: str = "https://ncdc.am/coronavirus/confirmed-cases-by-days/"
    source_url: str = "https://e.infogram.com/"
    regex: dict = {
        "entity": "f5b6e83c-39b1-47c6-a84f-cd7ebaa3b7b1",
        "element": r"window\.infographicData=({.*})",
    }
    rename_columns: dict = {
        "": "Date",
        "Հաստատված դեպքեր": "positive",
        "Բացասական թեստերի արդյունքներ": "negative",
    }

    def read(self) -> pd.DataFrame:
        """Read data from source"""
        data_id = self._get_data_id_from_source(self.source_url_ref)
        data = self._load_data(data_id)
        df = self._build_df(data)
        return df

    def _get_data_id_from_source(self, source_url: str) -> str:
        """Get Data ID from source"""
        soup = get_soup(source_url)
        data_id = soup.find(class_="infogram-embed")["data-id"]
        return data_id

    def _load_data(self, data_id):
        """Load data from source"""
        url = f"{self.source_url}{data_id}"
        soup = get_soup(url)
        match = re.search(self.regex["element"], str(soup))
        if not match:
            raise ValueError("Website Structure Changed, please update the script")
        data = json.loads(match.group(1))
        return data

    def _build_df(self, data: dict) -> pd.DataFrame:
        """Create df from raw data"""
        data = data["elements"]["content"]["content"]["entities"][self.regex["entity"]]["props"]["chartData"]["data"][
            0
        ]
        df = pd.DataFrame(data[1:], columns=data[0])
        return df

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean date"""
        df["Date"] = df.Date.apply(lambda x: re.sub(r"\D", "", x))
        return df.assign(Date=clean_date_series(df["Date"], "%d%m%Y")).sort_values("Date")

    def pipe_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process metrics"""
        return df.assign(
            **{"Daily change in cumulative total": df.positive.apply(clean_count) + df.negative.apply(clean_count)}
        )

    def pipe_pr(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Positive Rate"""
        return df.assign(
            **{
                "Positive rate": df.positive.rolling(7)
                .sum()
                .div(df["Daily change in cumulative total"].rolling(7).sum())
                .round(3)
                .fillna(0)
            }
        )

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline for data processing"""
        return (
            df.pipe(self.pipe_rename_columns)
            .pipe(self.pipe_date)
            .pipe(self.pipe_metrics)
            .pipe(self.pipe_pr)
            .pipe(self.pipe_metadata)
        )

    def export(self):
        """Export data to csv"""
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Armenia().export()
