"merge"
import pandas as pd


def get_reprod(file_url: str, country_mapping: str):
    reprod = pd.read_csv(
        file_url,
        usecols=["Country/Region", "Date", "R"],
    )
    reprod = (
        # reprod[reprod["days_infectious"] == 7]
        # .drop(columns=["days_infectious"])
        reprod.rename(
            columns={
                "Country/Region": "location",
                "Date": "date",
                "R": "reproduction_rate",
            }
        ).round(2)
    )
    mapping = pd.read_csv(country_mapping)
    reprod = reprod.replace(dict(zip(mapping.reprod, mapping.owid)))
    return reprod
