import requests
import zipfile
import io
import tempfile
import os

import pandas as pd

from cowidev.utils import get_soup
from cowidev.utils.clean.dates import clean_date, localdatenow

from cowidev.vax.utils.base import CountryVaxBase
from cowidev.vax.utils.checks import VACCINES_ONE_DOSE


class Denmark(CountryVaxBase):
    location = "Denmark"
    source_url_ref = "https://covid19.ssi.dk/overvagningsdata/download-fil-med-vaccinationsdata"
    vaccines_mapping = {
        "AstraZeneca Covid-19 vaccine": "Oxford/AstraZeneca",
        "Janssen COVID-19 vaccine": "Johnson&Johnson",
        "Moderna Covid-19 Vaccine": "Moderna",
        "Moderna/Spikevax Covid-19 Vacc.": "Moderna",
        "Moderna/Spikevax Covid-19 0,5 ml": "Moderna",
        "Pfizer BioNTech Covid-19 vacc": "Pfizer/BioNTech",
        "Pfizer/Comirnaty Original/Omikron BA1": "Pfizer/BioNTech",
        "Uspecificeret": "Unknown",
    }
    regions_accepted = {
        "Nordjylland",
        "Midtjylland",
        "Syddanmark",
        "Hovedstaden",
        "Sjælland",
    }
    date_limit_one_dose = "2021-05-27"

    @property
    def date_limit_one_dose_ddmmyyyy(self):
        return clean_date(self.date_limit_one_dose, "%Y-%m-%d", output_fmt="%d%m%Y")

    def read(self, gap_days, bfill=True) -> pd.DataFrame:
        url = self._parse_link_zip()
        with tempfile.TemporaryDirectory() as tf:
            # Download and extract
            self._download_and_extract_data(url, tf)
            # Load data
            df = self._load_data(tf)
        if bfill:
            df_bfill = self._read_single_shots_bfill(index=gap_days)
            df = df.merge(df_bfill, on="date", how="left")
            df = df.assign(
                single_shots=df.single_shots_x.fillna(df.single_shots_y),
                single_shots_2nd=df.single_shots_2nd_x.fillna(df.single_shots_2nd_y),
            )
        return df

    def _load_data(self, path):
        df = self._read_data(path)
        df_ss = pd.DataFrame([self._read_single_shots_daily(path)])
        df = df.merge(df_ss, on="date", how="left")
        return df

    def _parse_link_zip(self) -> str:
        """Get link to latest pdf."""
        soup = get_soup(self.source_url_ref)
        url = soup.find("a", string="Download her").get("href")
        return url

    def _download_and_extract_data(self, url, output_path):
        r = requests.get(url)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(output_path)

    def _read_data(self, path) -> pd.DataFrame:
        path = _build_filepath(path, "Vaccine_dato.csv")

        df = (
            _load_datafile(path)
            .rename(
                columns={
                    "Dato": "date",
                    "Antal 1. stik": "people_vaccinated",
                    "Antal 2. stik": "people_fully_vaccinated",
                    "Antal 3. stik": "total_boosters",
                }
            )
            # .groupby("date", as_index=False)
            # .sum()
            .sort_values("date")
            .transform(
                {
                    "date": lambda x: x,
                    "people_vaccinated": lambda x: x.cumsum(),
                    "people_fully_vaccinated": lambda x: x.cumsum(),
                    "total_boosters": lambda x: x.cumsum(),
                }
            )
        )
        return df

    def _read_single_shots_bfill(self, index=None, date_limit=None):
        """Read single shots using bfill (iterates over old links)"""
        links = self._get_file_links_bfill(index=index, date_limit=date_limit)
        records = []
        for link in links[:1]:
            # print("Back filling (single shots)", link)
            with tempfile.TemporaryDirectory() as tf:
                self._download_and_extract_data(link, tf)
                records.append(self._read_single_shots_daily(tf))
        df = pd.DataFrame(records).drop_duplicates(subset=["date"], keep="last")
        return df

    def _read_single_shots_daily(self, path) -> dict:
        # single shots
        path_ = _build_filepath(path, "Vaccine_type_region.csv")
        df = _load_datafile(path_)
        msk = df["Vaccinenavn"].replace(self.vaccines_mapping).isin(VACCINES_ONE_DOSE)
        single_shots = df.loc[msk, "Antal 1. stik"].sum()
        single_shots_2nd = df.loc[msk, "Antal 2. stik"].sum()
        # Check vaccine names
        vaccines_wrong = set(df.Vaccinenavn).difference(self.vaccines_mapping)
        if vaccines_wrong:
            raise ValueError(f"Unknown vaccine(s) {vaccines_wrong}")
        regions_wrong = set(df.Region).difference(self.regions_accepted)
        if vaccines_wrong:
            raise ValueError(f"Unknown region(s) {regions_wrong}")
        # Load date
        path_ = _build_filepath(path, "Vaccine_dato.csv")
        df = _load_datafile(path_)
        date = df.Dato.max()
        return {
            "date": date,
            "single_shots": single_shots,
            "single_shots_2nd": single_shots_2nd,
        }

    def _get_file_links_bfill(self, index=None, date_limit=None):
        soup = get_soup(self.source_url_ref)
        links = [x.a.get("href") for x in soup.find_all("h5")]
        if index is None:
            date_limit = date_limit if date_limit is not None else self.date_limit_one_dose_ddmmyyyy
            i = [i for i, l in enumerate(links) if date_limit in l]
            index = i[0]
        links = links[:index]
        return links

    def pipe_vaccine(self, df: pd.DataFrame) -> pd.DataFrame:
        def _enrich_vaccine(date: str) -> str:
            if date >= self.date_limit_one_dose:
                return "Johnson&Johnson, Moderna, Pfizer/BioNTech"
            if date >= "2021-04-14":
                return "Moderna, Pfizer/BioNTech"
            if date >= "2021-02-08":
                return "Moderna, Oxford/AstraZeneca, Pfizer/BioNTech"
            if date >= "2021-01-13":
                return "Moderna, Pfizer/BioNTech"
            return "Pfizer/BioNTech"

        return df.assign(vaccine=df.date.astype(str).apply(_enrich_vaccine))

    def pipe_metrics(self, df: pd.DataFrame, df_current: pd.DataFrame) -> pd.DataFrame:
        # Merge current data with new
        df = df.merge(df_current, on="date", how="left")
        df = df.assign(
            single_shots=df.single_shots.fillna(df.single_shots_current),
            single_shots_2nd=df.single_shots_2nd.fillna(df.single_shots_2nd_current),
        )
        df = df.assign(
            total_vaccinations=(
                df.people_vaccinated.ffill().fillna(0)  # first dose + single shots
                + df.people_fully_vaccinated.ffill().fillna(0)  # second doses (inc. from single shot vax)
                + df.total_boosters.ffill().fillna(0)  # third dose
            ),
            people_fully_vaccinated=(
                df.people_fully_vaccinated.ffill().fillna(0)  # second doses (inc. from single shot vax)
                + df.single_shots.ffill().fillna(0)  # single shots
                - df.single_shots_2nd.ffill().fillna(0)  # secon doses of single shots
            ),
            total_boosters=(
                df.total_boosters.ffill().fillna(0)  # single shots
                + df.single_shots_2nd.ffill().fillna(0)  # secon doses of single shots
            ),
        )
        return df

    def pipeline(self, df: pd.DataFrame, df_current: pd.DataFrame) -> pd.DataFrame:
        return (
            df.assign(
                location=self.location,
                source_url=self.source_url_ref,
            )
            .pipe(self.pipe_vaccine)
            .pipe(self.pipe_metrics, df_current)[
                [
                    "location",
                    "date",
                    "vaccine",
                    "source_url",
                    "total_vaccinations",
                    "people_vaccinated",
                    "people_fully_vaccinated",
                    "total_boosters",
                    "single_shots",
                    "single_shots_2nd",
                ]
            ]
        )

    def read_current(self):
        return pd.read_csv(self.output_path, usecols=["date", "single_shots", "single_shots_2nd"]).rename(
            columns={"single_shots": "single_shots_current", "single_shots_2nd": "single_shots_2nd_current"}
        )

    def _get_num_gap_days(self, df_current):
        return (
            localdatenow(tz=None, as_datetime=True) - clean_date(df_current.date.max(), "%Y-%m-%d", as_datetime=True)
        ).days

    def export(self):
        # Read current
        df_current = self.read_current()
        # print(df_current.columns)
        index = self._get_num_gap_days(df_current)
        # Read new
        df = self.read(index).pipe(self.pipeline, df_current).pipe(self.make_monotonic)
        # Export
        df.to_csv(self.output_path, index=False)


def _load_datafile(path):
    """Read csv file."""
    df = pd.read_csv(path, encoding="iso-8859-1", sep=";")
    if len(df.columns) == 1:
        df = pd.read_csv(path, encoding="iso-8859-1", sep=",")
    return df


def _build_filepath(path, filename):
    """Build filepath."""
    return os.path.join(path, "Vaccine_DB", filename)


def main():
    Denmark().export()
