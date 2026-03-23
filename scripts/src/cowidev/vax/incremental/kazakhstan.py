import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from cowidev.utils.clean import clean_count, clean_date
from cowidev.vax.utils.incremental import increment, enrich_data
from cowidev.vax.utils.base import CountryVaxBase


class Kazakhstan(CountryVaxBase):
    location = "Kazakhstan"
    source_url = "https://www.coronavirus2020.kz/"

    def read(self) -> pd.Series:
        op = Options()
        op.add_argument("--headless")
        with webdriver.Chrome(options=op) as driver:
            driver.get(self.source_url)
            people_vaccinated, people_fully_vaccinated = self._parse_vaccinations(driver)
            date = self._parse_date(driver)
            data = {
                "people_vaccinated": people_vaccinated,
                "people_fully_vaccinated": people_fully_vaccinated,
                "date": date,
            }
            try:
                total_boosters = self._parse_boosters(driver)
            except IndexError:
                pass
            else:
                data["total_boosters"] = total_boosters
            return pd.Series(data)

    def _parse_vaccinations(self, driver: webdriver.Chrome) -> tuple:
        people_vaccinated = clean_count(driver.find_element_by_id("vaccinated_1").text)
        people_fully_vaccinated = clean_count(driver.find_element_by_id("vaccinated_2").text)
        return people_vaccinated, people_fully_vaccinated

    def _parse_boosters(self, driver: webdriver.Chrome) -> tuple:
        elems = driver.find_elements_by_class_name("number_revac_info")
        elem = [e for e in elems if "Всего" in e.find_element_by_xpath("..").text][0]
        total_boosters = clean_count(elem.text)
        return total_boosters

    def _parse_date(self, driver: webdriver.Chrome) -> str:
        elem = driver.find_element_by_class_name("tabl_vactination")
        date_str_raw = pd.read_html(elem.get_attribute("innerHTML"))[0].iloc[-1, -1]
        return clean_date(date_str_raw, "*данные на %d.%m.%Y")

    def pipe_metadata(self, ds: pd.Series):
        ds = enrich_data(ds, "location", self.location)
        ds = enrich_data(ds, "source_url", self.source_url)
        return ds

    def pipe_vaccine(self, ds: pd.Series):
        return enrich_data(ds, "vaccine", "QazVac, Sinopharm/Beijing, Sputnik V")

    def pipe_metrics(self, ds: pd.Series):
        if "total_boosters" in ds:
            total_vaccintations = ds["people_vaccinated"] + ds["people_fully_vaccinated"] + ds["total_boosters"]
            return enrich_data(ds, "total_vaccinations", total_vaccintations)
        return ds

    def pipe_to_frame(self, ds: pd.Series):
        return ds.to_frame().T

    def pipeline(self, ds: pd.Series) -> pd.Series:
        df = ds.pipe(self.pipe_metadata).pipe(self.pipe_vaccine).pipe(self.pipe_metrics).pipe(self.pipe_to_frame)
        # df = add_latest_who_values(df, "Kazakhstan", ["total_vaccinations"])
        return df

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df, attach=True)


def main():
    Kazakhstan().export()
