import datetime
import re

import pandas as pd
import tabula

from cowidev.utils import get_soup
from cowidev.utils.clean import clean_count
from cowidev.utils.utils import check_known_columns
from cowidev.utils.web import get_base_url
from cowidev.vax.utils.incremental import increment
from cowidev.vax.utils.base import CountryVaxBase


class SriLanka(CountryVaxBase):
    def __init__(self):
        self.location = "Sri Lanka"
        self.source_url = "http://www.epid.gov.lk/web/index.php?option=com_content&view=article&id=231&lang=en"

    def read(self) -> pd.DataFrame:
        last_update = self.last_update()
        records = []
        # Get elements
        elems = self._get_elems()
        for elem in elems:
            date = re.search(r"20\d\d\-\d\d\-\d\d", elem.text).group()
            if date <= last_update:
                break
            data = self._parse_data(date, elem)
            records.append(data)
        return pd.DataFrame(records)

    def _get_elems(self) -> list:
        soup = get_soup(self.source_url)
        elems = soup.find_all("tr")
        elems = [e for e in elems if "Progress Report of COVID - 19 Immunization" in e.text]
        return elems

    def _parse_data(self, date, elem) -> dict:
        pdf_path = get_base_url(self.source_url) + elem.find("a").get("href")
        data = self.parse_metrics_from_pdf(pdf_path)
        data = {
            **data,
            "date": date,
            "location": self.location,
            "source_url": pdf_path,
            "vaccine": "Oxford/AstraZeneca, Sinopharm/Beijing, Sputnik V, Pfizer/BioNTech, Moderna",
        }
        return data

    def parse_metrics_from_pdf(self, pdf_path):
        # print(pdf_path)
        dfs = tabula.read_pdf(pdf_path)
        df = dfs[0]

        # Fix header
        df = self._fix_header(df)
        # All calculations below assume a fixed shape of the PDF's table, and a specific order for
        # the columns and vaccines. If the following test fails, then the table should be checked
        # for potential changes.
        check_known_columns(
            df,
            [
                "දිය",
                "ේ ාවිෂීල්ඩඩ් Covishield",
                "ටයිේයාෆාම් Sinopharm",
                # "ටුට්නිව් - V",
                "ට ට්නිව් - V",
                "Sputnik - V",
                "Unnamed: 0",
                "ෆයිසර්Pfizer",
                "Unnamed: 1",
                "Unnamed: 2",
                "ම ොඩර්ර්ො Moderna",
            ],
        )

        values_idx = df.index[df.iloc[:, 1].notnull()].max()
        values_raw = df.iloc[values_idx].values.flatten()
        values = []
        for val in values_raw:
            if not pd.isnull(val):
                values += val.split()
        assert len(values) == 11

        doses = {
            "first": {
                "covishield": clean_count(values[0]),
                "sinopharm": clean_count(values[2]),
                "sputnik": clean_count(values[4]),
                "pfizer": clean_count(values[6]),
                "moderna": clean_count(values[9]),
            },
            "second": {
                "covishield": clean_count(values[1]),
                "sinopharm": clean_count(values[3]),
                "sputnik": clean_count(values[5]),
                "pfizer": clean_count(values[7]),
                "moderna": clean_count(values[10]),
            },
            "third": {"pfizer": clean_count(values[8])},
        }

        people_vaccinated = sum(doses["first"].values())
        people_fully_vaccinated = sum(doses["second"].values())
        total_boosters = sum(doses["third"].values())
        total_vaccinations = people_vaccinated + people_fully_vaccinated + total_boosters

        return pd.Series(
            {
                "total_vaccinations": total_vaccinations,
                "people_vaccinated": people_vaccinated,
                "people_fully_vaccinated": people_fully_vaccinated,
                "total_boosters": total_boosters,
            }
        )

    def _fix_header(self, df):
        cond = all("Unnamed: " in col for col in df.columns)
        while cond:
            df.columns = df.iloc[0]
            df = df[1:]
            cond = all("Unnamed: " in col for col in df.columns)
        cols = []
        cont = 0
        for col in df.columns:
            if pd.isna(col):
                cols.append(f"Unnamed: {cont}")
                cont += 1
            else:
                cols.append(col)
        df.columns = cols
        return df

    def export(self):
        df = self.read()
        if not df.empty:
            self.export_datafile(df, attach=True)


def main():
    SriLanka().export()
