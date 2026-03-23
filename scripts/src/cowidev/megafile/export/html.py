import pandas as pd
import locale

from cowidev import PATHS


def pipe_vax_locations_to_html(df: pd.DataFrame) -> pd.DataFrame:
    locale.setlocale(locale.LC_TIME, "en_US")
    # build table
    country_faqs = {
        "Israel",
        "Palestine",
    }
    faq = ' (see <a href="https://ourworldindata.org/covid-vaccinations#frequently-asked-questions">FAQ</a>)'
    codes = [i for i in df.iso_code.tolist() if "OWID_" not in i or i == "OWID_KOS"]
    df = df.assign(
        location=(df.location.apply(lambda x: f"<td><strong>{x}</strong>{faq if x in country_faqs else ''}</td>")),
        source=('<td><a href="' + df.source_website + '">' + df.source_name + "</a></td>"),
        last_observation_date=(
            pd.to_datetime(df.last_observation_date).apply(lambda x: f"<td>{x.strftime('%b. %e, %Y')}</td>")
        ),
        vaccines=(df.vaccines.apply(lambda x: f"<td>{x}</td>")),
    )[["location", "source", "last_observation_date", "vaccines"]]
    df.columns = [col.capitalize().replace("_", " ") for col in df.columns]
    body = ("<tr>" + df.sum(axis=1) + "</tr>").sum(axis=0)
    header = "<tr>" + "".join(f"<th>{col}</th>" for col in df.columns) + "</tr>"
    html_table = f"<table><tbody>{header}{body}</tbody></table>"
    coverage_info = f"Vaccination against COVID-19 has now started in {len(codes)} locations."
    html_table = (f'<p><strong>{coverage_info}</strong></p><div class="tableContainer">{html_table}</div>\n').replace(
        "  ", " "
    )
    return html_table


def generate_htmls():
    # Vaccinations html source table
    df = pd.read_csv(PATHS.DATA_VAX_META_FILE)
    html_table = pipe_vax_locations_to_html(df)
    with open(PATHS.DATA_INTERNAL_VAX_TABLE, "w") as f:
        f.write(html_table)
