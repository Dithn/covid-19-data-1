import re

from bs4 import BeautifulSoup
import pandas as pd

from cowidev.utils.web.scraping import request_json
from cowidev.utils import get_soup, clean_count, clean_date
from cowidev.testing import CountryTestBase


class Myanmar(CountryTestBase):
    location: str = "Myanmar"
    units: str = "samples tested"
    source_label: str = "Ministry of Health"
    source_url: str = "https://services7.arcgis.com/AB2LoFxJT2bJUJYC/arcgis/rest/services/CaseCount_130720/FeatureServer/0/query?f=json&where=1%3D1&returnGeometry=false&spatialRel=esriSpatialRelIntersects&outFields=*&outStatistics=%5B%7B%22statisticType%22%3A%22sum%22%2C%22onStatisticField%22%3A%22Tested%22%2C%22outStatisticFieldName%22%3A%22value%22%7D%5D&resultType=standard"
    source_url_ref: str = "https://mohs.gov.mm/Main/content/publication/2019-ncov"
    regex: dict = {
        "date": r"as of (\d{1,2}\-\d{1,2}\-20\d{2})",
    }

    def read(self) -> pd.DataFrame:
        """Read data from source"""
        soup = get_soup(self.source_url_ref, verify=False)
        date = self._parse_date(soup)
        df = pd.DataFrame(
            {
                "Date": [date],
            }
        )
        return df

    def pipe_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Parse metrics from source"""
        data = request_json(self.source_url)
        count = data["features"][0]["attributes"]["value"]
        return df.assign(**{"Cumulative total": clean_count(count)})

    def _parse_date(self, soup: BeautifulSoup) -> str:
        """Parse date from soup"""
        text = soup.get_text()
        date = re.search(self.regex["date"], text).group(1)
        return clean_date(date, "%d-%m-%Y")

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline for data processing"""
        return df.pipe(self.pipe_metrics).pipe(self.pipe_metadata)

    def export(self):
        """Export data to csv"""
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df, attach=True)


def main():
    Myanmar().export()
