from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from nist_gas_srm.core import basemodels

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path
    from typing import Any

    from httpx import Client, Response


def _get_srm_params(
    srm_query: str | basemodels.srm.SRMQuery | None,
    *,
    srm_id: int | None = None,
    batch_id: str | None = None,
    lot_id: str | None = None,
) -> dict[str, Any]:
    if srm_query is not None:
        return {
            "srm_query": basemodels.srm.SRMQuery.from_srm_query(
                srm_query
            ).model_dump_json(exclude_unset=True)
        }
    return basemodels.srm.SRMQuery.from_params_exclude_none(
        srm_id=srm_id, batch_id=batch_id, lot_id=lot_id
    ).model_dump(exclude_unset=True)


def _get_multiple(
    client: Client,
    *,
    url: str,
    srm_id: int | None = None,
    batch_id: str | None = None,
    lot_id: str | None = None,
    srm_query: Sequence[str | basemodels.srm.SRMQuery] | None = None,
    subtable: str | None = None,
    complete: bool = False,
) -> Response:
    if subtable is not None:
        url = f"{url}/{subtable}"
    if complete:
        url = f"{url}/complete"
    if srm_query is not None:
        srm_query_str = [
            basemodels.srm.SRMQuery.from_srm_query(q).model_dump_json(
                exclude_unset=True
            )
            for q in srm_query
        ]
        return client.get(url, params={"srm_query": srm_query_str})

    params = basemodels.srm.SRMQuery.from_params_exclude_none(
        srm_id=srm_id, batch_id=batch_id, lot_id=lot_id
    ).model_dump(exclude_unset=True)
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
    srm_query: str | basemodels.srm.SRMQuery | None = None,
    complete: bool = False,
    subtable: str | None = None,
) -> Response:
    if subtable is not None:
        url = f"{url}/{subtable}"
    if complete:
        url = f"{url}/complete"

    params = _get_srm_params(srm_query, srm_id=srm_id, batch_id=batch_id, lot_id=lot_id)
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
    srm_query: str | basemodels.srm.SRMCreate | basemodels.srm.SRMQuery | None = None,
) -> Response:
    if srm_query is not None:
        srm_query_str = (
            basemodels.srm.SRMCreate.from_srm_query(srm_query)
            if isinstance(srm_query, str)
            else srm_query
        ).model_dump_json(exclude_unset=True)
    else:
        srm_query_str = basemodels.srm.SRMQuery.from_params_exclude_none(
            srm_id=srm_id, batch_id=batch_id, lot_id=lot_id
        ).model_dump_json(exclude_unset=True)

    with path.open("rb") as f:
        files = {"file": (path.name, f, "application/vnd.ms-excel")}
        return client.post(
            "/upload-excel", data={"srm_query": srm_query_str}, files=files
        )


def download_excel_file(
    client: Client,
    *,
    path: Path,
    srm_id: int | None = None,
    batch_id: str | None = None,
    lot_id: str | None = None,
    srm_query: str | basemodels.srm.SRMQuery | None = None,
) -> None:

    params = _get_srm_params(srm_query, srm_id=srm_id, batch_id=batch_id, lot_id=lot_id)

    response = client.get("/download-excel", params=params)

    with path.open("wb") as f:
        _ = f.write(response.content)
