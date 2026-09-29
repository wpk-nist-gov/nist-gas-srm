import streamlit as st

home_page = st.Page("home.py", title="Gas SRM Analysis", icon="👋")

basic_entry_page = st.Page("basic_data_entry.py", title="Basic data entry")
table_entry_page = st.Page("basic_data_entry_table.py", title="Basic data entry table")
upload_page = st.Page("upload_excel_file.py", title="Upload from file")

view = st.Page("view.py", title="View measurements")

certified_page = st.Page("certified.py", title="Certified data")

download_excel = st.Page("download_excel_file.py", title="Download excel file")


pg = st.navigation([
    home_page,
    basic_entry_page,
    table_entry_page,
    upload_page,
    view,
    certified_page,
])  # ty: ignore[call-non-callable]
pg.run()
