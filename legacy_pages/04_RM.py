import streamlit as st
from st_helpers import render_algorithm_workbench

st.set_page_config(page_title="Legacy RM", layout="wide")
st.title("Legacy RM Page")
render_algorithm_workbench(
    initial_family="RM",
    initial_variant="Uniprocessor",
    lock_selection=True,
    show_retired_notice=True,
)