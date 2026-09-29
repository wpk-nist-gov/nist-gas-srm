from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from nist_gas_srm.core import basemodels

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path
    from typing import Any

    from httpx import Client, Response


def _get_params_drop_none(**kwargs: Any) -> dict[str, Any]:
    return {k: v for k, v in kwargs.items() if v is not None}


def _validate_srm_query(
    srm_query: basemodels.srm.SRMQuery | str,
) -> basemodels.srm.SRMQuery:
    if isinstance(srm_query, str):
        return basemodels.srm.SRMQuery.from_string(srm_query)
    return srm_query


def _get_multiple(
    client: Client,
    *,
    url: str,
    srm_id: int | None = None,
    batch_id: str | None = None,
    lot_id: str | None = None,
    srm_query: Sequence[basemodels.srm.SRMQuery | str] | None = None,
    subtable: str | None = None,
    complete: bool = False,
) -> Response:
    if subtable is not None:
        url = f"{url}/{subtable}"
    if complete:
        url = f"{url}/complete"
    if srm_query is not None:
        srm_str_query = [
            _validate_srm_query(q).model_dump_json(exclude_unset=True)
            for q in srm_query
        ]
        return client.get(url, params={"srm": srm_str_query})

    params = _get_params_drop_none(srm_id=srm_id, batch_id=batch_id, lot_id=lot_id)
    return client.get(url, params=params)


get_srms = partial(_get_multiple, url="/srms")
get_measurements = partial(_get_multiple, url="/measurements")
get_standard_analyses = partial(_get_multiple, url="/standard-analyses")
get_rcerts = partial(_get_multiple, url="/rcerts")


def _get_single(
    client: Client,
    *,
    url: str,
    srm_id: int | None = None,
    batch_id: str | None = None,
    lot_id: str | None = None,
    srm_query: basemodels.srm.SRMQuery | str | None = None,
    complete: bool = False,
    subtable: str | None = None,
) -> Response:
    if subtable is not None:
        url = f"{url}/{subtable}"
    if complete:
        url = f"{url}/complete"
    if srm_query is not None:
        srm_str_query = _validate_srm_query(srm_query).model_dump_json(
            exclude_unset=True
        )
        return client.get(url, params={"srm": srm_str_query})

    params = _get_params_drop_none(srm_id=srm_id, batch_id=batch_id, lot_id=lot_id)
    return client.get(url, params=params)


get_srm = partial(_get_single, url="/srm")
get_measurements = partial(_get_single, url="/measurement")
get_standard_analysis = partial(_get_single, url="/standard-analysis")
get_rcerts = partial(_get_single, url="/rcert")


def upload_excel_file(
    client: Client,
    *,
    path: Path,
    srm_id: int | None = None,
    batch_id: str | None = None,
    lot_id: str | None = None,
    srm_query: basemodels.srm.SRMQuery | str | None = None,
) -> Response:
    if srm_query is not None:
        srm_str_query = _validate_srm_query(srm_query).model_dump_json(
            exclude_unset=True
        )
    else:
        srm_str_query = basemodels.srm.SRMQuery.from_params_exclude_none(
            srm_id=srm_id, batch_id=batch_id, lot_id=lot_id
        ).model_dump_json(exclude_unset=True)

    with path.open("rb") as f:
        files = {"uploadfile": (path.name, f, "application/vnd.ms-excel")}
        return client.post(
            "/upload-excel", data={"srm_query": srm_str_query}, files=files
        )
