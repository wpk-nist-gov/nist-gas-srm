import pandas as pd
import streamlit as st

st.title("📊 Grid-Based Bulk Data Entry")

# Initialize an empty starting template
if "bulk_data" not in st.session_state:
    st.session_state.bulk_data = pd.DataFrame([
        {"Item": "Laptop", "Price": 1200, "In Stock": True},
        {"Item": "Mouse", "Price": 25, "In Stock": True},
    ])

st.write("Modify cells, add new rows at the bottom, or delete rows:")

# Render editable spreadsheet layout
edited_df = st.data_editor(
    st.session_state.bulk_data,
    num_rows="dynamic",  # Enables add/delete row buttons
    use_container_width=True,
)

# Button to commit modifications
if st.button("Save Changes"):
    st.session_state.bulk_data = edited_df
    st.success("Changes permanently pushed to state!")
