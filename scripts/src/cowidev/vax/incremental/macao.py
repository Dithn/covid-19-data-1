import time
import re

from cowidev.utils.clean import clean_count, extract_clean_date
from cowidev.utils.web import get_driver
from cowidev.vax.utils.incremental import increment


class Macao:
    source_url = "https://www.ssm.gov.mo/apps1/PreventCOVID-19/en.aspx"
    location = "Macao"

    def read_old(self):
        """Create data."""
        with get_driver() as driver:
            # Get main page
            driver.get(self.source_url)
            time.sleep(5)
            # Get element
            # iframe_url = "https://www.ssm.gov.mo/apps1/COVID19Case/en.aspx"
            iframe_url = self._get_iframe_url(driver)
            # Build data
            print(iframe_url)
            data = self._parse_data(iframe_url, driver)
            return data

    def read(self):
        with get_driver() as driver:
            url = "https://www.ssm.gov.mo/apps1/COVID19Case/en.aspx"
            data = self._parse_data(url, driver)
            return data

    def _get_iframe_url(self, driver):
        """Get iframe url."""
        elem = driver.find_element_by_id("ICovid19Monitor")
        return elem.get_property("src")

    def _parse_data(self, url, driver):
        driver.get(url)
        # Obtain metrics
        # total_vaccinations
        elem = self._get_elem_div(driver, "Total doses administered (local and non-local)")
        total_vaccinations = clean_count(
            re.search(r"Total doses administered \(local and non-local\) : ([\d,]+).*", elem.text).group(1)
        )
        # people_vaccinated
        elem = self._get_elem_div(driver, "Total number of people vaccinated")
        people_vaccinated = clean_count(re.search(r"Total number of people vaccinated : (\d+)", elem.text).group(1))
        # people_with_2_doses_or_more
        elem = self._get_elem_div(driver, "Number of people completed 2 or more doses")
        people_with_2_doses_or_more = clean_count(
            re.search(r"Number of people completed 2 or more doses : (\d+)", elem.text).group(1)
        )
        # Obtain date
        elem = self._get_elem_div(driver, "updated on:")
        date = extract_clean_date(elem.text, r"updated on:(\d\d/\d\d/20\d\d)", "%d/%m/%Y")
        # Build dict
        data = {
            "total_vaccinations": total_vaccinations,
            "people_vaccinated": people_vaccinated,
            "people_fully_vaccinated": people_with_2_doses_or_more,
            "total_boosters": total_vaccinations - people_vaccinated - people_with_2_doses_or_more,
            "source_url": url,
            "date": date,
        }
        return data

    def _get_elem_div(self, driver, text_match):
        elem = driver.find_elements_by_xpath(f"//div[contains(text(), '{text_match}')]")
        print(elem)
        assert len(elem) == 1
        return elem[0]

    def _parse_date(self, element):
        """Get data from report file title."""
        r = r".* \(Last updated: (\d\d\/\d\d\/20\d\d) .*\)"
        return extract_clean_date(element.text, r, "%d/%m/%Y")

    def export(self):
        data = self.read()
        increment(
            location=self.location,
            total_vaccinations=data["total_vaccinations"],
            people_vaccinated=data["people_vaccinated"],
            people_fully_vaccinated=data["people_fully_vaccinated"],
            total_boosters=data["total_boosters"],
            date=data["date"],
            source_url=data["source_url"],
            # vaccines in use: https://www.ssm.gov.mo/apps1/covid19vaccine/en.aspx#vactype
            vaccine="Pfizer/BioNTech, Sinopharm/Beijing",
        )


def main():
    Macao().export()
