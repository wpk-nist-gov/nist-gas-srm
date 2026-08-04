from datetime import UTC, datetime

import pandas as pd
import streamlit as st

# pylint: disable=duplicate-code

st.title("📊 SRM data entry")

# Initialize an empty starting template
if "bulk_data" not in st.session_state:
    st.session_state.bulk_data = pd.DataFrame(
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
st.write("Modify cells, add new rows at the bottom, or delete rows:")

# Render editable spreadsheet layout
edited_df = st.data_editor(
    st.session_state.bulk_data,
    num_rows="fixed",  # Enables add/delete row buttons
    use_container_width=True,
    hide_index=True,
)

# Button to commit modifications
if st.button("Save Changes"):
    st.session_state.bulk_data = edited_df
    st.success("Changes permanently pushed to state!")
