"""CLI program to interact with web-API"""
# ruff: file-ignore[commented-out-code]

from __future__ import annotations

import json
import logging
from enum import StrEnum, auto
from functools import partial
from typing import TYPE_CHECKING, Annotated

import httpx
import typer
from typer.core import TyperGroup

from nist_gas_srm import __version__
from nist_gas_srm.core.typing_compat import override

from . import crud

if TYPE_CHECKING:
    from typing import Any


FORMAT = "%(message)s [%(name)s - %(levelname)s]"
logging.basicConfig(level=logging.WARNING, format=FORMAT)
logger: logging.Logger = logging.getLogger("nist-gas-srm")

FASTAPI_URL = "http://127.0.0.1:8000"

_get_client = partial(httpx.Client, base_url=FASTAPI_URL)


def _callback_verbose(
    verbose: int | None,
) -> int | None:
    if verbose is None:
        return None

    if verbose < 0:  # pragma: no cover
        level = logging.ERROR
    elif not verbose:  # pragma: no cover
        level = logging.WARNING
    elif verbose == 1:
        level = logging.INFO
    else:  # pragma: no cover
        level = logging.DEBUG

    for logger_ in map(logging.getLogger, logging.root.manager.loggerDict):  # pylint: disable=no-member,bad-builtin
        logger_.setLevel(level)
    return verbose


def _callback_version(value: bool) -> None:
    """Versioning call back."""
    if value:
        typer.echo(f"pyproject2conda, version {__version__}")
        raise typer.Exit


def _get_json_string_from_response(
    response: httpx.Response, pretty: bool = False
) -> str:
    if pretty:
        return json.dumps(response.json(), indent=4)

    return response.text


# * Typer App --------------------------------------------------------------------------
class _AliasedGroup(TyperGroup):
    """Provide aliasing for commands"""

    @override
    def get_command(self, ctx: Any, cmd_name: str) -> Any | None:
        if (rv := super().get_command(ctx, cmd_name)) is not None:
            return rv
        if not (
            matches := [x for x in self.list_commands(ctx) if x.startswith(cmd_name)]
        ):
            return None
        if len(matches) == 1:
            return super().get_command(ctx, matches[0])
        ctx.fail(
            "Too many matches: {}".format(", ".join(sorted(matches)))
        )  # pragma: no cover
        return None  # pragma: no cover

    @override
    def list_commands(self, ctx: Any) -> list[str]:  # ruff: ignore[unused-method-argument]
        return list(self.commands)


app: typer.Typer = typer.Typer(cls=_AliasedGroup, no_args_is_help=True)

app_get = typer.Typer(help="Get", no_args_is_help=True)
app.add_typer(app_get, name="get")


@app.callback()
def main(
    version: Annotated[  # ruff: ignore[unused-function-argument]
        bool,
        typer.Option("--version", "-v", callback=_callback_version, is_eager=True),
    ] = False,
) -> None:
    """
    Interact with nist-gas-srm web-api from command line.
    """
    return


# * Parameters ----------------------------------------------------------------
class SubTable(StrEnum):
    MEASUREMENTS = auto()
    STANDARD_ANALYSIS = "standard-analysis"
    RCERT = auto()


SUBTABLE_OPTION = Annotated[
    SubTable | None,
    typer.Option(
        "--sub",
        help="""
        Select only subtable.
        """,
    ),
]
SRM_ID_OPTION = Annotated[
    int | None,
    typer.Option(
        "--srm-id",
        help="""
        SRM number ID.
        """,
    ),
]
BATCH_ID_OPTION = Annotated[
    str | None,
    typer.Option(
        "--batch",
        help="""
        Batch ID.
        """,
    ),
]
LOT_ID_OPTION = Annotated[
    str | None,
    typer.Option(
        "--lot",
        help="""
        Lot ID.
        """,
    ),
]

COMPLETE_OPTION = Annotated[
    bool,
    typer.Option(
        "--complete/--no-complete",
        help="""
        Whether to extract the complete json record.
        """,
    ),
]
PRETTY_OPTION = Annotated[
    bool,
    typer.Option(
        "--pretty/--no-pretty",
        help="""
        Pretty json output.
        """,
    ),
]
VERBOSE_OPTIONS = Annotated[
    int | None,
    typer.Option(
        "--verbose",
        "-v",
        help="Set verbosity level.  Can specify multiple times",
        count=True,
        callback=_callback_verbose,
    ),
]
ALL_OPTION = Annotated[
    bool,
    typer.Option(
        "--all/--no-all",
        help="Get all records",
    ),
]


SRM_QUERY_OPTIONAL_ARGUMENT = Annotated[
    str | None,
    typer.Argument(
        help="""
        srms to download.  Format is ``{srm_id}{batch_id}-{lot_id}``.
        """,
    ),
]
SRM_TABLE_ID_OPTION = Annotated[
    str | None,
    typer.Option(
        "--id",
        help="""
        Database id for the SRM.
        """,
    ),
]
SRM_QUERY_MULT_OPTIONAL_ARGUMENT = Annotated[
    list[str] | None,
    typer.Argument(
        help="""
        srms to download.  Format is ``{srm_id}{batch_id}-{lot_id}``.
        """,
    ),
]
SRM_TABLE_ID_MULT_OPTION = Annotated[
    list[str] | None,
    typer.Option(
        "--id",
        help="""
        Database id for the SRM.
        """,
    ),
]


def _get_dict_drop_drop_none(**kwargs: Any) -> dict[str, Any]:
    return {k: v for k, v in kwargs.items() if v is not None}


# def _get_single(
#     *,
#     srm_id: SRM_ID_OPTION = None,
#     batch_id: BATCH_ID_OPTION = None,
#     lot_id: LOT_ID_OPTION = None,
#     srm_query: SRM_QUERY_OPTIONAL_ARGUMENT = None,
#     srm_table_id: SRM_TABLE_ID_OPTION = None,
#     complete: COMPLETE_OPTION = False,
#     pretty: PRETTY_OPTION = False,
#     subtable: SUBTABLE_OPTION = None,
#     verbose: VERBOSE_OPTIONS = None,
#     url: str | None = "/srm",
# ) -> None:

#     params: dict[str, Any] = _get_dict_drop_drop_none(
#         srm_id=srm_id,
#         batch_id=batch_id,
#         lot_id=lot_id,
#         srm_query=srm_query,
#         srm_table_id=srm_table_id,
#         complete=complete,
#         subtable=subtable,
#         url=url,
#     )

#     logger.info("params %s", params)

#     with _get_client() as client:
#         response = crud.get_single_table(client=client, **params)

#         _ = response.raise_for_status()

#         typer.echo(_get_json_string_from_response(response, pretty=pretty))


# get_srm = app_get.command(
#     "srm",
#     no_args_is_help=True,
#     help="Get data for single SRM.",
# )(
#     partial(
#         _get_single,
#         url="/srm",
#     )
# )

# get_measurement = app_get.command(
#     "measurement",
#     no_args_is_help=True,
#     help="Get measurements data for single SRM",
# )(
#     partial(
#         _get_single,
#         url="/measurement",
#         subtable=None,
#     )
# )
# get_standard_analysis = app_get.command(
#     "standard-analysis",
#     no_args_is_help=True,
#     help="Get standard analysis data for single SRM",
# )(
#     partial(
#         _get_single,
#         url="/standard-analysis",
#         subtable=None,
#     )
# )
# get_rcert = app_get.command(
#     "rcert",
#     no_args_is_help=True,
#     help="Get R certification data for single SRM",
# )(
#     partial(
#         _get_single,
#         url="/rcert",
#         subtable=None,
#     )
# )


def _get_multiple(
    *,
    srm_id: SRM_ID_OPTION = None,
    batch_id: BATCH_ID_OPTION = None,
    lot_id: LOT_ID_OPTION = None,
    srm_query: SRM_QUERY_MULT_OPTIONAL_ARGUMENT = None,
    srm_table_id: SRM_TABLE_ID_MULT_OPTION = None,
    complete: COMPLETE_OPTION = False,
    pretty: PRETTY_OPTION = False,
    subtable: SUBTABLE_OPTION = None,
    verbose: VERBOSE_OPTIONS = None,  # ruff: ignore[unused-function-argument]
    url: str | None = "/srm",
    all_: ALL_OPTION = False,  # ruff: ignore[unused-function-argument]
) -> None:

    params: dict[str, Any] = _get_dict_drop_drop_none(
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
        srm_query=srm_query,
        srm_table_id=srm_table_id,
        complete=complete,
        subtable=subtable,
        url=url,
    )

    logger.info("params %s", params)

    with _get_client() as client:
        response = crud.get_multiple_tables(client=client, **params)

        _ = response.raise_for_status()

        typer.echo(_get_json_string_from_response(response, pretty=pretty))


get_srms = app_get.command(
    "srms",
    no_args_is_help=True,
    help="Get data for multiple SRMs",
)(
    partial(
        _get_multiple,
        url="/srms",
    )
)

get_measurements = app_get.command(
    "measurements",
    no_args_is_help=True,
    help="Get measurements data for multiple SRMs",
)(
    partial(
        _get_multiple,
        url="/measurements",
        subtable=None,
    )
)
get_standard_analyses = app_get.command(
    "standard-analyses",
    no_args_is_help=True,
    help="Get standard analysis data for multiple SRMs",
)(
    partial(
        _get_multiple,
        url="/standard-analyses",
        subtable=None,
    )
)
get_rcerts = app_get.command(
    "rcerts",
    no_args_is_help=True,
    help="Get R certification data for multiple SRMs",
)(
    partial(
        _get_multiple,
        url="/rcerts",
        subtable=None,
    )
)
