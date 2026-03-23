import logging
import re
from datetime import datetime, timedelta
from urllib.error import HTTPError

import pandas as pd

from cowidev.utils import clean_count, clean_date_series, clean_date
from cowidev.vax.utils.base import CountryVaxBase


# When checking which vaccines are listed, we want to ignore these columns
COLUMNS_VAX_IGNORE = ["Dosis entregadas total (1)"]


class Spain(CountryVaxBase):
    location = "Spain"
    vaccine_mapping = {
        "Pfizer": "Pfizer/BioNTech",
        "Moderna": "Moderna",
        "AstraZeneca": "Oxford/AstraZeneca",
        "Janssen": "Johnson&Johnson",
    }
    _date_field_raw = "Fecha de la última vacuna registrada(1)"
    _max_days_back = 70

    def read(self, last_update: str) -> pd.Series:
        return self._parse_data(last_update)

    def _parse_data(self, last_update: str):
        """Goes back _max_days_back days to retrieve data.

        Does not exceed `last_update` date.
        """
        records = []
        for days in range(self._max_days_back):
            date_it = clean_date(datetime.now() - timedelta(days=days))
            # print(date_it)
            # print(f"{date_it} > {last_update}?")
            if date_it > last_update:
                source = self._get_source_url(date_it.replace("-", ""))
                
                try:
                    df_1 = pd.read_excel(source, sheet_name="Comunicacion_1", index_col=0)
                    df_2 = pd.read_excel(source, sheet_name="Comunicacion_2", index_col=0, parse_dates=[self._date_field_raw])
                except HTTPError:
                    # print(f"Date {date_it} not available!")
                    print(f"Date {date_it} not available!")
                else:
                    # print("Adding!")
                    print(date_it, source)
                    self._check_vaccine_names(df_1)
                    ds = self._parse_data_day(df_1, df_2, source)
                    records.append(ds)
            else:
                # print("End!")
                break
        if len(records) > 0:
            return pd.DataFrame(records)
        print("No data being added to Spain")
        return None

    def _parse_data_day(self, df_1: pd.DataFrame, df_2: pd.DataFrame, source: str) -> pd.Series:
        """Parse data for a single day"""
        # Get data from Comunicacion_2
        df_2.loc[~df_2.index.isin(["Sanidad Exterior"]), self._date_field_raw].dropna().max()
        data = {
            "people_vaccinated": clean_count(df_2.loc["Totales", "Nº Personas con al menos 1 dosis"]),
            "people_fully_vaccinated": clean_count(df_2.loc["Totales", "Nº Personas con pauta completa"]),
            "date": clean_date(
                df_2.loc[
                    ~df_2.index.isin(["Sanidad Exterior"]),
                    self._date_field_raw,
                ]
                .dropna()
                .max()
            ),
            "source_url": source,
        }
        if (col_boosters := "Nº Personas con 1ª dosis de recuerdo(2)") in df_2.columns:
            # print("EEE")
            data["total_boosters"] = clean_count(df_2.loc["Totales", col_boosters])

        # Get data from Comunicacion_1
        data["total_vaccinations"] = clean_count(round(df_1.loc["Totales", "Dosis administradas (2)*"]))
        data["vaccine"] = ", ".join(self._get_vaccine_names(df_1, translate=True))
        return pd.Series(data=data)

    def _get_source_url(self, dt_str):
        return (
            "https://www.sanidad.gob.es/profesionales/saludPublica/ccayes/alertasActual/nCov/documentos/"
            f"Informe_Comunicacion_{dt_str}.ods"
        )

    def _get_vaccine_names(self, df: pd.DataFrame, translate: bool = False):
        regex_vaccines = r"Dosis entregadas ([a-zA-Z]*) \(1\)"
        if translate:
            return sorted(
                [
                    self.vaccine_mapping[re.search(regex_vaccines, col).group(1)]
                    for col in df.columns if col not in COLUMNS_VAX_IGNORE
                    if re.match(regex_vaccines, col)
                ]
            )
        else:
            return sorted(
                [re.search(regex_vaccines, col).group(1) for col in df.columns if re.match(regex_vaccines, col) and col not in COLUMNS_VAX_IGNORE]
            )

    def _check_vaccine_names(self, df: pd.DataFrame):
        vaccines = self._get_vaccine_names(df)
        unknown_vaccines = set(vaccines).difference(self.vaccine_mapping.keys())
        if unknown_vaccines:
            raise ValueError("Found unknown vaccines: {}".format(unknown_vaccines))

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(date=clean_date_series(df[self._date_field_raw]))

    def pipe_location(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(location=self.location)

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.pipe(self.pipe_location)

    def export(self):
        last_update = self.load_datafile().date.astype(str).max()
        df = self.read(last_update)
        if df is not None:
            df = df.pipe(self.pipeline)
            self.export_datafile(df, attach=True)


def main():
    Spain().export()
