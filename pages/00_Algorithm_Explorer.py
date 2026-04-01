import streamlit as st
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
	sys.path.insert(0, str(ROOT_DIR))

from st_helpers import render_algorithm_workbench

st.set_page_config(page_title="Algorithm Explorer", layout="wide")
st.title("Algorithm Explorer")
st.caption("Choose a base family first, then select a derivative variant.")

render_algorithm_workbench()