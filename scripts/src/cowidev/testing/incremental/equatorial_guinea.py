import os
from datetime import date
from cowidev.testing.utils.base import CountryTestBase

import pandas as pd

from cowidev.utils import get_soup, clean_count


class EquatorialGuinea(CountryTestBase):
    location = "Equatorial Guinea"

    def export(self):
        url = "https://guineasalud.org/estadisticas/"

        soup = get_soup(url)
        stats = soup.find_all("tr")
        count = clean_count(stats[9].find_all("td")[-1].text)

        date_str = date.today().strftime("%Y-%m-%d")
        df = pd.DataFrame(
            {
                "Country": self.location,
                "Date": [date_str],
                "Cumulative total": count,
                "Source URL": url,
                "Source label": "Ministerio de Sanidad y Bienestar Social",
                "Units": "tests performed",
                "Notes": pd.NA,
            }
        )

        if os.path.isfile(self.output_path):
            existing = pd.read_csv(self.output_path)
            if count > existing["Cumulative total"].max() and date_str > existing["Date"].max():
                df = pd.concat([df, existing]).sort_values("Date", ascending=False).drop_duplicates()
                df.to_csv(self.output_path, index=False)


def main():
    EquatorialGuinea().export()
