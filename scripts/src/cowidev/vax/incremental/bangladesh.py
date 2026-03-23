from multiprocessing.sharedctypes import Value
import pandas as pd

from cowidev.utils.clean import clean_count
from cowidev.utils.clean.dates import localdate
from cowidev.utils.web.scraping import get_soup
from cowidev.vax.utils.incremental import enrich_data, increment


class Bangladesh:
    location: str = "Bangladesh"
    source_url: str = "http://103.247.238.92/webportal/pages/covid19-vaccination-update.php"
    vaccines_rename = {
        "AstraZeneca": "Oxford/AstraZeneca",
        "Pfizer": "Pfizer/BioNTech",
        "Pfizer-PF (Comirnaty)": "Pfizer/BioNTech",
        "Sinopharm": "Sinopharm/Beijing",
        "Moderna": "Moderna",
        "Sinovac": "Sinovac",
        "Janssen (Johnson & Johnson)": "Johnson&Johnson",
    }

    def read(self) -> pd.Series:
        soup = get_soup(self.source_url, timeout=30)
        metrics = self._parse_metrics(soup)
        vaccines = self._parse_vaccines(soup)
        date = localdate("Asia/Dhaka")
        return pd.Series(
            data={
                **metrics,
                "date": date,
                "vaccine": vaccines,
            }
        )

    def _parse_single_doses(self):
        url = "http://103.247.238.92/webportal/pages/covid19-vaccination-johnson.php"
        soup = get_soup(url, timeout=60)
        metrics = self._parse_metrics_raw(soup, raise_err=False)
        if metrics["people_vaccinated"] != 0:
            raise ValueError("First dose for one dose vaccines should be 0!")
        return metrics["people_fully_vaccinated"]

    def _parse_metrics_raw(self, soup, raise_err=True):
        elems = soup.find_all(class_="ttip")
        has_d3 = False
        for e in elems:
            if p := e.find("p"):
                if (text := p.text.strip()) == "1st doses administered":
                    dose1 = clean_count(e.span.text)
                elif text == "2nd doses administered":
                    dose2 = clean_count(e.span.text)
                elif text == "3rd doses administered":
                    dose3 = clean_count(e.span.text)
                    has_d3 = True
        if has_d3:
            return {
                "total_vaccinations": dose1 + dose2 + dose3,
                "people_vaccinated": dose1,
                "people_fully_vaccinated": dose2,
                "total_boosters": dose3,
            }
        if raise_err:
            raise ValueError("Dose 3 data missing!")

        return {
            "total_vaccinations": dose1 + dose2,
            "people_vaccinated": dose1,
            "people_fully_vaccinated": dose2,
        }

    def _parse_metrics(self, soup):
        metrics = self._parse_metrics_raw(soup)
        single_doses = self._parse_single_doses()
        metrics["people_vaccinated"] = metrics["people_vaccinated"] + single_doses
        return metrics

    def _parse_vaccines(self, soup):
        elem = soup.find(class_="nav nav-pills")
        vaccines = {a.text.strip() for a in elem.find_all("a")}
        if vaccines_unk := vaccines.difference(set(self.vaccines_rename) | {"All Vaccine"}):
            raise ValueError(f"Unknown vaccines found {vaccines_unk}")
        return ", ".join(sorted(self.vaccines_rename.values()))

    def pipe_location(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "location", "Bangladesh")

    def pipe_location(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "location", "Bangladesh")

    def pipe_source(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "source_url", self.source_url)

    def pipeline(self, ds: pd.Series) -> pd.Series:
        return ds.pipe(self.pipe_location).pipe(self.pipe_source)

    def export(self):
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
    Bangladesh().export()
