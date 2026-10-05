from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from nist_gas_srm.core import basemodels
from nist_gas_srm.core.missing import MISSING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any, BinaryIO
    from uuid import UUID

    from httpx import Client, Response

    from nist_gas_srm.core.missing import MissingType


def _get_srm_params(
    srm_query: str | basemodels.srm.SRMQuery | MissingType,
    *,
    srm_id: int | MissingType = MISSING,
    batch_id: str | MissingType | None = MISSING,
    lot_id: str | MissingType | None = MISSING,
    srm_query_regex: str | MissingType = MISSING,
    srm_table_id: str | UUID | MissingType = MISSING,
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

    if srm_query_regex is not MISSING:
        params["query_regex"] = srm_query_regex

    params.update(
        basemodels.srm.SRMQuery.from_params_exclude_missing(
            srm_id=srm_id, batch_id=batch_id, lot_id=lot_id
        ).model_dump(exclude_unset=True)
    )

    return params


def _get_multiple(
    client: Client,
    *,
    url: str,
    srm_id: int | MissingType = MISSING,
    batch_id: str | MissingType | None = MISSING,
    lot_id: str | MissingType | None = MISSING,
    srm_query: Sequence[str | basemodels.srm.SRMQuery] | MissingType = MISSING,
    srm_query_regex: Sequence[str] | MissingType = MISSING,
    srm_table_id: Sequence[str | UUID] | MissingType = MISSING,
    subtable: str | MissingType = MISSING,
    complete: bool = False,
) -> Response:
    if subtable is not MISSING:
        url = f"{url}/{subtable}"
    if complete:
        url = f"{url}/complete"

    params: dict[str, Any] = {}

    if srm_table_id is not MISSING:
        params["id"] = srm_table_id

    if srm_query is not MISSING:
        params["srm_query"] = [
            q if isinstance(q, str) else q.model_dump_json(exclude_unset=True)
            for q in srm_query
        ]

    if srm_query_regex is not MISSING:
        params["query_regex"] = srm_query_regex

    params.update(
        basemodels.srm.SRMQuery.from_params_exclude_missing(
            srm_id=srm_id, batch_id=batch_id, lot_id=lot_id
        ).model_dump(exclude_unset=True)
    )

    return client.get(url, params=params)


get_srms = partial(_get_multiple, url="/srms")
get_measurements = partial(_get_multiple, url="/measurements")
get_standard_analyses = partial(_get_multiple, url="/standard-analyses")
get_rcerts = partial(_get_multiple, url="/rcerts")


def _get_single(
    client: Client,
    *,
    url: str,
    srm_id: int | MissingType = MISSING,
    batch_id: str | MissingType | None = MISSING,
    lot_id: str | MissingType | None = MISSING,
    srm_query: str | basemodels.srm.SRMQuery | MissingType = MISSING,
    srm_table_id: str | UUID | MissingType = MISSING,
    complete: bool = False,
    subtable: str | MissingType = MISSING,
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
    )
    return client.get(url, params=params)


get_srm = partial(_get_single, url="/srm")
get_measurements = partial(_get_single, url="/measurement")
get_standard_analysis = partial(_get_single, url="/standard-analysis")
get_rcerts = partial(_get_single, url="/rcert")


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
    srm_query_regex: str | MissingType = MISSING,
) -> Response:

    params = _get_srm_params(
        srm_query,
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
        srm_query_regex=srm_query_regex,
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
    srm_query_regex: str | MissingType = MISSING,
) -> Response:

    params = _get_srm_params(
        srm_query,
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
        srm_query_regex=srm_query_regex,
    )

    return client.delete("/srm", params=params)
