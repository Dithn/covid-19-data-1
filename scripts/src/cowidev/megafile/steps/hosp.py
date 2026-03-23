"merge"
import pandas as pd


def get_hosp(data_file: str):
    # TODO: Change input to be non-grapher file
    hosp = pd.read_csv(data_file)
    hosp = hosp.rename(
        columns={
            "Country": "location",
            "Year": "date",
            "Daily ICU occupancy": "icu_patients",
            "Daily ICU occupancy per million": "icu_patients_per_million",
            "Daily hospital occupancy": "hosp_patients",
            "Daily hospital occupancy per million": "hosp_patients_per_million",
            "Weekly new ICU admissions": "weekly_icu_admissions",
            "Weekly new ICU admissions per million": "weekly_icu_admissions_per_million",
            "Weekly new hospital admissions": "weekly_hosp_admissions",
            "Weekly new hospital admissions per million": "weekly_hosp_admissions_per_million",
        }
    ).round(3)
    hosp.loc[:, "date"] = (
        ([pd.to_datetime("2020-01-21")] * hosp.shape[0]) + hosp["date"].apply(pd.offsets.Day)
    ).astype(str)
    return hosp
