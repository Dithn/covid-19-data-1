from datetime import datetime

import pandas as pd
import requests

from cowidev.utils.web import get_soup
from cowidev.utils.clean import clean_date_series
from cowidev.vax.utils.checks import validate_vaccines
from cowidev.vax.utils.base import CountryVaxBase
from cowidev.vax.utils.utils import build_vaccine_timeline


class Switzerland(CountryVaxBase):
    location = "Switzerland"

    def __init__(self):
        self.source_url = "https://opendata.swiss/en/dataset/covid-19-schweiz"
        self.vaccine_mapping = {
            "pfizer_biontech": "Pfizer/BioNTech",
            "moderna": "Moderna",
            "johnson_johnson": "Johnson&Johnson",
            "novavax": "Novavax",
            "moderna_bivalent": "Moderna",
            "pfizer_biontech_bivalent": "Pfizer/BioNTech",
        }

    def read(self):
        doses_url, people_url, manufacturer_url = self._get_file_url()
        df, df_manufacturer = self._parse_data(doses_url, people_url, manufacturer_url)
        # df_age = self.read_age()
        return df, df_manufacturer  #, df_age

    def read_age(self):
        soup = get_soup(self.source_url)
        url = self._parse_age_link(soup)
        return pd.read_csv(url)

    def _parse_age_link(self, soup):
        elems = soup.find_all(class_="resource-item")
        elem = list(
            filter(lambda x: (x.a.get("title") == "COVID19VaccPersons_AKL10_w_v2") & (x.small.text == "CSV"), elems)
        )[0]
        return elem.find(class_="btn").get("href")

    def _get_file_url(self) -> str:
        response = requests.get("https://www.covid19.admin.ch/api/data/context").json()
        context = response["sources"]["individual"]["csv"]
        doses_url = context["vaccDosesAdministered"]
        people_url = context["vaccPersonsV2"]
        manufacturer_url = context["weeklyVacc"]["byVaccine"]["vaccDosesAdministered"]
        return doses_url, people_url, manufacturer_url

    def _parse_data(self, doses_url, people_url, manufacturer_url):
        # print(doses_url)
        # print(people_url)
        # print(manufacturer_url)
        doses = pd.read_csv(
            doses_url,
            usecols=["geoRegion", "date", "sumTotal", "type"],
        )
        people = pd.read_csv(
            people_url,
            usecols=["geoRegion", "date", "sumTotal", "type", "age_group"],
        )
        accepted_types = {
            "COVID19AtLeastOneDosePersons",
            # "COVID19FullyVaccPersons",
            "COVID19PartiallyVaccPersons",
            "COVID19FirstBoosterPersons",
            "COVID19NotVaccPersons",
            "COVID19SecondBoosterPersons",
            "COVID19VaccSixMonthsPersons",
        }
        vax_missing = set(people["type"]).difference(accepted_types)
        assert not vax_missing, f"New type found! Check people.type: {set(vax_missing)}"
        people = people[people.age_group == "total_population"].drop(columns=["age_group"])
        manufacturer = pd.read_csv(
            manufacturer_url,
            usecols=["date", "geoRegion", "vaccine", "sumTotal"],
        )
        return pd.concat([doses, people], ignore_index=True), manufacturer

    def save_vaccine_timeline(self, df_manuf: pd.DataFrame) -> pd.DataFrame:
        self.vaccine_timeline = (
            df_manuf[df_manuf.sumTotal > 0][["vaccine", "date"]]
            .replace(self.vaccine_mapping)
            .groupby("vaccine")
            .min()
            .to_dict()["date"]
        )

    def pipe_filter_country(self, df: pd.DataFrame, country_code: str) -> pd.DataFrame:
        return df[df.geoRegion == country_code].drop(columns=["geoRegion"])

    def pipe_unique_rows(self, df: pd.DataFrame):
        # Checks
        a = df.groupby(["date", "type"]).count().reset_index()
        if not a[a.sumTotal > 1].empty:
            raise ValueError("Duplicated rows in either `people` or `doses` dataframes!")
        return df

    def pipe_pivot(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.pivot(index=["date"], columns="type", values="sumTotal").reset_index().sort_values("date")

    def pipe_rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.rename(
            columns={
                # "COVID19FullyVaccPersons": "people_fully_vaccinated",
                "COVID19VaccDosesAdministered": "total_vaccinations",
                "COVID19AtLeastOneDosePersons": "people_vaccinated",
                "COVID19FirstBoosterPersons": "total_boosters",
                "COVID19SecondBoosterPersons": "total_boosters_2",
            }
        )

    def pipe_fix_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        df.loc[df.total_vaccinations < df.people_vaccinated, "total_vaccinations"] = df.people_vaccinated
        df = df.assign(total_boosters=df.total_boosters + df.total_boosters_2)
        return df

    def pipe_location(self, df: pd.DataFrame, location: str) -> pd.DataFrame:
        return df.assign(location=location)

    def pipe_source(self, df: pd.DataFrame, country_code: str) -> pd.DataFrame:
        return df.assign(
            source_url=f"{self.source_url}?detGeo={country_code}",
        )

    def pipe_filter_dp(self, df: pd.DataFrame) -> pd.DataFrame:
        date_th = min(self.vaccine_timeline.values())
        return df[df.date >= date_th]

    def pipeline(self, df: pd.DataFrame, location: str) -> pd.DataFrame:
        geo_region = _get_geo_region(location)
        return (
            df.pipe(self.pipe_filter_country, geo_region)
            .pipe(self.pipe_unique_rows)
            .pipe(self.pipe_pivot)
            .pipe(self.pipe_rename_columns)
            .pipe(self.pipe_fix_metrics)
            .pipe(self.pipe_location, location)
            .pipe(self.pipe_source, geo_region)
            .pipe(build_vaccine_timeline, self.vaccine_timeline)
            .pipe(self.pipe_filter_dp)[
                [
                    "location",
                    "date",
                    "vaccine",
                    "source_url",
                    "total_vaccinations",
                    "people_vaccinated",
                    # "people_fully_vaccinated",
                    "total_boosters",
                ]
            ]
        )

    def pipeline_manufacturer(self, df: pd.DataFrame) -> pd.DataFrame:
        validate_vaccines(df, self.vaccine_mapping)
        df = df[df.sumTotal > 0]
        return (
            df.rename(columns={"sumTotal": "total_vaccinations"})[df.geoRegion == "CH"]
            .drop(columns="geoRegion")
            .assign(location="Switzerland")
            .replace(self.vaccine_mapping)
            .groupby(["location", "date", "vaccine"], as_index=False)
            .sum()
            .pipe(self.make_monotonic, ["vaccine"])
        )

    def pipe_age_filter_region(self, df, geo_region):
        # Only Switzerland
        return df[(df.geoRegion == geo_region) & (df.age_group_type == "age_group_AKL10")]

    def pipe_age_checks(self, df):
        # Check population per age group is unique
        if not (df.groupby("altersklasse_covid19").pop.nunique() == 1).all():
            raise ValueError("Different `pop` values for same `alterklasse_covid19` value!")
        # Check type
        type_wrong = set(df.type_variant).difference(["altersklasse_covid19"])
        if type_wrong:
            raise ValueError(f"Invalid `type_variant` value: {type_wrong}")
        # Date+Age group uniqueness
        if not (df.groupby(["date", "altersklasse_covid19"]).type.value_counts() == 1).all():
            raise ValueError("Some dates and age groups have multiple entries for same metric!")
        return df

    def pipe_age_pivot(self, df):
        return df.pivot(
            index=["date", "altersklasse_covid19"], columns=["type"], values="per100PersonsTotal"
        ).reset_index()

    def pipe_age_date(self, df):
        return df.assign(date=clean_date_series(df.date.apply(lambda x: datetime.strptime(str(x) + "+0", "%G%V+%w"))))

    def pipe_age_location(self, df, location):
        return df.assign(location=location)

    def pipe_age_rename_columns(self, df):
        return df.rename(
            columns={
                "altersklasse_covid19": "age_group",
                "COVID19AtLeastOneDosePersons": "people_vaccinated_per_hundred",
                # "COVID19FullyVaccPersons": "people_fully_vaccinated_per_hundred",
            }
        )

    def pipe_age_groups(self, df):
        regex = r"(\d{1,2})+?(?: - (\d{1,2}))?"
        df[["age_group_min", "age_group_max"]] = df.age_group.str.extract(regex)
        return df

    def pipe_age_select_cols(self, df):
        return df[
            [
                "location",
                "date",
                "age_group_min",
                "age_group_max",
                "people_vaccinated_per_hundred",
                # "people_fully_vaccinated_per_hundred",
            ]
        ]

    def pipeline_age(self, df, location):
        geo_region = _get_geo_region(location)

        df_ = df.copy()
        return (
            df_.pipe(self.pipe_age_filter_region, geo_region)
            .pipe(self.pipe_age_checks)
            .pipe(self.pipe_age_pivot)
            .pipe(self.pipe_age_date)
            .pipe(self.pipe_age_location, location)
            .pipe(self.pipe_age_rename_columns)
            .pipe(self.make_monotonic, ["age_group"])
            .pipe(self.pipe_age_groups)
            .pipe(self.pipe_age_select_cols)
        )

    def export(self):
        locations = ["Switzerland", "Liechtenstein"]
        # df, df_manuf, df_age = self.read()
        df, df_manuf = self.read()

        # Save vaccine timeline
        self.save_vaccine_timeline(df_manuf)

        # Main data
        for location in locations:
            df_c = df.pipe(self.pipeline, location)
            self.export_datafile(df_c, filename=location)

        # Manufacturer
        df_manuf = df_manuf.pipe(self.pipeline_manufacturer)
        self.export_datafile(
            df_manufacturer=df_manuf,
            meta_manufacturer={"source_name": "Federal Office of Public Health", "source_url": self.source_url},
        )

        # Age
        # for location in locations:
        #     df_age_ = df_age.pipe(self.pipeline_age, location)
        #     self.export_datafile(
        #         df_age=df_age_,
        #         meta_age={"source_name": "Federal Office of Public Health", "source_url": self.source_url},
        #         filename=location,
        #     )


def main():
    Switzerland().export()


def _get_geo_region(location):
    if location == "Switzerland":
        return "CH"
    elif location == "Liechtenstein":
        return "FL"
    else:
        raise ValueError("Only Switzerland or Liechtenstein are accepted values for `location`.")
