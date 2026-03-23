import pandas as pd


METADATA = {
    "source_url_hosp_stock": "https://raw.githubusercontent.com/WWolf/korea-covid19-hosp-data/main/beds.csv",
    "source_url_hosp_flow_icu_stock": "https://github.com/WWolf/korea-covid19-hosp-data/raw/main/hospitalization.csv",
    "source_url_icu_flow": "https://raw.githubusercontent.com/WWolf/korea-covid19-hosp-data/main/weekly_icu.csv",
    "source_url_ref": (
        "http://ncov.mohw.go.kr/en/bdBoardList.do?brdId=16&brdGubun=161&dataGubun=&ncvContSeq=&contSeq=&board_id="
    ),
    "source_name": "Ministry of Health and Welfare, via WWolf on GitHub",
    "entity": "South Korea",
}


def main():

    hosp_flow_icu_stock = (
        pd.read_csv(
            METADATA["source_url_hosp_flow_icu_stock"],
            usecols=[
                "Date",
                "Hospitalizations with moderate to severe symptoms",
                "New hospital admissions (daily)",
            ],
            na_values="NA",
        )
        .rename(columns={"Date": "date"})
        .sort_values("date")
    )
    hosp_flow_icu_stock["New hospital admissions (daily)"] = (
        hosp_flow_icu_stock["New hospital admissions (daily)"].rolling(7).sum()
    )

    icu_flow = (
        pd.read_csv(
            METADATA["source_url_icu_flow"],
            usecols=["Date", "Hospital admissions with moderate to severe symptoms (weekly)"],
            na_values="NA",
        )
        .rename(columns={"Date": "date"})
        .sort_values("date")
    )

    hosp_stock = (
        pd.read_csv(METADATA["source_url_hosp_stock"])
        .drop_duplicates()
        .rename(columns={"Date": "date"})
        .sort_values("date")
    )
    hosp_stock["Daily hospital occupancy"] = (
        hosp_stock["위중증"] + hosp_stock["준중증"] + hosp_stock["중등증"] + hosp_stock["경증"]
    )
    hosp_stock = hosp_stock[["date", "Daily hospital occupancy"]]

    df = (
        hosp_flow_icu_stock.merge(icu_flow, on="date", how="outer", validate="one_to_one")
        .merge(hosp_stock, on="date", how="outer", validate="one_to_one")
        .melt("date", var_name="indicator")
        .dropna(subset=["value"])
    )
    df["indicator"] = df.indicator.replace(
        {
            "Hospitalizations with moderate to severe symptoms": "Daily ICU occupancy",
            "New hospital admissions (daily)": "Weekly new hospital admissions",
            "Hospital admissions with moderate to severe symptoms (weekly)": "Weekly new ICU admissions",
        }
    )

    df["entity"] = METADATA["entity"]

    # Filter outlier
    df = df[df.date != "2023-02-23"]
    return df, METADATA


if __name__ == "__main__":
    main()
