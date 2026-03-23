import pandas as pd
from cowidev import PATHS


def load_status_get(path, path_ts):
    df = pd.read_csv(path)

    def _msg_err(x):
        try:
            err = x.replace("\n", "<br>")
            return f"<details><summary>show</summary><pre>{err}</pre></details>"
        except:
            return ""

    df = (
        df.assign(
            status=df.success.replace({True: "✅", False: "❌"}).fillna("⚠️"),
            status_id=df.success.replace({True: 1, False: 0}).fillna(0.5),
            error=df.error.apply(lambda x: _msg_err(x)),
        )
        .sort_values(["status_id", "timestamp", "execution_time (sec)"], ascending=[True, False, False])
        .drop(columns=["success", "status_id"])[["module", "status", "timestamp", "execution_time (sec)", "error"]]
    )
    table = df.to_html(index=False, escape=False)
    n_fail = (df.status == "❌").sum()
    n_skip = (df.status == "⚠️").sum()
    with open(path_ts, "r") as f:
        date_last = f.read()
    text = f"`{n_fail}/{len(df)}` scripts failed, `{n_skip}/{len(df)}` were skipped. Latest update was `{date_last}`."
    return f"""{text}

{table}
"""


def load_status_process(path, path_ts):
    df = pd.read_csv(path)

    def _msg_err(x):
        try:
            err = x.replace("\n", "<br>")
            return f"<details><summary>show</summary><pre>{err}</pre></details>"
        except:
            return ""

    df = (
        df.assign(
            status=df.success.replace({True: "✅", False: "❌"}).fillna("⚠️"),
            status_id=df.success.replace({True: 1, False: 0}).fillna(0.5),
            error=df.error.apply(lambda x: _msg_err(x)),
        )
        .sort_values(["status_id", "timestamp"], ascending=[True, False])
        .drop(columns=["success", "status_id"])[["location", "status", "timestamp", "error"]]
    )
    table = df.to_html(index=False, escape=False)
    n_fail = (df.status == "❌").sum()
    n_skip = (df.status == "⚠️").sum()
    with open(path_ts, "r") as f:
        date_last = f.read()
    text = f"`{n_fail}/{len(df)}` processes failed, `{n_skip}/{len(df)}` were skipped. Latest update was `{date_last}`."
    return f"""{text}

{table}
"""


def get_placeholder():
    return {
        "status-vax-get": load_status_get(
            PATHS.INTERNAL_OUTPUT_VAX_STATUS_GET, PATHS.INTERNAL_OUTPUT_VAX_STATUS_GET_TS
        ),
        "status-vax-process": load_status_process(
            PATHS.INTERNAL_OUTPUT_VAX_STATUS_PROCESS, PATHS.INTERNAL_OUTPUT_VAX_STATUS_PROCESS_TS
        ),
        "status-test-get": load_status_get(
            PATHS.INTERNAL_OUTPUT_TEST_STATUS_GET, PATHS.INTERNAL_OUTPUT_TEST_STATUS_GET_TS
        ),
    }


def generate_status(template: str, output: str):
    placeholders = get_placeholder()
    with open(template, "r", encoding="utf-8") as fr:
        s = fr.read()
        s = s.format(**placeholders)
        with open(output, "w", encoding="utf-8") as fw:
            fw.write(s)
