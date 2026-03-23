import time

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from cowidev.utils.clean import clean_count
from cowidev.utils.clean.dates import localdate
from cowidev.vax.utils.incremental import enrich_data
from cowidev.vax.utils.base import CountryVaxBase
from cowidev.vax.utils.utils import add_latest_who_values


class Qatar(CountryVaxBase):
    location = "Qatar"
    source_url = "https://covid19.moph.gov.qa/EN/Pages/Vaccination-Program-Data.aspx"

    def read(self) -> pd.Series:
        return self.connect_parse_data()

    def connect_parse_data(self) -> pd.Series:
        op = Options()
        op.add_argument("--headless")

        with webdriver.Chrome(options=op) as driver:
            driver.get(self.source_url)
            time.sleep(5)

            total_vaccinations = clean_count(driver.find_element_by_id("counter1").text)
            total_boosters = clean_count(driver.find_element_by_id("counter4").text)
            # people_vaccinated_share = driver.find_element_by_id("counter4").text
            # assert "One dose" in people_vaccinated_share
            # people_fully_vaccinated_share = driver.find_element_by_id("counter4a").text
            # assert "Two doses" in people_fully_vaccinated_share

        # This logic is only valid as long as Qatar *exclusively* uses 2-dose vaccines
        # people_vaccinated_share = float(re.search(r"[\d.]+", people_vaccinated_share).group(0))
        # people_fully_vaccinated_share = float(re.search(r"[\d.]+", people_fully_vaccinated_share).group(0))
        # vaccinated_proportion = people_vaccinated_share / (people_vaccinated_share + people_fully_vaccinated_share)
        # people_vaccinated = round(total_vaccinations * vaccinated_proportion)
        # people_fully_vaccinated = total_vaccinations - people_vaccinated

        date = localdate("Asia/Qatar")

        data = {
            "total_vaccinations": total_vaccinations,
            "total_boosters": total_boosters,
            # "people_vaccinated": people_vaccinated,
            # "people_fully_vaccinated": people_fully_vaccinated,
            "date": date,
        }
        return pd.Series(data=data)

    def enrich_location(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "location", "Qatar")

    def enrich_vaccine(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "vaccine", "Moderna, Pfizer/BioNTech")

    def enrich_source(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "source_url", self.source_url)

    def pipeline(self, ds: pd.Series) -> pd.Series:
        ds = ds.pipe(self.enrich_location).pipe(self.enrich_vaccine).pipe(self.enrich_source)
        df = add_latest_who_values(ds, "Qatar", ["people_vaccinated", "people_fully_vaccinated"])
        return df

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df, attach=True)
        # increment(
        #     location=data["location"],
        #     total_vaccinations=data["total_vaccinations"],
        #     # people_vaccinated=data["people_vaccinated"],
        #     # people_fully_vaccinated=data["people_fully_vaccinated"],
        #     total_boosters=data["total_boosters"],
        #     date=data["date"],
        #     source_url=data["source_url"],
        #     vaccine=data["vaccine"],
        # )


def main():
    Qatar().export()
