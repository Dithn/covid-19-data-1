import re
import time

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from cowidev.utils.clean import clean_count
from cowidev.utils.clean.dates import clean_date
from cowidev.vax.utils.incremental import enrich_data
from cowidev.vax.utils.base import CountryVaxBase


class DominicanRepublic(CountryVaxBase):
    location = "Dominican Republic"
    source_url = "https://vacunate.gob.do"
    source_url_ref = source_url

    def read(self):
        op = Options()
        op.add_argument("--headless")

        with webdriver.Chrome(options=op) as driver:
            driver.get(self.source_url)
            time.sleep(10)
            metrics = self._parse_metrics(driver)
            date = self._parse_date(driver)
        data = {
            "date": date,
            **metrics,
        }
        return pd.Series(data=data)

    def _parse_metrics(self, driver):
        metric_candidates = _find_potential_metrics(driver)
        metrics_raw_mapping = {
            "Primera dosis": "people_vaccinated",
            "Cantidad total de dosis administradas": "total_vaccinations",
            "Población completamente vacunada": "people_fully_vaccinated",
            "Dosis de refuerzo": "total_boosters",
        }
        metrics = {}
        for metric in metric_candidates:
            for old, new in metrics_raw_mapping.items():
                if old == metric["name"]:
                    metrics[new] = clean_count(metric["value"])
        if len(metrics) != 4:
            raise ValueError(f"Some metrics are missing! Currently we have {metrics.keys()}")
        return metrics

    def _parse_date(self, driver):
        dt_candidates = [e.text for e in driver.find_elements_by_tag_name("h3")]
        for dt_candidate in dt_candidates:
            if "Estadísticas nacionales | Acumulados" in dt_candidate:
                return clean_date(
                    dt_candidate,
                    "Estadísticas nacionales | Acumulados al %d de %B de %Y",
                    lang="es",
                )

    def pipe_vaccine(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "vaccine", "Oxford/AstraZeneca, Pfizer/BioNTech, Sinopharm/Beijing, Sinovac")

    def pipeline(self, ds: pd.Series) -> pd.Series:
        return ds.pipe(self.pipe_metadata).pipe(self.pipe_vaccine)

    def export(self):
        data = self.read().pipe(self.pipeline)
        self.export_datafile(df=data, attach=True)


def _find_h3(driver):
    elem = [
        e
        for e in driver.find_elements_by_tag_name("h3")
        if re.search(r"Estadísticas nacionales \| Acumulados al \d+ de \w+ de 20\d\d", e.text)
    ]
    if len(elem) == 1:
        elem = elem[0]
    else:
        raise ValueError("More than one element found!")
    return elem


def _find_potential_metric_elements(h3):
    div_main = h3.find_element_by_xpath("..")
    return div_main.find_elements_by_tag_name("div")


def _find_potential_metrics(driver):
    h3 = _find_h3(driver)
    elems = _find_potential_metric_elements(h3)
    # Filter only those with two div children
    elems = [ee for e in elems if len(ee := e.find_elements_by_tag_name("div")) == 2]
    metrics = []
    for e in elems:
        for ee in e:
            if match := re.search(r"[\d,]+", ee.text):
                value = match.group()
            else:
                name = ee.text
        metrics.append(
            {
                "name": name,
                "value": value,
            }
        )
    return metrics


def main():
    DominicanRepublic().export()
