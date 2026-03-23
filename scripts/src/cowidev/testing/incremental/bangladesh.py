from cowidev.utils.web import get_soup
from cowidev.utils.clean import clean_count, clean_date
from cowidev.testing.utils.incremental import increment


class Bangladesh:
    location: str = "Bangladesh"
    units: str = "tests performed"
    source_label: str = "Government of Bangladesh"
    source_url: str = "https://dghs-dashboard.com/pages/covid19.php"
    notes: str = ""

    def _parse_data(self):
        soup = get_soup(self.source_url)
        date_raw = soup.select("span+ span")[0].text
        return {
            "count": clean_count(soup.select(".bg-success:nth-child(1) .info-box-number")[0].text),
            "date": clean_date(date_raw, "%d/%m/%Y"),
        }

    def export(self):
        data = self._parse_data()
        increment(
            daily_change=data["count"],
            sheet_name=self.location,
            country=self.location,
            units=self.units,
            date=data["date"],
            source_url=self.source_url,
            source_label=self.source_label,
        )


def main():
    Bangladesh().export()
