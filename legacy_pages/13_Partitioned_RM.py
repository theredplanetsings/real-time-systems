import streamlit as st
from st_helpers import render_algorithm_workbench

st.set_page_config(page_title="Legacy Partitioned RM", layout="wide")
st.title("Legacy Partitioned RM Page")
render_algorithm_workbench(
    initial_family="RM",
    initial_variant="Partitioned",
    lock_selection=True,
    show_retired_notice=True,
)