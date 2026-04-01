import streamlit as st
from st_helpers import render_algorithm_workbench

st.set_page_config(page_title="Legacy Partitioned DM", layout="wide")
st.title("Legacy Partitioned DM Page")
render_algorithm_workbench(
    initial_family="DM",
    initial_variant="Partitioned",
    lock_selection=True,
    show_retired_notice=True,
)