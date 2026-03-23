import re
import requests

from bs4 import BeautifulSoup
import pandas as pd
import tabula

from cowidev.utils import get_soup, clean_count, clean_date
from cowidev.testing import CountryTestBase


class Bahamas(CountryTestBase):
    location: str = "Bahamas"
    units: str = "tests performed"
    source_label: str = "Ministry of Health and Wellness"
    source_url: str = "https://www.bahamas.gov.bs/wps/portal/public/gov/government/news/!ut/p/b1/vZfJkqM4EIafpR6AsiQQgqNYbbMjwOCLwyvewAu2WZ5-XBPTMV3dPa45lI1ORGTGp_xzkdQb99LeuJzeNvn0sjmU0_3H_1ic8MB0KBUkRzJECgYxb_DYorwZwLtBdjcA__FR8NnfxEC8-_s29UkfeRbqjXppP7s22sHJDapM1tko9PXQnUehe92PiHixcwHpzV455OKSSxf2iQgj1TBGDm7ramRfJx1JS7nRrWbu7c6xGJ6yel0dCrnYggBXgCmRml0Pc7FE8z2Ty5tk8Ae7JcoQL1REy3S10QU85IOJ5-mic49bSy4wn825Zi2VYgPBPzE-COJRjBB_4S-A_6fxA8AX_qPe-OEWP3bwt8GjNH6VSLd_KJa97G5GfjKLEgAGENCQwQBILuxFvRQIE7Ztj4Nu14VbULdut3BZ5ADQxSDSUubOdFBdVOjocAh10Dq60EaRYTOwQ8y1_UUSxgpVOU-fnn8FeiiS70AVilaMAQPCs4Em9qS7ECTyKUbA9OCrgfxLJTV9Dzw9wk9FIwTfn8Nhb7yZFe_1vHgH75IsQkwkQZZEIAgS6SXbDBBNGtT6wJ-o1dWVTVwEYFNLRp4F62V8OcyZxbh9CH3On-rVVu-4mV4h61yPd7NAoZvT3rVnXRRKMvCahTkw2Db3g4Oe2lZnBH3BrXWzTgsaJ8Ar2hvHcd5YvRS5m17Xx2V_OYzLhJumHe5OS1_g-dt6tmvNOYG-k11QMuYWFc-z0aoKkRgZZxMKocFWWRpF81Vl-qfL2s3f3h4La1q_12oXoEivkaPXHdwmbqT5gRvvWndhQaYNWmAnAxZltRPfBe4GHbv8EJauHcZmj7tRNfCzgZ-bA1DyYuAfavXJQPHVwGdJGiggYLbMU0AxBoM-iggxYx5g_tURvrpKxVfnUPz-Kv00UXlZJhLEkiBBCUEo9ZJhVsjajtaGPl6F2ZJcyyVix62eVXRzoYBN4nJhmdwti87lSpkgz-ycW07VzbZfcGjYikEXzAJM6K3MjaE6XS5n_WmrHW3zZnt93DqTMY2Si4tnkkayUhGLaHE8-9N0WjoypzbqTVeVEkz44KupKJHfC5yEjrNVrPttooE7hBwtjd3IsJjsQcdO7mcQ6FgMHXcbWmybIeey-iHOPJ9W2Rd3FJN_NvDXqSi-GoifBTQ9J1A_JI2UD0n5fp-KNu_p8NXA78_hp47CAsRYhkgWEUEEko-OaolWDWrt_mgahkiCR5EMpuE1cFZqvhueA5aWh8WaobNU5te95zadt_S5DAf64OTOpjNxEtjtjpLY3NDriCUnLSnIfOvIKjuUOlj5zc7FrWKfV81yhfmDhZrQxEgvjfR8PRX16XStbC297BS8kEHa3GdGTO_ddSzim2XZYtivofTv4ovbH5b0s0n99heUoIvF/dl4/d5/L2dBISEvZ0FBIS9nQSEh/"
    source_url_ref: str = None
    _base_url: str = "https://www.bahamas.gov.bs"
    column_to_check: str = "Total # of RT-"
    regex: dict = {
        "title": r"COVID-19 Report Update",
    }

    def read(self) -> pd.DataFrame:
        """Read data from source"""
        soup = get_soup(self.source_url)
        df = self._parse_data(soup)
        return df

    def _parse_data(self, soup: BeautifulSoup) -> pd.DataFrame:
        """Parse data from soup"""
        # Get the article url
        self.source_url_ref = self._parse_link(soup)
        # Extract pdf table from link
        table = self._parse_pdf_table()
        # Get the metrics
        count = self._parse_metrics(table)
        # Get the date
        date = self._parse_date(soup)
        df = pd.DataFrame(
            {
                "Date": [date],
                "Cumulative total": [count],
            }
        )
        return df

    def _parse_link(self, soup: BeautifulSoup) -> str:
        """Parse the article url from soup"""
        page_href = soup.find("a", text=re.compile(self.regex["title"]))["href"]
        if not page_href:
            raise ValueError("Article page not found, please update the script")
        soup_page = get_soup(f"{self.source_url}{page_href}")
        href = soup_page.find_all("a", text=re.compile(self.regex["title"]))[-1]["href"]
        return f"{self._base_url}{href}"

    def _parse_pdf_table(self) -> pd.DataFrame:
        """Parse pdf table from link"""
        response = requests.get(self.source_url_ref, stream=True, verify=True)
        tables = tabula.read_pdf(response.raw, pages="all")
        table = [df for df in tables if self.column_to_check in df.columns]
        if not table:
            raise ValueError("Table not found, please update the script")
        return table[0]

    def _parse_metrics(self, table: pd.DataFrame) -> int:
        """Parse metrics from table"""
        count = table.iloc[-1][0]
        return clean_count(count)

    def _parse_date(self, soup: BeautifulSoup) -> str:
        """Parse date from soup"""
        date_str = soup.find("a", text=re.compile(self.regex["title"])).parent.previousSibling.text
        if not date_str:
            raise ValueError("Date not found, please update the script")
        return clean_date(date_str.lower(), "%B %d, %Y")

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline for data processing"""
        return df.pipe(self.pipe_metadata)

    def export(self):
        """Export data to csv"""
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df, attach=True)


def main():
    Bahamas().export()
