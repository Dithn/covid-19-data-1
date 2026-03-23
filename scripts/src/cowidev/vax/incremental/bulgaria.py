import re

import pandas as pd
from bs4 import BeautifulSoup

from cowidev.utils.clean.dates import localdate
from cowidev.utils.web import get_soup
from cowidev.vax.utils.incremental import enrich_data, increment
from cowidev.vax.utils.base import CountryVaxBase
from cowidev.vax.utils.utils import add_latest_who_values


class Bulgaria(CountryVaxBase):
    location: str = "Bulgaria"
    source_url: str = "https://coronavirus.bg/bg/statistika"

    def read(self) -> pd.Series:
        soup = get_soup(self.source_url)
        return self._parse_data(soup)

    def _parse_data(self, soup: BeautifulSoup) -> pd.Series:
        table = soup.find("p", string=re.compile("Поставени ваксини по")).parent.find("table")
        data = pd.read_html(str(table))[0]
        data = data.droplevel(level=0, axis=1)
        data = data[data["Област"] == "Общо"]
        return data.set_index(data.columns[0]).T.squeeze()

    def pipe_date(self, ds: pd.Series) -> pd.Series:
        date = localdate("Europe/Sofia")
        return enrich_data(ds, "date", date)

    def pipe_index(self, ds: pd.Series) -> pd.Series:
        return ds.rename(
            {
                "Общ брой лица със завършен ваксинационен цикъл": "people_fully_vaccinated",
                "Общо поставени дози": "total_vaccinations",
                "Общ брой лица със завършен ваксинационен курс": "people_fully_vaccinated",
                "Общ брой лица с поставена бустерна доза (реваксинация)": "total_boosters",
            }
        )

    def pipe_location(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "location", self.location)

    def pipe_vaccine(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "vaccine", "Johnson&Johnson, Oxford/AstraZeneca, Moderna, Pfizer/BioNTech")

    def pipe_source(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "source_url", "https://coronavirus.bg/bg/statistika")

    def pipeline(self, ds: pd.Series) -> pd.DataFrame:
        return (
            ds.pipe(self.pipe_index)
            .pipe(self.pipe_date)
            .pipe(self.pipe_location)
            .pipe(self.pipe_vaccine)
            .pipe(self.pipe_source)
            .pipe(self.pipe_merge_with_current)
            .pipe(add_latest_who_values, self.location, ["people_vaccinated"])
        )

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df, valid_cols_only=True)


def main():
    Bulgaria().export()
