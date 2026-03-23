from datetime import datetime

import pandas as pd

from cowidev.utils.clean import clean_date
from cowidev.utils.web import request_json
from cowidev.vax.utils.incremental import increment
from cowidev.vax.utils.orgs import WHO_VACCINES, ACDC_COUNTRIES, ACDC_VACCINES


class AfricaCDC:
    _base_url = (
        "https://services8.arcgis.com/vWozsma9VzGndzx7/ArcGIS/rest/services/"
        "Admin_Boundaries_Africa_corr_Go_Vaccine_DB_JOIN/FeatureServer/0"
    )
    source_url_ref = "https://africacdc.org/covid-19-vaccination/"
    columns_rename = {
        "ADM0_SOVRN": "location",
        "TotAmtAdmi": "total_vaccinations",
        "FullyVacc": "people_fully_vaccinated",
        "VacAd1Dose": "people_vaccinated",
        "Booster": "total_boosters",
    }
    columns_use = list(columns_rename.keys()) + [
        "ISO_3_CODE",
        "VacAd2Dose",
        "VaccApprov",
    ]

    def __init__(self, skip_who: bool = False) -> None:
        self.skip_who = skip_who

    @property
    def source_url(self):
        return f"{self._base_url}/query?f=json&where=1=1&outFields=*"

    @property
    def source_url_date(self):
        return f"{self._base_url}?f=pjson"

    def read(self) -> pd.DataFrame:
        data = request_json(self.source_url)
        res = [d["attributes"] for d in data["features"]]
        df = pd.DataFrame(res)
        return df

    def pipe_filter_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[self.columns_use]

    def pipe_rename(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.rename(columns=self.columns_rename)

    def pipe_filter_countries(self, df: pd.DataFrame, countries: dict) -> pd.DataFrame:
        """Get rows from selected countries."""
        df = df[df.location.isin(countries.keys())]
        df = df.assign(location=df.location.replace(countries))
        return df

    def pipe_one_dose_correction(self, df: pd.DataFrame) -> pd.DataFrame:
        single_shot = df.people_fully_vaccinated - df.VacAd2Dose
        return df.assign(people_vaccinated=df.people_vaccinated + single_shot)

    def pipe_vaccine(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(vaccine=df.VaccApprov.apply(self._map_vaccines))

    def _map_vaccines(self, vaccine_raw: str):
        vaccine_raw = vaccine_raw.strip()
        vaccines = []
        for vax_old, vax_new in ACDC_VACCINES.items():
            if vax_old in vaccine_raw:
                vaccines.append(vax_new)
                vaccine_raw = vaccine_raw.replace(vax_old, "").strip()
            if vaccine_raw == "":
                break
        if vaccine_raw != "":
            raise ValueError(f"Some vaccines were unknown {vaccine_raw}")
        vaccines = ", ".join(sorted(vaccines))
        return vaccines

    def pipe_vaccine_who(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.skip_who:
            return df
        # url = "https://covid19.who.int/who-data/vaccination-data.csv"
        url = "https://srhdpeuwpubsa.blob.core.windows.net/whdh/COVID/vaccination-data.csv"
        df_who = pd.read_csv(url, usecols=["ISO3", "VACCINES_USED"]).rename(columns={"VACCINES_USED": "vaccine"})
        df_who = df_who.dropna(subset=["vaccine"])
        df = df.merge(df_who, left_on="ISO_3_CODE", right_on="ISO3")
        df = df.assign(
            vaccine=df.vaccine.apply(lambda x: ", ".join(sorted(set(WHO_VACCINES[xx.strip()] for xx in x.split(",")))))
        )
        return df

    def pipe_source(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(source_url=self.source_url_ref)

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(date=self._parse_date())

    def _parse_date(self):
        res = request_json(self.source_url_date)
        edit_ts = res["editingInfo"]["lastEditDate"]
        return clean_date(datetime.fromtimestamp(edit_ts / 1000))

    def pipe_select_out_cols(self, df: pd.DataFrame) -> pd.DataFrame:
        cols = [
            "location",
            "date",
            "source_url",
            "total_vaccinations",
            "people_vaccinated",
            "people_fully_vaccinated",
            "total_boosters",
        ]
        if not self.skip_who:
            cols += ["vaccine"]
        return df[cols]

    def pipe_exclude_observations(self, df: pd.DataFrame) -> pd.DataFrame:
        # Exclude observations where people_fully_vaccinated == 0, as they always seem to be
        # data errors rather than countries without any full vaccination.
        df = df[df.people_fully_vaccinated > 0]

        # Exclude observations where people_fully_vaccinated > people_vaccinated
        df = df[df.people_fully_vaccinated <= df.people_vaccinated]

        return df

    def pipeline(self, df: pd.DataFrame, countries: dict = ACDC_COUNTRIES, exclude=True) -> pd.DataFrame:
        df = (
            df.pipe(self.pipe_filter_columns)
            .pipe(self.pipe_rename)
            .pipe(self.pipe_filter_countries, countries)
            .pipe(self.pipe_one_dose_correction)
            .pipe(self.pipe_vaccine_who)
            .pipe(self.pipe_source)
            .pipe(self.pipe_date)
            .pipe(self.pipe_select_out_cols)
        )
        if exclude:
            df = df.pipe(self.pipe_exclude_observations)
        return df

    def increment_countries(self, df: pd.DataFrame):
        for row in df.sort_values("location").iterrows():
            row = row[1]
            increment(
                location=row["location"],
                total_vaccinations=row["total_vaccinations"],
                people_vaccinated=row["people_vaccinated"],
                people_fully_vaccinated=row["people_fully_vaccinated"],
                total_boosters=row["total_boosters"],
                date=row["date"],
                vaccine=row["vaccine"],
                source_url=row["source_url"],
            )
            country = row["location"]
            # logger.info(f"\tvax.incremental.africacdc.{country}: SUCCESS ✅")

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.increment_countries(df)


def main():
    AfricaCDC().export()
