# pylint: disable=duplicate-code
from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID

import httpx

from nist_gas_srm import basemodels
from nist_gas_srm.core.missing import MISSING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any, BinaryIO

    from httpx import Client, Response

    from nist_gas_srm.core.missing import MissingType
    from nist_gas_srm.core.typing import SubTableType

FASTAPI_URL = "http://127.0.0.1:8000"

_get_client = partial(httpx.Client, base_url=FASTAPI_URL)


def _get_srm_params(
    srm_query: str | basemodels.srm.SRMQuery | MissingType,
    *,
    srm_number: int | MissingType = MISSING,
    batch: str | MissingType | None = MISSING,
    lot: str | MissingType | None = MISSING,
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
            srm_number=srm_number, batch=batch, lot=lot
        ).model_dump(exclude_unset=True)
    )

    if raise_if_empty and not params:
        msg = "No parameters to query"
        raise ValueError(msg)

    return params


def get_multiple_tables(
    client: Client | None = None,
    *,
    url: str,
    srm_number: int | MissingType = MISSING,
    batch: str | MissingType | None = MISSING,
    lot: str | MissingType | None = MISSING,
    srm_query: str
    | basemodels.srm.SRMQuery
    | Sequence[str | basemodels.srm.SRMQuery]
    | MissingType = MISSING,
    srm_table_id: str | UUID | Sequence[str | UUID] | MissingType = MISSING,
    subtable: SubTableType = None,
    complete: bool = False,
    one: bool = False,
) -> Response:

    if client is None:
        with _get_client() as client_:
            return get_multiple_tables(
                client=client_,
                url=url,
                srm_number=srm_number,
                batch=batch,
                lot=lot,
                srm_query=srm_query,
                srm_table_id=srm_table_id,
                subtable=subtable,
                complete=complete,
                one=one,
            )

    params: dict[str, Any] = {"one": one, "complete": complete}
    if subtable is not None:
        params.update(subtable=subtable)

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
            srm_number=srm_number, batch=batch, lot=lot
        ).model_dump(exclude_unset=True)
    )

    return client.get(url, params=params)


get_srms = partial(get_multiple_tables, url="/srms")


def download_excel_file(
    path: Path | MissingType = MISSING,
    client: Client | None = None,
    *,
    srm_number: int | MissingType = MISSING,
    batch: str | MissingType | None = MISSING,
    lot: str | MissingType | None = MISSING,
    srm_query: str | basemodels.srm.SRMQuery | MissingType = MISSING,
    srm_table_id: str | UUID | MissingType = MISSING,
) -> Response:
    if client is None:
        with _get_client() as client_:
            return download_excel_file(
                path=path,
                client=client_,
                srm_number=srm_number,
                batch=batch,
                lot=lot,
                srm_query=srm_query,
                srm_table_id=srm_table_id,
            )

    params = _get_srm_params(
        srm_query,
        srm_number=srm_number,
        batch=batch,
        lot=lot,
        srm_table_id=srm_table_id,
    )

    response = client.get("/srms/files", params=params)

    if path is not MISSING:
        with path.open("wb") as f:
            _ = f.write(response.content)

    return response


def upload_excel_file(
    path_or_buffer: Path | BinaryIO,
    client: Client | None = None,
    *,
    srm_number: int | MissingType = MISSING,
    batch: str | MissingType | None = MISSING,
    lot: str | MissingType | None = MISSING,
    srm_query: str
    | basemodels.srm.SRMCreate
    | basemodels.srm.SRMQuery
    | MissingType = MISSING,
    upload_name: str | MissingType = MISSING,
) -> Response:
    if client is None:
        with _get_client() as client_:
            return upload_excel_file(
                client=client_,
                path_or_buffer=path_or_buffer,
                srm_number=srm_number,
                batch=batch,
                lot=lot,
                srm_query=srm_query,
                upload_name=upload_name,
            )

    if srm_query is not MISSING:  # pylint: disable=consider-ternary-expression
        srm_query_str = (
            basemodels.srm.SRMCreate.from_srm_query(srm_query)
            if isinstance(srm_query, str)
            else srm_query
        ).model_dump_json(exclude_unset=True)
    else:
        srm_query_str = basemodels.srm.SRMQuery.from_params_exclude_missing(
            srm_number=srm_number, batch=batch, lot=lot
        ).model_dump_json(exclude_unset=True)

    func = partial(client.post, "/srms/files", data={"srm_query": srm_query_str})
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


def delete_srm(
    client: Client | None = None,
    *,
    srm_number: int | MissingType = MISSING,
    batch: str | MissingType | None = MISSING,
    lot: str | MissingType | None = MISSING,
    srm_query: str | basemodels.srm.SRMQuery | MissingType = MISSING,
    srm_table_id: str | UUID | MissingType = MISSING,
) -> Response:
    if client is None:
        with _get_client() as client_:
            return delete_srm(
                client=client_,
                srm_number=srm_number,
                batch=batch,
                lot=lot,
                srm_query=srm_query,
                srm_table_id=srm_table_id,
            )

    params = _get_srm_params(
        srm_query,
        srm_number=srm_number,
        batch=batch,
        lot=lot,
        srm_table_id=srm_table_id,
    )

    return client.delete("/srms", params=params)
