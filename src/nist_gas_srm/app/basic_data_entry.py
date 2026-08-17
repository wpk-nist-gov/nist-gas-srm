"""Basic Data entry of metadata, etc"""

import pandas as pd
import streamlit as st

from nist_gas_srm._models import SRMDataCreate

# ruff: disable[commented-out-code]
# using streamlit-pydantic
# srm_data = sp.pydantic_form(key="Sample form", model=SRMDataCreate)

# if srm_data:
#     st.json(srm_data.model_dump())
# ruff: enable[commented-out-code]

st.title("SRM data entry")

if "data_log" not in st.session_state:
    st.session_state.data_log = {}

if "srm_data" not in st.session_state:
    st.session_state.srm_data = None


with st.form("entry_form", clear_on_submit=False):
    st.subheader("Enter SRM metadata")

    PARAMS = {
        "name": st.text_input("Name", placeholder="A descriptive name"),
        "srm_id": st.number_input(
            "ID", placeholder="2627", min_value=0, max_value=10000000
        ),
        "batch_id": st.text_input("Batch", placeholder="a"),
        "lot_id": st.text_input("Lot", placeholder="XXX"),
        "timestamp": st.datetime_input("timestamp"),
    }

    # form submit
    submitted = st.form_submit_button("Save Entry")


# # Display
if submitted:
    st.session_state.srm_data = SRMDataCreate.model_validate({
        short_name: value for short_name, value in PARAMS.items() if value
    })


st.write("### Submitted metadata")
if (srm_data := st.session_state.srm_data) is not None:
    st.dataframe(pd.DataFrame([srm_data.model_dump()]), use_container_width=True)
