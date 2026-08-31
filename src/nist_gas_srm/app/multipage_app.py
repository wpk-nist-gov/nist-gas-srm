import streamlit as st

home_page = st.Page("home.py", title="Gas SRM Analysis", icon="👋")

basic_entry_page = st.Page("basic_data_entry.py", title="Basic data entry")
table_entry_page = st.Page("basic_data_entry_table.py", title="Basic data entry table")
upload_page = st.Page("upload_excel_file.py", title="Upload from file")

certified_page = st.Page("certified.py", title="Certified data")

pg = st.navigation([
    home_page,
    basic_entry_page,
    table_entry_page,
    upload_page,
    certified_page,
])
pg.run()
