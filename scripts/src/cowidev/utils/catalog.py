from owid.catalog import catalogs, RemoteCatalog, Table
from typing import List, Literal


def load_table_from_catalog(
        namespace: str,
        dataset: str,
        table: str,
        channels: List[Literal["meadow", "garden", "grapher"]] = ["garden"],
        remote: bool = False,
    ) -> Table:
    if remote:
        values = catalogs.find(namespace=namespace, dataset=dataset, table=table)
        tb = values.sort_values("version").iloc[-1].load()
    else:
        cat = RemoteCatalog(channels=channels)
        tb = cat.find_latest(namespace=namespace, dataset=dataset, table=table)
    return tb
