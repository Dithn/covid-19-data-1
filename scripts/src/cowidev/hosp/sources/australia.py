# NOTE from the author:
# Note: From December 2023, we will no longer be updating this site due to the very minimal COVID-19 data reporting from the federal and state/territory governments.

import io
import requests

import pandas as pd

METADATA = {
    "source_url": "https://covidbaseau.com/hospital-patients.csv",
    "source_url_ref": "https://covidbaseau.com",
    "source_name": "Official data from states via covidbaseau.com",
    "entity": "Australia",
}


def main():
    response = requests.get(METADATA["source_url"])
    df = pd.read_csv(io.StringIO(response.content.decode()))

    df = df.melt(id_vars="date", var_name="indicator").assign(entity=METADATA["entity"])
    df["indicator"] = df.indicator.replace(
        {
            "hospital_patients": "Daily hospital occupancy",
            "icu_patients": "Daily ICU occupancy",
        }
    )

    return df, METADATA


if __name__ == "__main__":
    main()
