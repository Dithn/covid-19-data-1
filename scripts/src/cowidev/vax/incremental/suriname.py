import time

import pandas as pd

from cowidev.utils.clean import clean_count
from cowidev.utils.clean.dates import localdate
from cowidev.utils.web.scraping import get_driver
from cowidev.vax.utils.incremental import enrich_data, increment


def read(source: str) -> pd.Series:

    with get_driver() as driver:
        driver.get(source)
        time.sleep(10)

        for block in driver.find_elements_by_class_name("kpimetric"):
            if "1ste dosis" in block.text and "%" not in block.text:
                people_partly_vaccinated = clean_count(block.find_element_by_class_name("valueLabel").text)
            elif "2de dosis" in block.text and "%" not in block.text:
                people_fully_vaccinated = clean_count(block.find_element_by_class_name("valueLabel").text)
            elif "3de dosis" in block.text and "%" not in block.text:
                total_boosters = clean_count(block.find_element_by_class_name("valueLabel").text)

    people_vaccinated = people_partly_vaccinated + people_fully_vaccinated

    return pd.Series(
        data={
            "total_vaccinations": people_vaccinated + people_fully_vaccinated,
            "people_vaccinated": people_vaccinated,
            "people_fully_vaccinated": people_fully_vaccinated,
            "total_boosters": total_boosters,
            "date": localdate("America/Paramaribo"),
        }
    )



def enrich_location(ds: pd.Series) -> pd.Series:
    return enrich_data(ds, "location", "Suriname")


def enrich_vaccine(ds: pd.Series) -> pd.Series:
    return enrich_data(ds, "vaccine", "Oxford/AstraZeneca, Pfizer/BioNTech, Sinopharm/Beijing")


def enrich_source(ds: pd.Series) -> pd.Series:
    return enrich_data(ds, "source_url", "https://laatjevaccineren.sr/")


def pipeline(ds: pd.Series) -> pd.Series:
    return ds.pipe(enrich_location).pipe(enrich_vaccine).pipe(enrich_source)


def main():
    source = "https://datastudio.google.com/u/0/reporting/d316df2b-49e0-4c3e-aa51-0900828d8cf5/page/igSUC"
    data = read(source).pipe(pipeline)
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
