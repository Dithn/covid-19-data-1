import re
import math
import pandas as pd
import tabula
from typing import Tuple

from bs4 import BeautifulSoup

from cowidev.utils.clean import clean_count, clean_date
from cowidev.utils.web.scraping import get_soup, get_response
from cowidev.vax.utils.incremental import enrich_data, increment


class Taiwan:
    source_url = "https://www.cdc.gov.tw"
    location = "Taiwan"
    vaccines_mapping = {
        "AstraZeneca": "Oxford/AstraZeneca",
        "AZ": "Oxford/AstraZeneca",
        "高端": "Medigen",
        "Moderna 雙價\rBA.1": "Moderna",
        "Moderna 雙價 BA.1": "Moderna",
        "Moderna雙價 BA.1": "Moderna",
        "Moderna": "Moderna",
        "Moderna雙價 BA.4/5": "Moderna",
        "BioNTech": "Pfizer/BioNTech",
        "Novavax": "Novavax",
        "Moderna 雙價 BA.4/5": "Novavax",
    }

    @property
    def source_data_url(self):
        return f"{self.source_url}/Category/Page/9jFXNbCe-sFK9EImRRi2Og"

    def read(self) -> pd.Series:
        soup = get_soup(self.source_data_url)
        url_pdf, filename_pdf = self._parse_pdf_link(soup)
        print(url_pdf)
        df = self._parse_table(url_pdf)
        data = self.parse_data(df, filename_pdf)
        return data

    def _parse_pdf_link(self, soup) -> Tuple[str, str]:
        filename = ""
        for a in soup.find(class_="download").find_all("a"):
            if "疫苗接種統計資料" in a["title"]:
                filename = a.text
                break
        url_pdf = f"{self.source_url}{a['href']}"
        for i in range(10):
            response = get_response(url_pdf)
            if response.headers["Content-Type"] == "application/pdf":
                return url_pdf
            content = response.content
            soup = BeautifulSoup(content, "lxml", from_encoding=None)
            a = soup.find(class_="viewer-button")
            if a is not None:
                break
        return f"{self.source_url}{a['href']}", filename

    def _parse_table(self, url_pdf: str):
        print(url_pdf)
        dfs = self._parse_tables_all(url_pdf)
        df = dfs[0]
        cols = df.columns

        shape_expected = (44, 4)
        if df.shape != shape_expected:
            raise ValueError(f"Table 1: format has changed! It has shape {df.shape} instead of {shape_expected}")

        # Sanity check
        if not (
            len(cols) == 4
            and cols[0] == "廠牌"
            and cols[1] == "劑次"
            and cols[2].endswith("接種人次")
            and re.match(r"((\d+/)?\d+\/\d+ *(\-|~) *)?(\d+/(\d+\/)?)?\d+? *接種人次", cols[2])
            and re.match(r"累計至 *(\d+/)?\d+\/\d+ *接種人次", cols[3])
        ):
            raise ValueError(f"There are some unknown columns: {cols}")

        # The last few columns may be left-shifted and require this small surgery.
        # If math.isnan() raise exception that means the table is changed.
        # print(df)
        # usually rows either starting from row_delimit_1 or row_delimit_2 are the ones needing surgery.
        print(df)
        # row_delimit_1 = 28
        # row_delimit_2 = 34
        row_delimit = 37
        if not df.iloc[row_delimit][0] == "第二劑":
            raise ValueError(
                f"Unexpected value in both key cells {row_delimit} ({df.iloc[row_delimit][0]})!"
            )
        for i in range(row_delimit, len(df)):
            if not isinstance(df.iloc[i][3], str) and math.isnan(df.iloc[i][3]):
                df.iloc[i][[3, 2, 1]] = df.iloc[i][[2, 1, 0]]
                df.iloc[i][0] = float("nan")
        # if df.iloc[27][0] == "總計":
        #     df.iloc[27][0] = float("nan")
        # Patch for Novavax
        print(df)
        # Index fixes
        df["劑次"] = df["劑次"].str.replace(r"\s+", "", regex=True)
        df["廠牌"] = df["廠牌"].fillna(method="ffill")
        df = df.set_index(["廠牌", "劑次"])
        df.columns = ["daily", "total"]
        return df

    def _parse_tables_all(self, url_pdf: str) -> int:
        kwargs = {"pandas_options": {"dtype": str, "header": 0}, "lattice": True}
        dfs = tabula.read_pdf(url_pdf, pages=1, **kwargs)
        return dfs

    def parse_data(self, df: pd.DataFrame, filename_pdf: str):
        stats = self._parse_stats(df)
        data = pd.Series(
            {
                "total_boosters": stats["total_boosters"],
                "total_vaccinations": stats["total_vaccinations"],
                "people_vaccinated": stats["people_vaccinated"],
                "people_fully_vaccinated": stats["people_fully_vaccinated"],
                "date": self._parse_date(filename_pdf),
                "vaccine": self._parse_vaccines(df),
            }
        )
        return data

    def _parse_stats(self, df: pd.DataFrame) -> int:
        # row with all vaccines ('總計') should have 7 rows 
        num_dose1 = clean_count(df.loc["總計", "第一劑"]["total"])
        num_dose2 = clean_count(df.loc["總計", "第二劑"]["total"])
        num_booster1 = clean_count(df.loc["總計", "基礎加強劑"]["total"])
        num_add_1 = clean_count(df.loc["總計", "追加劑"]["total"])
        num_add_2 = clean_count(df.loc["總計", "第二次追加劑"]["total"])
        num_add_3 = clean_count(df.loc["總計", "第三次追加劑"]["total"])
        num_add_4 = clean_count(df.loc["總計", "第四次追加劑"]["total"])
        num_add_5 = clean_count(df.loc["總計", "第五次追加劑"]["total"])

        return {
            "total_vaccinations": num_dose1 + num_dose2 + num_booster1 + num_add_1 + num_add_2 + num_add_3 + num_add_4 + num_add_5,
            "people_vaccinated": num_dose1,
            "people_fully_vaccinated": num_dose2,
            "total_boosters": num_booster1 + num_add_1 + num_add_2 + num_add_3 + num_add_4 + num_add_5,
        }

    def _parse_vaccines(self, df: pd.DataFrame) -> str:
        vaccines = set(df.index.levels[0]) - {"總計", "追加劑"}
        vaccines_wrong = vaccines.difference(self.vaccines_mapping)
        if vaccines_wrong:
            raise ValueError(f"Invalid vaccines: {vaccines_wrong}")
        return ", ".join(sorted(set(self.vaccines_mapping[vax] for vax in vaccines)))

    def _parse_date(self, filename_pdf) -> str:
        regex = r"112年(\d{1,2})月(\d{1,2})日COVID-19疫苗接種統計資料\.pdf"
        month, day = re.search(regex, filename_pdf).group(1, 2)
        date_str = clean_date(f"2023{month}{day}", fmt="%Y%m%d")
        return date_str

    def pipe_location(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "location", self.location)

    def pipe_source(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "source_url", self.source_data_url)

    def pipeline(self, ds: pd.Series) -> pd.Series:
        return ds.pipe(self.pipe_location).pipe(self.pipe_source)

    def export(self):
        data = self.read().pipe(self.pipeline)
        increment(
            location=data["location"],
            total_vaccinations=data["total_vaccinations"],
            people_vaccinated=data["people_vaccinated"],
            people_fully_vaccinated=data["people_fully_vaccinated"],
            date=data["date"],
            source_url=data["source_url"],
            vaccine=data["vaccine"],
            total_boosters=data["total_boosters"],
        )


def main():
    Taiwan().export()
