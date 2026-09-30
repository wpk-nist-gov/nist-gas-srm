# ruff:file-ignore[commented-out-code]


import streamlit as st

home_page = st.Page("home.py", title="Gas SRM Analysis", icon="👋")

basic_entry_page = st.Page("basic_data_entry.py", title="Basic data entry")
table_entry_page = st.Page("basic_data_entry_table.py", title="Basic data entry table")
inspect_excel_file_page = st.Page("inspect_excel_file.py", title="Inspect excel file")
upload_excel_file = st.Page("upload_excel_file_to_database.py", title="Upload file")

view = st.Page("view.py", title="View data")

certified_page = st.Page("certified.py", title="Certified data")

download_excel_file = st.Page("download_excel_file.py", title="Download excel file")


pg = st.navigation([
    home_page,
    basic_entry_page,
    table_entry_page,
    inspect_excel_file_page,
    upload_excel_file,
    download_excel_file,
    view,
    certified_page,
])  # ty: ignore[call-non-callable]
pg.run()


# st.html("""
#     <style>
#         .stAppHeader {
#             background-color: #1E3A8A; /* Dark blue background */
#         }
#     </style>
# """)


# with st.bottom:
#     st.markdown("---")
#     st.caption("Developed with ❤️ | © 2026 My Streamlit App")


# def local_css(path: Path) -> None:
#     # with path.open(encoding="utf-8") as f:
#     if not path.exists():
#         msg = f"csss {path} does not exist"
#         raise ValueError(msg)
#     s = f"<style>{path.read_text(encoding='utf-8')}</style>"
#     # st.write(s)
#     st.html(s)
#     #st.markdown(s, unsafe_allow_html=True)

# def local_js(path: Path) -> None:
#     if not path.exists():
#         msg = f"path {path} does not exist"
#         raise ValueError(msg)
#     s = dedent(f"""\
#     <script>
#     {path.read_text(encoding='utf-8')}
#     </script>
#     """)
#     from streamlit.components.v1 import html
#     html(s) #, unsafe_allow_javascript=True)


# def local_html(path: Path) -> None:
#     if not path.exists():
#         msg = f"path {path} does not exist"
#         raise ValueError(msg)
#     st.html(path.read_text(encoding="utf-8"))


# local_css(Path(__file__).parent / "_static/css/nist-combined.css")
# local_js(Path(__file__).parent / "_static/js/nist-header-footer.js")
# local_html(Path(__file__).parent/ "_static/html/boilerplate-header.html")
# local_html(Path(__file__).parent / "_static/html/boilerplate-footer.html")

# hide_footer_style = """
#     <style>
#     #MainMenu {visibility: hidden;}
#     footer {visibility: hidden;}

#     .custom-footer {
#         position: fixed;
#         left: 0;
#         bottom: 0;
#         width: 100%;
#         background-color: #f8f9fa;
#         color: #6c757d;
#         text-align: center;
#         padding: 10px;
#         font-size: 14px;
#         z-index: 100;
#     }
#     </style>
#     <div class="custom-footer">
#         <p>Developed with ❤️ by <a href="https://example.com" target="_blank">Your Name</a></p>
#     </div>
# """

# st.markdown(hide_footer_style, unsafe_allow_html=True)

# from streamlit.components.v1 import html

# # Define your javascript
# my_js = """
# alert("Hola mundo");
# """

# # Wrapt the javascript as html code
# my_html = f"<script>{my_js}</script>"

# # Execute your app
# st.title("Javascript example")
# html(my_html)
