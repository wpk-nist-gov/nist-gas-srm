"""Convert columns to database names"""

from pathlib import Path
from typing import cast

import pandas as pd

path = Path(__file__).parent.parent / "tmp/columns-name-mapping.xlsx"

df = pd.read_excel(path)  # pyright: ignore[reportUnknownMemberType]
df = df.dropna(how="all").ffill().astype({"rcert": "bool"})

out = {}
out_rcert = {}
for (rcert, tablename), g in df.groupby(["rcert", "table"], sort=False):
    val = dict(zip(g.excel, g.normalized))  # ruff: ignore[zip-without-explicit-strict]

    if cast("bool", rcert):
        out_rcert[tablename] = val
    else:
        out[tablename] = val


print("SRM_COLNAMES_TO_DBNAMES_MAPPER: Final[dict[str, dict[str, str]]] = ", out)  # ruff: ignore[print]  # pyright: ignore[reportUnknownArgumentType]
print()  # ruff: ignore[print]
print(  # ruff: ignore[print]
    "RCERT_COLNAMES_TO_DBNAMES_MAPPER: Final[dict[str, dict[str, str]]] = ",
    out_rcert,  # pyright: ignore[reportUnknownArgumentType]
)
print()  # ruff: ignore[print]
