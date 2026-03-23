import pandas as pd

from cowidev.utils.clean.dates import clean_date
from cowidev.testing import CountryTestBase
from cowidev.utils.web.scraping import get_driver


class Turkey(CountryTestBase):
    location = "Turkey"
    source_url = "https://covid19.saglik.gov.tr/TR-66935/genel-koronavirus-tablosu.html"
    source_url_ref = source_url
    units = "tests performed"
    source_label = "Turkish Ministry of Health"
    rename_columns = {
        "Tarih": "Date",
        "Toplam Test Sayısı": "Cumulative total",
        "Bugünkü Test Sayısı": "Daily change in cumulative total",
    }

    def read(self):
        table = self._parse_table()
        df = pd.read_html(table, thousands=".")[0]
        return df

    def _parse_table(self):
        with get_driver() as driver:
            # with webdriver.Chrome() as driver:
            driver.get(self.source_url)
            table = driver.find_element_by_class_name("table-striped")
            return table.get_attribute("outerHTML")

    def pipe_filter(self, df: pd.DataFrame):
        return df[["Tarih", "Bugünkü Test Sayısı"]].dropna()

    def pipe_date(self, df: pd.DataFrame):
        df["Date"] = (
            df["Date"]
            .str.replace("OCAK", "Jan")
            .str.replace("ŞUBAT", "Feb")
            .str.replace("MART", "Mar")
            .str.replace("NİSAN", "Apr")
            .str.replace("MAYIS", "May")
            .str.replace("HAZİRAN", "Jun")
            .str.replace("TEMMUZ", "Jul")
            .str.replace("AĞUSTOS", "Aug")
            .str.replace("EYLÜL", "Sep")
            .str.replace("EKİM", "oct")
            .str.replace("KASIM", "Nov")
            .str.replace("ARALIK", "Dec")
            .apply(clean_date, fmt="%d %b %Y")
        )
        return df

    def pipeline(self, df: pd.DataFrame):
        df = df.pipe(self.pipe_filter).pipe(self.pipe_rename_columns).pipe(self.pipe_date).pipe(self.pipe_metadata)
        return df

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Turkey().export()
