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


def get_download_file_name(srm_query: str) -> str:
    return f"SRM{srm_query.upper()}.xlsx"


srm = st.selectbox(
    "SRM",
    get_all_srms(include_subtypes=False),
    accept_new_options=False,
)


if srm:
    st.download_button(
        label="Download excel file",
        data=download_file(srm).content,
        file_name=get_download_file_name(srm),
        mime="application/vnd.ms-excel",
    )
