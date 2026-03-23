import re

import pandas as pd

from cowidev.utils.clean import extract_clean_date, clean_column_name
from cowidev.utils.web.scraping import get_soup
from cowidev.vax.utils.incremental import enrich_data, increment


class Guernsey:
    source_url = "https://covid19.gov.gg/guidance/vaccine/stats"
    location = "Guernsey"
    _regex_date = r"This page was last updated on (\d{1,2} [A-Za-z]+ 202\d)"

    def read(self) -> pd.Series:
        soup = get_soup(self.source_url)
        df = self.parse_data(soup)
        # print(df)
        return df

    def parse_data(self, soup):
        # print(soup)
        # Date
        data = {
            "date": extract_clean_date(
                soup.find("div", class_="ace-notice-paragraph").text, self._regex_date, "%d %B %Y"
            ),
        }
        # Get tables
        tables = soup.find_all("table")
        # Table 1
        ds = pd.read_html(str(tables[0]))[0].squeeze()
        data["total_vaccinations"] = ds.loc[ds[0] == "Total number of doses delivered", 1].values[0]
        # Table 2
        df = pd.read_html(str(tables[1]), header=0)[0]
        df.columns = [clean_column_name(col) for col in df.columns]
        totals = df.iloc[-1]
        data["people_vaccinated"] = int(totals["First dose"])
        data["people_fully_vaccinated"] = int(totals["Second dose"])
        data["total_boosters"] = (
            int(totals["Third dose*"])
            + int(totals["First booster"])
            + int(re.sub(r"[\*,]*", "", totals["Second booster**"]))
            + int(re.sub(r"[\*,]*", "", totals["Third booster**"]))
        )
        # print(ds.loc[ds[0] == "Total doses", 1].values[0])
        # Rename, add/remove columns
        return pd.Series(data)

    def pipe_location(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "location", self.location)

    def pipe_vaccine(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "vaccine", "Moderna, Oxford/AstraZeneca, Pfizer/BioNTech")

    def pipe_source(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "source_url", self.source_url)

    def pipeline(self, ds: pd.Series) -> pd.Series:
        return ds.pipe(self.pipe_location).pipe(self.pipe_vaccine).pipe(self.pipe_source)

    def export(self):
        """Generalized."""
        data = self.read().pipe(self.pipeline)
        increment(
            location=data["location"],
            total_vaccinations=data["total_vaccinations"],
            people_vaccinated=data["people_vaccinated"],
            people_fully_vaccinated=data["people_fully_vaccinated"],
            total_boosters=data["total_boosters"],
            date=data["date"],
            source_url=data["source_url"],
            vaccine=data["vaccine"],
        )


def main():
    Guernsey().export()
