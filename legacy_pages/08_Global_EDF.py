import streamlit as st
from st_helpers import render_algorithm_workbench

st.set_page_config(page_title="Legacy Global EDF", layout="wide")
st.title("Legacy Global EDF Page")
render_algorithm_workbench(
    initial_family="EDF",
    initial_variant="Global",
    lock_selection=True,
    show_retired_notice=True,
)