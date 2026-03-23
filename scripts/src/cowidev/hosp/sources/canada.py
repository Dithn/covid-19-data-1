"""As of April 4, 2024, we no longer report COVID-19 hospital use. This is due to the limited amount of data available to report a valid national number and weekly trend. Please refer to provincial and territorial web pages for regional level information.
"""

import pandas as pd

METADATA = {
    "source_url": "https://health-infobase.canada.ca/src/data/covidLive/covid19-epiSummary-hospVentICU.csv",
    "source_url_ref": "https://health-infobase.canada.ca/covid-19/",
    "source_name": "Government of Canada",
    "entity": "Canada",
}


def main():
    df = (
        pd.read_csv(
            METADATA["source_url"],
            usecols=[
                "Date",
                "COVID_HOSP",
                "COVID_ICU",
            ],
        )
        .rename(columns={"Date": "date"})
        .melt("date", ["COVID_HOSP", "COVID_ICU"], "indicator")
        .replace(
            {
                "COVID_HOSP": "Daily hospital occupancy",
                "COVID_ICU": "Daily ICU occupancy",
            }
        )
        .assign(entity=METADATA["entity"])
    )

    return df, METADATA


if __name__ == "__main__":
    main()
