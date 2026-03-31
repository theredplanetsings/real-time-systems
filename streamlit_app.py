import streamlit as st
from rt_utils import ALGORITHMS

st.set_page_config(
    page_title="Dashboard Home",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Real-Time Scheduling Dashboard")

st.markdown(
    """
This project collects real-time scheduling algorithms and visualisations in a
single, interactive scheduling dashboard. The dashboard lets you build custom task
sets, check schedulability tests, and generate schedules with hoverable job and
resource details. Schedules can be exported as PNG, and task sets as CSV.
"""
)

st.markdown(
    """
**How to run**

```bash
streamlit run streamlit_app.py
```
"""
)

st.subheader("Available Algorithms")
cols = st.columns(2)
for idx, name in enumerate(ALGORITHMS):
    cols[idx % 2].write(f"- {name}")

st.info("Use the pages list in the sidebar to navigate between algorithms.")