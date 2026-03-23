import pandas as pd

from cowidev.utils.clean import clean_date_series


METADATA = {
    "source_url_flow": "https://docs.google.com/spreadsheets/d/e/2PACX-1vRGCkIwakQ5rpfXky9FZhDwr3qUgerfhBLSzn9OsA79yQ_2G_y-_Ns9JjRJZWXD5kxJ3qicoL7bHGjE/pub?gid=1044172863&output=csv",
    "source_url_stock": "https://docs.google.com/spreadsheets/d/e/2PACX-1vRGCkIwakQ5rpfXky9FZhDwr3qUgerfhBLSzn9OsA79yQ_2G_y-_Ns9JjRJZWXD5kxJ3qicoL7bHGjE/pub?gid=1317252294&single=true&output=csv",
    "source_url_ref": (
        "https://docs.google.com/spreadsheets/d/1Ln3FO3E0hz2r_kCCWM6on9Wd18wRvrkiIV-bbE2EDQ0/edit#gid=1044172863"
    ),
    "source_name": (
        "National Policy Data Observatory (NPDO) at the Council for Scientific and Industrial Research (CSIR)"
    ),
    "entity": "South Africa",
}


def main() -> pd.DataFrame:

    flow = pd.read_csv(METADATA["source_url_flow"], usecols=["Week ending:", "National"]).rename(
        columns={"Week ending:": "date"}
    )
    stock = pd.read_csv(METADATA["source_url_stock"], usecols=["Dates", "Hospitalised", "ICU"]).rename(
        columns={"Dates": "date"}
    )

    df = (
        stock.merge(flow, on="date", how="left")  # validate="1:1")
        .melt("date", var_name="indicator")
        .dropna(subset=["value"])
        .replace(
            {
                "National": "Weekly new hospital admissions",
                "Hospitalised": "Daily hospital occupancy",
                "ICU": "Daily ICU occupancy",
            }
        )
    )

    df["date"] = clean_date_series(df.date, "%d/%m/%Y")
    df["entity"] = METADATA["entity"]

    return df, METADATA


if __name__ == "__main__":
    main()
