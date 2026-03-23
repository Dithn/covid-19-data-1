from datetime import datetime

import pandas as pd

from cowidev.cmd.vax.track.vaccines import vaccines_comparison_with_who
from cowidev import PATHS


def get_who_data():
    # Load WHO
    # url = "https://covid19.who.int/who-data/vaccination-data.csv"
    url = "https://srhdpeuwpubsa.blob.core.windows.net/whdh/COVID/vaccination-data.csv"
    df_who = pd.read_csv(url, usecols=["ISO3", "COUNTRY", "DATA_SOURCE"])
    df_who = df_who.rename(columns={"COUNTRY": "location_WHO"})
    # Countries WHO relies on us
    df_who = df_who.assign(reporting_to_WHO=df_who.DATA_SOURCE == "OWID")
    return df_who


def country_updates_summary(
    path_vaccinations: str = None,
    path_locations: str = None,
    path_automation_state: str = None,
    as_dict: bool = False,
    sortby_counts: bool = False,
    sortby_updatefreq: bool = False,
    who: bool = False,
    vaccines: bool = False,
    metric_counts: bool = False,
):
    """Check last updated countries.

    It loads the content from locations.csv, vaccinations.csv and automation_state.csv to present results on the update
    frequency and timeline of all countries. By default, the countries are sorted from least to most recently updated.
    You can also sort them from least to most frequently updated ones by using argument `sortby_counts`.

    In Jupyter is recommended to ass the following lines to enable the DataFrame to be fully shown:

    ```python
    import pandas as pd
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_colwidth', None)
    ```

    Args:
        path_vaccinations (str, optional): Path to vaccinations csv file.
                                            Default value works if repo structure is left unmodified.
        path_locations (str, optional): Path to locations csv file.
                                        Default value works if repo structure is left unmodified.
        path_automation_state (str, optional): Path to automation state csv file.
                                                Default value works if repo structure is left unmodified.
        as_dict (bool, optional): Set to True for the return value to be shaped as a dictionary. Otherwise returns a
                                    DataFrame.
        sortby_counts (bool, optional): Set to True to sort resuls from least to most updated countries.
        who (bool, optional): Display WHO columns
        metric_counts (bool, optional): Set to True to display how many rows with a non-null value for each metric
                                        appear.
    Returns:
        Union[pd.DataFrame, dict]: List or DataFrame, where each row (or element) contains five fields:
                                    - 'last_observation_date': Last update date.
                                    - 'location': Country name.
                                    - 'source_website': Source used to retrieve last added data.
                                    - 'automated': True if country process is automated.
                                    - 'counts': Number of times the country has been updated.
    """
    # Get data paths
    if not path_vaccinations:
        path_vaccinations = PATHS.DATA_VAX_MAIN_FILE
    if not path_locations:
        path_locations = PATHS.DATA_VAX_META_FILE
    if not path_automation_state:
        path_automation_state = PATHS.INTERNAL_OUTPUT_VAX_AUTOM_FILE
    columns_output = [
        "location",
        "last_observation_date",
        "first_observation_date",
        "counts",
        "update_frequency",
        "num_observation_days",
        "source_website",
        "automated",
    ]
    # Read data
    df_vax = pd.read_csv(path_vaccinations)
    df_loc = pd.read_csv(path_locations)
    df_state = pd.read_csv(path_automation_state)
    df_who = get_who_data()
    # Get counts
    metrics = ["total_vaccinations", "people_vaccinated", "people_fully_vaccinated", "total_boosters"]
    df_vax = df_vax.dropna(
        subset=metrics,
        how="all",
    )
    df_vax_ = pd.DataFrame(
        {
            "counts": df_vax.groupby("location").date.count().sort_values(),
            "first_observation_date": df_vax.groupby("location").date.min(),
        }
    )
    if metric_counts:
        metrics_rename = {m: f"{m}_counts" for m in metrics}
        df_vax_metrics = df_vax.groupby("location", as_index=False)[metrics].nunique().rename(columns=metrics_rename)
        df_vax_ = df_vax_.merge(df_vax_metrics, on="location")
        columns_output += list(metrics_rename.values())
    df_vax = df_vax_.copy()

    # Merge data
    df = df_loc.merge(df_state, on="location")
    df = df.merge(df_vax, on="location")
    # Merge with WHO
    if who:
        # print(df_who.columns)
        df = df.merge(df_who, left_on="iso_code", right_on="ISO3", how="left")
        columns_output += ["reporting_to_WHO", "location_WHO"]
    # Additional fields
    num_observation_days = (datetime.now() - pd.to_datetime(df.first_observation_date)).dt.days + 1
    num_updates_per_observation_day = df.counts / num_observation_days

    df = df.assign(
        num_observation_days=num_observation_days,
        update_frequency=num_updates_per_observation_day,
    )
    # Sort data
    if sortby_updatefreq:
        sort_column = "update_frequency"
    elif sortby_counts:
        sort_column = "counts"
    else:
        sort_column = "last_observation_date"
    df = df.sort_values(by=sort_column)[columns_output]

    def _web_type(x):
        govs = [
            ".gov/",
            "gov.",
            ".gob.",
            ".moh.",
            ".gub.",
            ".go.",
            ".gouv.",
            "govern",
            ".govt",
            ".coronavirus2020.kz/",
            "thl.fi",
            ".gv.",
            "corona.nun.gl",
            "exploregov.ky",
            "covid19response.lc/",
            "corona.fo/",
            "103.247.238.92/webportal/",
            "data.public.lu/",
            "vaccinocovid.iss.sm/",
            "koronavirus.hr",
            "koronavirusinfo.az",
            "covid.is",
            "government.",
            "covid19ireland-geohive.hub.arcgis",
            "sacoronavirus.co.za",
            "covidodgovor.me",
            "experience.arcgis.com/experience/59226cacd2b441c7a939dca13f832112/",
            "guineasalud.org/estadisticas/",
            "bakuna.cw/",
            "laatjevaccineren.sr/",
            "coronavirus.bg/bg/statistika",
            "admin.ch",
            "folkhalsomyndigheten.se/",
            "covid19.ssi.dk/",
            "fhi.no/",
            "impfdashboard.de/",
            "covid-19.nczisk.sk",
            "opendata.digilugu.ee",
            ".mzcr.cz/",
            "ghanahealthservice.org/",
            "ccss.sa.cr/",
            "epistat.wiv-isp.be",
            "covidmaroc.ma",
            "experience.arcgis.com/experience/cab84dcfe0464c2a8050a78f817924ca",
            "gtmvigilanciacovid.shinyapps",
            "belta.by",
            "fohm.se",
            "moh.",
            "vaccines.ncdc.ge",
            "opendata.swiss",
        ]
        if "facebook." in x.lower():
            return "Facebook"
        elif "twitter." in x.lower():
            return "Twitter"
        elif "github." in x.lower() or "githubusercontent" in x.lower():
            return "GitHub"
        elif any(gov in x.lower() for gov in govs):
            return "Govern/Official"
        elif (".who.int" in x.lower()) or ("who.maps.arcgis.com" in x.lower()):
            return "WHO"
        elif ".pacificdata.org" in x.lower():
            return "SPC"
        elif "ecdc.europa." in x.lower():
            return "ECDC"
        elif "paho.org" in x.lower():
            return "PAHO"
        elif "africacdc.org" in x.lower():
            return "Africa CDC"
        else:
            return "Others"

    df = df.assign(**{"web_type": df.source_website.apply(_web_type)})

    if vaccines:
        df_vax = vaccines_comparison_with_who()
        df = df.merge(
            df_vax[["location", "vaccines_used_owid", "vaccines_used_who", "missing_in_who", "missing_in_owid"]],
            on="location",
            how="left",
        )
    # Return data
    if as_dict:
        return df.to_dict(orient="records")
    return df


def countries_missing(
    path_population: str = None,
    path_locations: str = None,
    ascending: bool = False,
    as_dict: bool = False,
):
    """Get countries currently not present in our dataset.

    Args:
        path_population (str, optional): Path to UN population csv file.
                                            Default value works if repo structure is left unmodified.
        path_locations (str, optional): Path to locations csv file.
                                        Default value works if repo structure is left unmodified.
        ascending (bool, optional): Set to True to sort results in ascending order. By default sorts in ascedning
                                    order.
        as_dict (bool, optional): Set to True for the return value to be shaped as a dictionary. Otherwise returns a
                                    DataFrame.
    """
    if not path_population:
        path_population = PATHS.INTERNAL_INPUT_UN_POPULATION_FILE
    if not path_locations:
        path_locations = PATHS.DATA_VAX_META_FILE
    df_loc = pd.read_csv(path_locations, usecols=["location"])
    df_pop = pd.read_csv(path_population)
    df_pop = df_pop[df_pop.iso_code.apply(lambda x: isinstance(x, str) and len(x) == 3)]
    df_mis = df_pop.loc[~df_pop["entity"].isin(df_loc["location"]), ["entity", "population"]]
    # Sort
    if not ascending:
        df_mis = df_mis.sort_values(by="population", ascending=False)
    # Return data
    if as_dict:
        return df_mis.to_dict(orient="records")
    return df_mis
