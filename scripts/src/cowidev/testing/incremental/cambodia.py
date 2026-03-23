from cowidev.testing.utils.base import CountryTestBase
import pandas as pd

from cowidev.utils import get_soup, clean_count
from cowidev.utils.clean.dates import localdatenow


class Cambodia(CountryTestBase):
    location = "Cambodia"

    def export(self):

        data = pd.read_csv(self.output_path)

        url = "http://cdcmoh.gov.kh/"
        soup = get_soup(url)
        print(soup.select("span:nth-child(1) strong span"))

        count = clean_count(soup.select("p+ div strong:nth-child(1)")[0].text)

        date_str = localdatenow("Asia/Phnom_Penh")

        if count > data["Cumulative total"].max() and date_str > data["Date"].max():

            new = pd.DataFrame(
                {
                    "Country": self.location,
                    "Date": [date_str],
                    "Cumulative total": count,
                    "Source URL": url,
                    "Source label": "CDCMOH",
                    "Units": "tests performed",
                }
            )

            data = pd.concat([new, data], sort=False)
        self.export_datafile(data)


def main():
    Cambodia().export()
