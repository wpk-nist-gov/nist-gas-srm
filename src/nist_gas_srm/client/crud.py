from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID

from nist_gas_srm.core import basemodels
from nist_gas_srm.core.missing import MISSING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any, BinaryIO, Literal

    from httpx import Client, Response

    from nist_gas_srm.core.missing import MissingType

    SubTable = Literal["measurements", "standard-analysis", "rcert"]


def _get_srm_params(
    srm_query: str | basemodels.srm.SRMQuery | MissingType,
    *,
    srm_id: int | MissingType = MISSING,
    batch_id: str | MissingType | None = MISSING,
    lot_id: str | MissingType | None = MISSING,
    srm_table_id: str | UUID | MissingType = MISSING,
    raise_if_empty: bool = False,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    if srm_table_id is not MISSING:
        params["id"] = srm_table_id

    if srm_query is not MISSING:
        params["srm_query"] = (
            srm_query
            if isinstance(srm_query, str)
            else srm_query.model_dump_json(exclude_unset=True)
        )

    params.update(
        basemodels.srm.SRMQuery.from_params_exclude_missing(
            srm_id=srm_id, batch_id=batch_id, lot_id=lot_id
        ).model_dump(exclude_unset=True)
    )

    if raise_if_empty and not params:
        msg = "No parameters to query"
        raise ValueError(msg)

    return params


def get_single_table(
    client: Client,
    *,
    url: str,
    srm_id: int | MissingType = MISSING,
    batch_id: str | MissingType | None = MISSING,
    lot_id: str | MissingType | None = MISSING,
    srm_query: str | basemodels.srm.SRMQuery | MissingType = MISSING,
    srm_table_id: str | UUID | MissingType = MISSING,
    complete: bool = False,
    subtable: SubTable | MissingType = MISSING,
) -> Response:
    if subtable is not MISSING:
        url = f"{url}/{subtable}"
    if complete:
        url = f"{url}/complete"

    params = _get_srm_params(
        srm_query,
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
        srm_table_id=srm_table_id,
        raise_if_empty=True,
    )
    return client.get(url, params=params)


get_srm = partial(get_single_table, url="/srm")

get_measurement = partial(get_single_table, url="/measurement")
get_standard_analysis = partial(get_single_table, url="/standard-analysis")
get_rcert = partial(get_single_table, url="/rcert")


def get_multiple_tables(
    client: Client,
    *,
    url: str,
    srm_id: int | MissingType = MISSING,
    batch_id: str | MissingType | None = MISSING,
    lot_id: str | MissingType | None = MISSING,
    srm_query: str
    | basemodels.srm.SRMQuery
    | Sequence[str | basemodels.srm.SRMQuery]
    | MissingType = MISSING,
    srm_table_id: str | UUID | Sequence[str | UUID] | MissingType = MISSING,
    subtable: SubTable | MissingType = MISSING,
    complete: bool = False,
) -> Response:
    if subtable is not MISSING:
        url = f"{url}/{subtable}"
    if complete:
        url = f"{url}/complete"

    params: dict[str, Any] = {}

    if srm_table_id is not MISSING:
        if isinstance(srm_table_id, str | UUID):
            srm_table_id = [srm_table_id]
        params["id"] = srm_table_id

    if srm_query is not MISSING:
        if isinstance(srm_query, str | basemodels.srm.SRMQuery):
            srm_query = [srm_query]
        params["srm_query"] = [
            q if isinstance(q, str) else q.model_dump_json(exclude_unset=True)
            for q in srm_query
        ]

    params.update(
        basemodels.srm.SRMQuery.from_params_exclude_missing(
            srm_id=srm_id, batch_id=batch_id, lot_id=lot_id
        ).model_dump(exclude_unset=True)
    )

    return client.get(url, params=params)


get_srms = partial(get_multiple_tables, url="/srms")

get_measurements = partial(get_multiple_tables, url="/measurements")
get_standard_analyses = partial(get_multiple_tables, url="/standard-analyses")
get_rcerts = partial(get_multiple_tables, url="/rcerts")


def upload_excel_file(
    client: Client,
    path_or_buffer: Path | BinaryIO,
    *,
    srm_id: int | MissingType = MISSING,
    batch_id: str | MissingType | None = MISSING,
    lot_id: str | MissingType | None = MISSING,
    srm_query: str
    | basemodels.srm.SRMCreate
    | basemodels.srm.SRMQuery
    | MissingType = MISSING,
    upload_name: str | MissingType = MISSING,
) -> Response:
    if srm_query is not MISSING:
        srm_query_str = (
            basemodels.srm.SRMCreate.from_srm_query(srm_query)
            if isinstance(srm_query, str)
            else srm_query
        ).model_dump_json(exclude_unset=True)
    else:
        srm_query_str = basemodels.srm.SRMQuery.from_params_exclude_missing(
            srm_id=srm_id, batch_id=batch_id, lot_id=lot_id
        ).model_dump_json(exclude_unset=True)

    func = partial(client.post, "/upload-excel", data={"srm_query": srm_query_str})
    mime_type = "application/vnd.ms-excel"

    if isinstance(path_or_buffer, Path):
        if upload_name is MISSING:
            upload_name = path_or_buffer.name

        with path_or_buffer.open("rb") as f:
            return func(files={"file": (upload_name, f, mime_type)})

    if upload_name is MISSING:
        msg = "must specify `upload_name` if passing buffer"
        raise ValueError(msg)

    return func(files={"file": (upload_name, path_or_buffer, mime_type)})


def download_excel_file(
    client: Client,
    path: Path | MissingType = MISSING,
    *,
    srm_id: int | MissingType = MISSING,
    batch_id: str | MissingType | None = MISSING,
    lot_id: str | MissingType | None = MISSING,
    srm_query: str | basemodels.srm.SRMQuery | MissingType = MISSING,
) -> Response:

    params = _get_srm_params(
        srm_query,
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
    )

    response = client.get("/download-excel", params=params)

    if path is not MISSING:
        with path.open("wb") as f:
            _ = f.write(response.content)

    return response


def delete_srm(
    client: Client,
    *,
    srm_id: int | MissingType = MISSING,
    batch_id: str | MissingType | None = MISSING,
    lot_id: str | MissingType | None = MISSING,
    srm_query: str | basemodels.srm.SRMQuery | MissingType = MISSING,
) -> Response:

    params = _get_srm_params(
        srm_query,
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
    )

    return client.delete("/srm", params=params)
