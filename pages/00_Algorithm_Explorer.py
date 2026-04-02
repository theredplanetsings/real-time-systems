import streamlit as st

from st_helpers import render_algorithm_workbench

st.set_page_config(page_title="Algorithm Explorer", layout="wide")
st.title("Algorithm Explorer")
st.caption("Choose a base family first, then select a derivative variant.")

render_algorithm_workbench()