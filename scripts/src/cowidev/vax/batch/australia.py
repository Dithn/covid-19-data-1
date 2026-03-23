import pandas as pd
import re
from datetime import datetime

from cowidev.utils import clean_date, clean_date_series, get_soup
from cowidev.utils.utils import check_known_columns
from cowidev.utils.web.download import read_csv_from_url, read_xlsx_from_url
from cowidev.vax.utils.base import CountryVaxBase
from cowidev.vax.utils.utils import build_vaccine_timeline


HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux i686)"}
VARIABLE_MAPPING = {
    "total_vaccinations": ["National - Total vaccine doses administered"],
    "people_vaccinated": [
        "National - Number of people 16 and over who have received at least 1 dose",
        "National - Number of people 12-15 who have received at least 1 dose",
        "National - Number of people 5-11 who have received at least 1 dose",
        "National - Number of people 16 and over with 1 dose",
        "National - Number of people 12-15 with 1 dose",
        "National - Number of people 5-11 with 1 dose",
    ],
    "people_fully_vaccinated": [
        "National - Number of people 16 and over who have received at least 2 doses",
        "National - Number of people 12-15 who have received at least 2 doses",
        "National - Number of people 5-11 who have received at least 2 doses",
        "National - Number of people 16 and over fully vaccinated",
        "National - Number of people 12-15 with 2 doses",
        "National - Number of people 5-11 fully vaccinated",
    ],
    "total_boosters": [
        "National - Number of people 16 and over who have received 3 doses",
        "National - Number of people 16 and over who have received 4 doses",
        "National - 16 and over with 3 or more doses",
        "National - Fourth dose number- daily update",
        "National - 16 and over with more than 2 doses",
        "National - 18 and over with more than 2 doses",
        "National - Number of people 16 and over with more than two doses",
    ],
}
URL_1 = r"https://www\.health\.gov\.au/sites/default/files/documents/202\d/\d\d?/.*-(\d\d?\-[a-z]*\-202\d)(_\d)?\.xlsx"


class Australia(CountryVaxBase):
    source_url = {
        "main": "https://covidbaseau.com/people-vaccinated.csv",
        "age_1d": "https://covidbaseau.com/historical/Vaccinations%20By%20Age%20Group%20and%20State%20First.csv",
        "age_2d": "https://covidbaseau.com/historical/Vaccinations%20By%20Age%20Group%20and%20State%20Second.csv",
    }
    source_url_ref = "https://covidbaseau.com/"
    source_file = "https://covidbaseau.com/people-vaccinated.csv"
    location = "Australia"
    columns_rename = {
        "dose_1": "people_vaccinated",
        "dose_2": "people_fully_vaccinated",
    }
    vaccine_timeline = {
        "Pfizer/BioNTech": "2021-01-01",
        "Moderna": "2021-03-06",
        "Oxford/AstraZeneca": "2021-03-06",
        "Novavax": "2022-02-17",
    }

    def read(self) -> pd.DataFrame:
        df = read_csv_from_url(self.source_url["main"])
        check_known_columns(df, ["date", "dose_1", "dose_2", "dose_3", "dose_4"])
        return df

    def read_latest_from_official_source(self) -> pd.DataFrame:
        # Get soup from all-reporting page
        base_url = "https://www.health.gov.au"
        url = f"{base_url}/resources/collections/covid-19-vaccination-vaccination-data"
        soup = get_soup(url)
        # Get elements of pages for specific date reportings
        elems = soup.find_all("a", text=re.compile(r"COVID-19 vaccination – vaccination data –"))

        # Only access last report
        res = self._extract_url_and_df(base_url, elems[0])
        return res

    def pipeline_latest_from_official_source(self, res) -> pd.DataFrame:
        # Transform
        date = _get_date(res)
        df = _get_df(res["df"])
        data = _parse_data(df)
        data["date"] = date
        data["source_url"] = res["url"]
        # Build df
        df = pd.DataFrame([data]).assign(
            location="Australia",
            vaccine="Moderna, Novavax, Oxford/AstraZeneca, Pfizer/BioNTech",
        )
        return df

    def _extract_url_and_df(self, base_url, elem):
        url = f"{base_url}/{elem.get('href')}"
        url = self._get_data_file_url(url)
        # Rea Excel
        df = read_xlsx_from_url(url, headers=HEADERS)
        return {
            "url": url,
            "df": df,
        }

    def _get_data_file_url(self, url):
        soup = get_soup(url)
        elem = soup.find(class_="health-file__link")
        url = elem.get("href")
        return url

    def read_age(self) -> pd.DataFrame:
        df_1 = read_csv_from_url(self.source_url["age_1d"], header=1).dropna(axis=1, how="all")
        df_1 = df_1.melt("Date", var_name="age_group", value_name="people_vaccinated_per_hundred")
        df_2 = read_csv_from_url(self.source_url["age_2d"], header=1).dropna(axis=1, how="all")
        df_2 = df_2.melt("Date", var_name="age_group", value_name="people_fully_vaccinated_per_hundred")
        df = df_1.merge(df_2, on=["Date", "age_group"], how="left")
        return df

    def pipe_total_vaccinations(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(total_vaccinations=df.dose_1 + df.dose_2 + df.dose_3 + df.dose_4)

    def pipe_total_boosters(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(total_boosters=df.dose_3 + df.dose_4)

    def pipe_rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.rename(columns=self.columns_rename)

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.assign(date=df.date.apply(clean_date, fmt="%Y-%m-%d", minus_days=1))
        return df

    def pipe_patch_data(self, df: pd.DataFrame) -> pd.DataFrame:
        # total vaccinations
        msk = (df["date"] < "2022-10-06") & (df["date"] > "2022-08-25")
        df.loc[msk, "total_vaccinations"] = None
        # people vaccinated
        msk = (df["date"] < "2022-10-06") & (df["date"] > "2022-04-07")
        df.loc[msk, "people_vaccinated"] = None
        # # people fully vaccinated
        msk = (df["date"] < "2022-10-06") & (df["date"] > "2022-06-17")
        df.loc[msk, "people_fully_vaccinated"] = None
        return df

    def pipe_vaccine(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.pipe(build_vaccine_timeline, self.vaccine_timeline)

    def pipe_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(location=self.location, source_url=self.source_url_ref)

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.pipe(self.pipe_total_vaccinations)
            .pipe(self.pipe_total_boosters)
            .pipe(self.pipe_rename_columns)
            .pipe(self.pipe_date)
            .pipe(self.pipe_vaccine)
            .pipe(self.pipe_metadata)
            .pipe(self.pipe_patch_data)
            .pipe(self.pipe_filter_dp, ["2022-10-06", "2022-10-13", "2022-10-20", "2022-10-27", "2023-02-09"])
            .pipe(self.make_monotonic)
            .sort_values("date")[
                [
                    "date",
                    "location",
                    "vaccine",
                    "source_url",
                    "total_vaccinations",
                    "people_vaccinated",
                    "people_fully_vaccinated",
                    "total_boosters",
                ]
            ]
        )

    def pipe_age_groups(self, df):
        regex = r"(\d{1,2})+?(?:-(\d{1,2}))?"
        df[["age_group_min", "age_group_max"]] = df.age_group.str.extract(regex)
        return df

    def pipe_age_numeric(self, df):
        regex = r"([\d\.]+).*"
        metrics = ["people_vaccinated_per_hundred", "people_fully_vaccinated_per_hundred"]
        for metric in metrics:
            df.loc[:, metric] = df[metric].str.extract(regex, expand=False).astype(float)
        return df

    def pipe_age_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(
            date=clean_date_series(df.Date),
            location=self.location,
        )

    def pipeline_age(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.pipe(self.pipe_age_numeric)
            .pipe(self.pipe_age_metadata)
            .pipe(self.pipe_filter_dp, ["2022-10-07", "2022-10-14", "2022-10-21"])
            .pipe(self.make_monotonic, ["date", "age_group"])
            .pipe(self.pipe_age_groups)
            # .dropna(subset=["people_vaccinated_per_hundred", "people_fully_vaccinated_per_hundred"], how="all")
            .drop_duplicates(subset=["people_vaccinated_per_hundred", "people_fully_vaccinated_per_hundred"])
            .sort_values(["date", "age_group_min"])[
                [
                    "location",
                    "date",
                    "age_group_min",
                    "age_group_max",
                    "people_vaccinated_per_hundred",
                    "people_fully_vaccinated_per_hundred",
                ]
            ]
        )

    def export(self):
        # Main
        df = self.read().pipe(self.pipeline)  # Use with attach=False
        # Age
        df_age = self.read_age().pipe(self.pipeline_age)
        self.export_datafile(
            df=df,
            df_age=df_age,
            meta_age={"source_name": "Ministry of Health via covidbaseau.com", "source_url": self.source_url_ref},
            # attach=True,
        )

    def export_official(self):
        # Main
        df = self.pipeline_latest_from_official_source(self.read_latest_from_official_source())  # Use with attach=True
        # Age
        df_age = self.read_age().pipe(self.pipeline_age)
        self.export_datafile(
            df=df,
            df_age=df_age,
            meta_age={"source_name": "Ministry of Health via covidbaseau.com", "source_url": self.source_url_ref},
            attach=True,
        )
        # Further transform
        df = self.load_datafile()
        df = df.pipe(self.pipe_patch_data).pipe(self.make_monotonic)
        self.export_datafile(df)


def main():
    Australia().export()


def _get_date(res):
    match = re.search(URL_1, res["url"])
    if not match:
        print(res["url"])
    date_str = match.group(1)
    # print(xx["df"].shape)
    date = datetime.strptime(date_str, "%d-%B-%Y").strftime("%Y-%m-%d")
    return date


def _get_df(df):
    # Sanity check
    assert df.shape[1] == 2
    # Column names
    df.columns = ["variable", "value"]
    # dropna
    df = df.dropna(subset=["variable"])
    # Only national repots
    df = df[df["variable"].str.contains("National")]
    return df


def _parse_data(df):
    data = {}
    for variable, variables_source in VARIABLE_MAPPING.items():
        msk = df["variable"].isin(variables_source)
        data[variable] = int(df.loc[msk, "value"].sum())
    return data
