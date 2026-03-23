import pandas as pd
from cowidev.utils.web import request_json


METADATA = {
    "source_url": "https://datadashboardapi.health.gov.il/api/queries/hospitalizationStatus",
    "source_url_ref": "https://datadashboard.health.gov.il/COVID-19/",
    "source_name": "Ministry of Health",
    "entity": "Israel",
}


def main():

    data = request_json(METADATA["source_url"], verify=False)
    df = pd.DataFrame.from_records(
        data,
        columns=["dayDate", "newHospitalized", "countHospitalized", "countBreathCum", "countCriticalStatus"],
    ).rename(columns={"dayDate": "date"})

    df["date"] = df.date.str.slice(0, 10)

    df = df.sort_values("date")

    df.loc[df.date < "2020-09-01", "countCriticalStatus"] = pd.NA

    df["newHospitalized"] = df.newHospitalized.rolling(7).sum()
    df["icu_admissions"] = (df.countBreathCum - df.countBreathCum.shift()).rolling(7).sum()

    df = (
        df.drop(columns="countBreathCum")
        .melt("date", var_name="indicator")
        .dropna(subset=["value"])
        .sort_values("date")
        .head(-1)
    )
    df["indicator"] = df.indicator.replace(
        {
            "countHospitalized": "Daily hospital occupancy",
            "countCriticalStatus": "Daily ICU occupancy",
            "icu_admissions": "Weekly new ICU admissions",
            "newHospitalized": "Weekly new hospital admissions",
        }
    )

    df["entity"] = METADATA["entity"]

    df = df.sort_values(["date", "indicator"])

    return df, METADATA


if __name__ == "__main__":
    main()
