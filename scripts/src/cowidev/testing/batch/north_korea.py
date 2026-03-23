import time
import pandas as pd
from cowidev.utils.web.scraping import get_driver


from cowidev.testing import CountryTestBase


class NorthKorea(CountryTestBase):
    location = "North Korea"
    units = "people tested"
    source_label = "NK News"
    source_url_ref = "https://www.nknews.org/pro/coronavirus-in-north-korea-tracker/"
    rename_columns = {
        "Unnamed: 1": "Daily change in cumulative total",
        "Unnamed: 4": "Source URL",
        "Unnamed: 5": "Date",
    }

    def read(self):
        table = self._parse_table()
        df = pd.read_html(table)[0]
        return df

    def _parse_table(self):
        with get_driver() as driver:
            # with webdriver.Chrome() as driver:
            driver.get(self.source_url_ref)
            table = driver.find_elements_by_tag_name("table")[2]
            time.sleep(6)
            return table.get_attribute("outerHTML")

    def pipe_filter(self, df: pd.DataFrame):
        df["Daily change in cumulative total"] = pd.to_numeric(df["Daily change in cumulative total"])
        df["Cumulative total"] = df["Daily change in cumulative total"].cumsum()
        df = df[df["Daily change in cumulative total"] != 0]
        return df.dropna()

    def pipeline(self, df: pd.DataFrame):
        df = df.pipe(self.pipe_rename_columns).pipe(self.pipe_filter).pipe(self.pipe_metadata)
        return df

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    NorthKorea().export()
