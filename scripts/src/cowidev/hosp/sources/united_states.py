import pandas as pd
from cowidev.utils.clean import clean_date_series

METADATA = {
    "source_url": "https://healthdata.gov/api/views/g62h-syeh/rows.csv",
    "source_url_ref": "https://healthdata.gov/Hospital/COVID-19-Reported-Patient-Impact-and-Hospital-Capa/g62h-syeh",
    "source_name": "U.S. Department of Health & Human Services",
    "entity": "United States",
}


def main():
    df = pd.read_csv(
        METADATA["source_url"],
        usecols=[
            "date",
            "total_adult_patients_hospitalized_confirmed_covid",
            "total_pediatric_patients_hospitalized_confirmed_covid",
            "staffed_icu_adult_patients_confirmed_covid",
            "previous_day_admission_adult_covid_confirmed",
            "previous_day_admission_pediatric_covid_confirmed",
        ],
    )
    df["date"] = clean_date_series(df.date, "%Y/%m/%d")
    df = df[df.date >= "2020-07-15"]
    df = df.groupby("date", as_index=False).sum().sort_values("date").head(-2)

    df["total_hospital_stock"] = df.total_adult_patients_hospitalized_confirmed_covid.fillna(0).add(
        df.total_pediatric_patients_hospitalized_confirmed_covid.fillna(0)
    )
    df["total_hospital_flow"] = df.previous_day_admission_adult_covid_confirmed.fillna(0).add(
        df.previous_day_admission_pediatric_covid_confirmed.fillna(0)
    )
    df["total_hospital_flow"] = df.total_hospital_flow.rolling(7).sum()

    df = (
        df[["date", "total_hospital_stock", "total_hospital_flow", "staffed_icu_adult_patients_confirmed_covid"]]
        .melt("date", var_name="indicator")
        .dropna(subset=["value"])
    )
    df["indicator"] = df.indicator.replace(
        {
            "total_hospital_stock": "Daily hospital occupancy",
            "staffed_icu_adult_patients_confirmed_covid": "Daily ICU occupancy",
            "total_hospital_flow": "Weekly new hospital admissions",
        }
    )

    df["entity"] = METADATA["entity"]

    return df, METADATA


if __name__ == "__main__":
    main()
