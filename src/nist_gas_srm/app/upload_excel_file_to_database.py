"""Data entry by upload excel file."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import streamlit as st

from nist_gas_srm.core import basemodels

if TYPE_CHECKING:
    from typing import Any

st.title("📋 Data upload portal")

# * Utils
FILENAME = Path(__file__).name


class EditableWidget:
    def __init__(
        self, label: str, widget_func: Any, default_value: Any = None, **kwargs: Any
    ) -> None:
        self.label = label
        self.keyname = f"_{FILENAME}_EDITABLETABLEKEY_{label}"
        self.widget_func = widget_func
        self.kwargs = kwargs

        if self.keyname not in st.session_state:
            self.update_key(default_value)

    def widget(self, **kwargs: Any) -> Any:
        kwargs = {**kwargs, **self.kwargs}
        return self.widget_func(self.label, **kwargs, key=self.keyname)

    def update_key(self, value: Any) -> None:
        st.session_state[self.keyname] = value


# * Basic entry ---------------------------------------------------------------
st.subheader("Enter SRM metadata")


editable_srm_widgets = {
    "srm_id": EditableWidget(
        "ID",
        st.number_input,
        min_value=1,
        max_value=10000000,
    ),
    "batch_id": EditableWidget("Batch", st.text_input, placeholder="a"),
    "lot_id": EditableWidget("Lot", st.text_input, placeholder="XXX"),
}

params = {k: v.widget() for k, v in editable_srm_widgets.items()}

params["name"] = st.text_input("Name", placeholder="A descriptive name", value=None)
params["note"] = st.text_input("Notes", placeholder="Notes", value=None)
params["units"] = st.text_input("Units", value="ppm")
params["timestamp"] = st.datetime_input("timestamp", value="now")

upload_file = st.file_uploader("Excel file to upload", type=".xls")

# * Update metadata from file -------------------------------------------------


def _get_metadata_from_filename() -> None:
    if upload_file is not None:
        from nist_gas_srm.core.excel_utils import parse_excel_filename_to_metadata

        values = parse_excel_filename_to_metadata(upload_file.name)
        values["srm_id"] = int(values["srm_id"])
        for k, v in values.items():
            editable_srm_widgets[k].update_key(v)


metadata_from_filename = st.button(
    "Parse filename for metadata", on_click=_get_metadata_from_filename
)

# * Submit to database --------------------------------------------------------
submit_to_database = st.button("Submit data")


def _submit_data_to_database() -> None:
    import httpx

    from nist_gas_srm.app._utils import FASTAPI_URL
    from nist_gas_srm.client import crud

    srm_query = basemodels.srm.SRMCreate.model_validate(params)

    with httpx.Client(base_url=FASTAPI_URL) as client:
        if upload_file is not None:
            response = crud.upload_excel_file(
                client=client,
                path_or_buffer=upload_file,
                srm_query=srm_query,
                upload_name=upload_file.name,
            )

            if not response.is_success:
                st.error(response.json()["detail"])
            else:
                st.info(f"Uploaded {srm_query.srm_string_id.upper()}")


if submit_to_database:
    _submit_data_to_database()
