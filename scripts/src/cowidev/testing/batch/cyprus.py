import pandas as pd

from cowidev.testing import CountryTestBase
from cowidev.utils import get_soup, clean_date_series


class Cyprus(CountryTestBase):
    location = "Cyprus"
    source_url = "https://www.data.gov.cy/node/4617?language=en"
    source_url_ref = source_url
    units = "tests performed"
    source_label = "Ministry of Health"
    rename_columns = {
        "date": "Date",
        "total tests": "Cumulative total",
    }

    def read(self):
        soup = get_soup(self.source_url)
        url = soup.find_all(class_="data-link")[-1]["href"]
        df = pd.read_csv(url, usecols=["date", "total tests"])
        return df

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        # Rename
        df = df.pipe(self.pipe_rename_columns)
        # Remove NaNs
        df = df[~df["Cumulative total"].isna()]
        # Date
        df = df.assign(Date=clean_date_series(df.Date, "%d/%m/%Y"))
        # Metadata
        df = df.pipe(self.pipe_metadata)
        return df

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df, attach=True)


def main():
    Cyprus().export()
