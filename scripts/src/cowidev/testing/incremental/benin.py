from cowidev.testing.utils.base import CountryTestBase
import pandas as pd

from cowidev.utils import get_soup
from cowidev.utils.clean.dates import localdatenow


class Benin(CountryTestBase):
    location = "Benin"

    def export(self):

        data = pd.read_csv(self.output_path)

        url = "https://www.gouv.bj/coronavirus/"
        soup = get_soup(url)

        stats = soup.find_all("h2", attrs={"class", "h1 adapt white regular"})

        count = int(stats[0].text) + int(stats[1].text)
        date_str = localdatenow("Africa/Porto-Novo")

        if count > data["Cumulative total"].max() and date_str > data["Date"].max():

            new = pd.DataFrame(
                {
                    "Country": self.location,
                    "Date": [date_str],
                    "Cumulative total": count,
                    "Source URL": url,
                    "Source label": "Government of Benin",
                    "Units": "tests performed",
                }
            )

            df = pd.concat([new, data], sort=False)
            self.export_datafile(df)


def main():
    Benin().export()
