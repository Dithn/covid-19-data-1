import pandas as pd
from tableauscraper import TableauScraper as TS

from cowidev.utils import clean_date_series
from cowidev.vax.utils.base import CountryVaxBase


class Thailand(CountryVaxBase):
    location = "Thailand"
    source_url = "https://public.tableau.com/views/SATCOVIDDashboard/1-dash-tiles-w"
    source_url_ref = "https://ddc.moph.go.th/covid19-dashboard/"

    def read(self) -> pd.DataFrame:
        """Read data from source"""
        df = self._parse_data()
        return df

    def _parse_data(self) -> pd.DataFrame:
        """Parse metrics from source"""
        # Get raw dataframe
        ts = TS()
        ts.loads(self.source_url)
        return ts.getWorksheet("D_Vac_Stack (2)").data

    def _get_abailable_worksheets(ts):
        workbook = ts.getWorkbook()
        for t in workbook.worksheets:
            print(f"worksheet name : {t.name}")

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(date=clean_date_series(df["DAY(txn_date)-value"]))

    def pipe_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        df = (
            df.pivot("date", "vaccine_plan_group-alias", "SUM(vaccine_total_acm)-value")
            .reset_index()
            .rename(
                columns={
                    "1": "people_vaccinated",
                    "2": "people_fully_vaccinated",
                    "3": "total_boosters",
                }
            )
        )
        return df.assign(total_vaccinations=df.people_vaccinated + df.people_fully_vaccinated + df.total_boosters)

    def pipe_vaccines(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add vaccine information"""
        return df.assign(vaccine="Moderna, Oxford/AstraZeneca, Pfizer/BioNTech, Sinopharm/Beijing, Sinovac")

    def pipe_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add metadata"""
        return df.assign(location=self.location, source_url=self.source_url_ref)

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline for data"""
        return df.pipe(self.pipe_date).pipe(self.pipe_metrics).pipe(self.pipe_vaccines).pipe(self.pipe_metadata)

    def export(self):
        """Export data to CSV"""
        df = self.read()
        df = df.pipe(self.pipeline)
        self.export_datafile(df, attach=True)


def main():
    Thailand().export()
