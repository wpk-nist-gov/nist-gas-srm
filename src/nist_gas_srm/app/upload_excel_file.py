"""Data entry by upload excel file."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, cast, override

import pandas as pd
import streamlit as st

from nist_gas_srm.core import basemodels, excel_interface

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import Any

st.title("📋 Data upload portal")

# * Utils
FILENAME = Path(__file__).name


class EditableTableBase:
    def __init__(self, keyname_base: str) -> None:
        self.keyname = f"_{FILENAME}_EDITABLETABLEKEY_{keyname_base}"
        self.table: pd.DataFrame | None = None
        if self.keyname not in st.session_state:
            self.update_key()

    def editable_table_widget(self, obj: Any, **kwargs: Any) -> pd.DataFrame | None:
        self.table = st.data_editor(
            obj,
            **kwargs,
            key=self.key,
        )
        return self.table

    @property
    def key(self) -> str:
        return cast("str", st.session_state[self.keyname])

    def update_key(self) -> None:
        st.session_state[self.keyname] = str(uuid.uuid4())


class EditableTableSRM(EditableTableBase):
    """
    Class to handle Editable Table with updates.

    This allows for refreshing the data after edits.
    See https://discuss.streamlit.io/t/how-to-refresh-datasets-in-st-data-editor/66710
    """

    def __init__(self, attr: str, name: str) -> None:
        self.attr = attr
        self.name = name
        super().__init__(keyname_base=attr)

    @override
    def editable_table_widget(
        self, obj: pd.ExcelFile, **kwargs: Any
    ) -> pd.DataFrame | None:
        return super().editable_table_widget(
            excel_interface.excel_to_dataframe_by_name(
                self.attr, excelfile, model=basemodels.SRMRCertCreateComplete
            ),
            **kwargs,
        )

    def refresh_table_widget(self) -> bool:
        return st.button(
            "Refresh table", on_click=self.update_key, key=f"{self.keyname}_button"
        )


def refresh_tables(tables: Iterable[EditableTableSRM]) -> None:
    for table in tables:
        table.update_key()


# * Initialize an empty starting template -------------------------------------
DBNAMES_TABLENAMES_MAPPING = {
    "ratios": "Ratio data",
    "vendors": "Vendor data",
    "standards": "Standards",
    "ratio_analysis_random_effects": "Ratio analysis",
    "ratio_analysis_fixed_effects": "Ratio analysis fixed effects",
    "past_lot_standards": "Past lot standards",
    "additional_lot_standards": "Additional lot standards",
    # certifiede values
    "rcert.srm_values": "SRM values",
    "rcert.standards_values": "Standards values",
    "rcert.additional_lot_standards": "Certified additional lot standards",
    "rcert.cylinder_results": "Cylinder results",
    "rcert.analysis_function_coefficients": "Analysis function coefficients",
    "rcert.correlation_coefficients": "Correlation coefficients",
    "rcert.outliers": "Outliers",
}

TABLES = [
    EditableTableSRM(attr=attr, name=name)
    for attr, name in DBNAMES_TABLENAMES_MAPPING.items()
]


if "srm_file" not in st.session_state:
    st.session_state.srm_file = None

if "srm_metadata" not in st.session_state:
    st.session_state.srm_metadata = pd.DataFrame(
        [
            {
                "name": "a name",
                "srm_id": 1,
                "batch_id": "X",
                "lot_id": "X",
                "timestamp": datetime.now(UTC),
            }
        ],
    )


# * Input widgets -------------------------------------------------------------
upload_file = st.file_uploader("Excel file to upload", type=".xls")


metadata_table = EditableTableBase(keyname_base="metadata")
edited_df = metadata_table.editable_table_widget(
    st.session_state.srm_metadata,
    num_rows="fixed",  # Enables add/delete row buttons
    width="stretch",
    hide_index=True,
)

if upload_file is not None:
    st.session_state.srm_file = pd.ExcelFile(upload_file)


def _get_metadata_from_filename() -> None:
    if upload_file is not None:
        from nist_gas_srm.core.utils import parse_excel_filename_to_metadata

        new = pd.DataFrame([parse_excel_filename_to_metadata(upload_file.name)]).astype({
            "srm_id": int
        })
        st.session_state.srm_metadata.update(new)
        metadata_table.update_key()


metadata_from_filename = st.button(
    "Parse filename for metadata", on_click=_get_metadata_from_filename
)
submit_to_database = st.button("Submit data")
refersh_tables = st.button(
    "Refresh all tables", on_click=partial(refresh_tables, TABLES)
)

if st.session_state.srm_file is not None:
    excelfile = st.session_state.srm_file

    tabs = st.tabs([table.name for table in TABLES])

    for tab, table in zip(tabs, TABLES, strict=True):
        with tab:
            table.refresh_table_widget()
            table.editable_table_widget(
                excelfile,
                num_rows="dynamic",
                width="stretch",
                hide_index=True,
                placeholder="-",
            )

    if submit_to_database:
        st.info("uploaded data")
        # ruff: disable[commented-out-code]
        # out = TABLES[0].table
        # out.to_csv("tmp.csv")
        # ruff: enable[commented-out-code]
