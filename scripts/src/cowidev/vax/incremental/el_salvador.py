import json

import pandas as pd
from bs4 import BeautifulSoup

from cowidev.utils.clean import clean_count, extract_clean_date
from cowidev.utils.web.scraping import get_soup
from cowidev.vax.utils.incremental import enrich_data, increment


class ElSalvador:
    location: str = "El Salvador"
    source_url: str = "https://covid19.gob.sv/"

    def read(self) -> pd.Series:
        soup = get_soup(self.source_url)
        link = self.parse_infogram_link(soup)
        # print(link)
        soup = get_soup(link)
        infogram_data = self.parse_infogram_data(soup)
        return pd.Series(
            {
                "date": self.parse_infogram_date(infogram_data),
                "source_url": self.source_url,
                "total_vaccinations": self._parse_total_vaccinations(infogram_data),
                "people_vaccinated": self._parse_people_vaccinated(infogram_data),
                "people_fully_vaccinated": self._parse_people_fully_vaccinated(infogram_data),
                "total_boosters": self._parse_boosters(infogram_data),
            }
        )

    def parse_infogram_link(self, soup: BeautifulSoup) -> str:
        url_end = soup.find(class_="infogram-embed").get("data-id")
        return f"https://e.infogram.com/{url_end}"

    def parse_infogram_data(self, soup: BeautifulSoup) -> dict:
        for script in soup.find_all("script"):
            if "infographicData" in str(script):
                json_data = script.string[:-1].replace("window.infographicData=", "")
                json_data = json.loads(json_data)
                break
        json_data = json_data["elements"]["content"]["content"]["entities"]
        return json_data

    def _get_infogram_value(self, infogram_data: dict, field_id: str, join_text: bool = False):
        if join_text:
            return "".join(x["text"] for x in infogram_data[field_id]["props"]["content"]["blocks"])
        return infogram_data[field_id]["props"]["content"]["blocks"][0]["text"]

    def _parse_total_vaccinations(self, infogram_data: dict) -> int:
        return clean_count(
            self._get_infogram_value(
                infogram_data, "33f6ba96-fffd-4a95-a7ac-b65aa9f808c35b18e4d2-a9b9-4383-a4c4-7aea197c5322"
            )
        )

    def _parse_people_vaccinated(self, infogram_data: dict) -> int:
        ppl_vaxed = clean_count(
            self._get_infogram_value(
                infogram_data, "4275cc3f-7ae8-4af3-9c5a-ef94203d47d71c0589f5-607d-4eb2-86b0-b24303e5455a"
            )
        )
        ppl_vaxed_for = clean_count(
            self._get_infogram_value(
                infogram_data, "8a007cb6-7384-4af1-9f92-c41699d77aab1ed244af-7cfe-47be-972f-210df044e204"
            )
        )
        return ppl_vaxed + ppl_vaxed_for

    def _parse_people_fully_vaccinated(self, infogram_data: dict) -> int:
        ppl_fully_vaxed = clean_count(
            self._get_infogram_value(
                infogram_data, "7b45d34f-b8d0-47d7-8c3a-35c89a4d4cdfbeb30c31-b4de-45fc-bdc5-78e39d37039b"
            )
        )
        ppl_fully_vaxed_for = clean_count(
            self._get_infogram_value(
                infogram_data, "9eee1f41-c398-4a15-81aa-2588250e53cbbc920ff4-fff6-4ef4-a174-af1915c4b1a7"
            )
        )
        return ppl_fully_vaxed + ppl_fully_vaxed_for

    def _parse_boosters(self, infogram_data: dict) -> int:
        third_dose = clean_count(
            self._get_infogram_value(
                infogram_data, "296d4de1-bd72-44d9-bca2-2fdff2477c2c463a2de2-f70e-4b18-aee0-43f01852970f"
            )
        )
        third_dose_for = clean_count(
            self._get_infogram_value(
                infogram_data, "de709d4d-bac0-4a75-84bc-1d1d1104169b3df9b985-04fb-48fc-b6b0-7ce028ab9aa1"
            )
        )
        forth_dose = clean_count(
            self._get_infogram_value(
                infogram_data, "2fbd1738-f9c3-49ad-8855-c933c83abc185dc2112e-d914-4551-8da9-2466a4916ca2"
            )
        )
        forth_dose_for = clean_count(
            self._get_infogram_value(
                infogram_data, "20d53fe7-91f8-4778-a13f-c938f18dd8fe92d01672-d40e-4099-96ff-9d125c46f748"
            )
        )
        return third_dose + third_dose_for + forth_dose + forth_dose_for

    def parse_infogram_date(self, infogram_data: dict) -> str:
        field_id = "d58d673d-f6f7-44d2-8825-8f83ea806a695bbc73d2-f5d6-493e-890b-b7499db493a2"
        x = self._get_infogram_value(infogram_data, field_id, join_text=True)
        dt = extract_clean_date(x, "RESUMEN DE VACUNACIÓN\s?(\d+-[A-Z]+-2\d)\s?", "%d-%b-%y", lang="es")
        return dt

    def pipe_location(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "location", "El Salvador")

    def pipe_vaccine(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "vaccine", "Oxford/AstraZeneca, Pfizer/BioNTech, Sinopharm/Beijing, Sinovac")

    def pipeline(self, ds: pd.Series) -> pd.Series:
        return ds.pipe(self.pipe_location).pipe(self.pipe_vaccine)

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
    ElSalvador().export()
