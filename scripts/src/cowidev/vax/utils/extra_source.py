import pandas as pd

from cowidev.vax.incremental.africacdc import AfricaCDC
from cowidev.vax.utils.orgs import ACDC_COUNTRIES_ALL
from cowidev.vax.utils.checks import METRICS


def add_latest_from_acdc(df: pd.DataFrame, metrics: list, priority: bool = False):
    # Get mapping countries
    locations = set(df.location)
    countries = {acdc: owid for acdc, owid in ACDC_COUNTRIES_ALL.items() if owid in locations}
    # Get ACDC data
    api = AfricaCDC(True)
    dfa = api.read()
    dfa = dfa.pipe(api.pipeline, countries, exclude=False)
    # Set ignored metrics to NA
    metrics_ignore = {m: pd.NA for m in METRICS if m not in metrics}
    dfa = dfa.assign(**metrics_ignore)
    # Do not use all-zero valued
    msk = (dfa[metrics] == 0).all(axis=1)
    dfa = dfa[~msk]
    # Concatenate
    df = pd.concat([df, dfa], ignore_index=True).sort_values(["date", "location"])
    # Propagate vaccines
    x = (
        df.dropna(subset=["vaccine"])
        .sort_values("date")
        .drop_duplicates()
        .rename(columns={"vaccine": "vaccine_latest"})
    )
    df = df.merge(x[["location", "vaccine_latest"]], on="location", how="outer")
    df = df.assign(vaccine=df.vaccine.fillna(df.vaccine_latest)).drop(columns=["vaccine_latest"])
    # Remove duplicates coming from WHO
    if priority:
        df = df.sort_values(["source_url"]).drop_duplicates(subset=["location", "date"], keep="first")
    return df
