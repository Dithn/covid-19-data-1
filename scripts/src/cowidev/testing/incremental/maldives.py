import pandas as pd

from cowidev.utils.web.scraping import request_json
from cowidev.utils.clean import clean_count, extract_clean_date
from cowidev.testing import CountryTestBase


class Maldives(CountryTestBase):
    location: str = "Maldives"
    units: str = "samples tested"
    source_label: str = "Maldives Health Protection Agency"
    source_url: str = "https://covid19.health.gov.mv/v2_data.json"
    source_url_ref: str = "https://covid19.health.gov.mv/en"
    regex: dict = {
        "date": r"(\d{1,2}\/\d{1,2}\/20\d{2})",
    }

    def read(self) -> pd.DataFrame:
        """Read data from source."""
        data = request_json(self.source_url)
        df = self._parse_data(data)
        return df

    def _parse_data(self, data: dict) -> pd.DataFrame:
        """Parse data."""
        count = clean_count(data["samples_collected"])
        date = extract_clean_date(
            data["screen_updated_times"]["toplevel_page_acf-options-statistics"], self.regex["date"], "%d/%m/%Y"
        )
        df = {
            "Date": [date],
            "Daily change in cumulative total": [count],
        }
        return pd.DataFrame(df)

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline for data."""
        return df.pipe(self.pipe_metadata)

    def export(self):
        """Export data to CSV."""
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df, attach=True)


def main():
    Maldives().export()
