"""Download excel file"""

from __future__ import annotations

import httpx
import streamlit as st

from nist_gas_srm.app._utils import (
    FASTAPI_URL,
    get_all_srms,
)
from nist_gas_srm.client import crud


def download_file(srm_query: str) -> httpx.Response:
    with httpx.Client(base_url=FASTAPI_URL) as client:
        return crud.download_excel_file(client, srm_query=srm_query)


def delete_srm_query(srm_query: str) -> httpx.Response:
    with httpx.Client(base_url=FASTAPI_URL) as client:
        return crud.delete_srm(client, srm_query=srm_query)


def get_download_file_name(srm_query: str) -> str:
    return f"SRM{srm_query.upper()}.xlsx"


if "delete_confirmed" not in st.session_state:
    st.session_state.delete_confirmed = False


if st.session_state.get("srm_list") is None:
    st.session_state.srm_list = get_all_srms(include_subtypes=False)


if "delete_info" not in st.session_state:
    st.session_state.delete_info = None

if "delete_error" not in st.session_state:
    st.session_state.delete_error = None


srm = st.selectbox(
    "SRM",
    st.session_state.srm_list,
)


@st.dialog("Confirm Action")
def confirm_modal() -> None:
    st.write(f"Are you sure you want to delete {srm}?")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes, Proceed"):
            st.session_state.delete_confirmed = True
            st.rerun()  # Rerun to immediately trigger the action below
    with col2:
        if st.button("Cancel"):
            st.rerun()  # Closes the modal without setting the flag


if srm:
    st.download_button(
        label="Download excel file",
        data=download_file(srm).content,
        file_name=get_download_file_name(srm),
        mime="application/vnd.ms-excel",
    )

    if st.button("delete file"):
        confirm_modal()

    if st.session_state.delete_confirmed:
        response = delete_srm_query(srm)

        if not response.is_success:
            st.session_state.delete_error = response.json()["detail"]
            st.session_state.delete_info = None
        else:
            st.session_state.delete_error = None
            st.session_state.delete_info = response.json()["message"]

        st.session_state.delete_confirmed = False
        st.session_state.srm_list = None
        st.rerun()


if st.session_state.delete_error:
    st.error(st.session_state.delete_error)
if st.session_state.delete_info:
    st.info(st.session_state.delete_info)
