import streamlit as st
from rt_utils import ALGORITHMS, ALGORITHM_FAMILIES

st.set_page_config(
    page_title="Dashboard Home",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Real-Time Scheduling Dashboard")

family_count = len(ALGORITHM_FAMILIES)
variant_count = sum(len(meta.get("variants", {})) for meta in ALGORITHM_FAMILIES.values())
method_count = len(ALGORITHMS)
special_methods = [
    name
    for name in ALGORITHMS
    if name
    not in {
        "EDF",
        "EDD",
        "RM",
        "DM",
        "Global EDF",
        "Global RM",
        "Global DM",
        "Partitioned EDF",
        "Partitioned RM",
        "Partitioned DM",
    }
]

st.markdown(
    """
This dashboard groups the project’s real-time scheduling experiments into one
place. Build task sets, compare algorithms, inspect schedules, and export the
results as PNG or CSV.
"""
)

metrics = st.columns(3)
metrics[0].metric("Families", family_count)
metrics[1].metric("Variants", variant_count)
metrics[2].metric("Methods", method_count)

st.markdown(
    f"""
Core families: **{family_count}** across EDF, EDD, RM, and DM.

Specialized methods: **{len(special_methods)}** including cyclic
executive, time-demand analysis, priority inversion, and slack stealing.
"""
)

st.subheader("Quick Start")
quick_links = st.columns(4)
with quick_links[0]:
    st.page_link("pages/00_Algorithm_Explorer.py", label="Algorithm Explorer", icon="🧭")
with quick_links[1]:
    st.page_link("pages/02_Compare_Mode.py", label="Compare Mode", icon="⚖️")
with quick_links[2]:
    st.page_link("pages/06_Cyclic_Executive.py", label="Cyclic Executive", icon="🗓️")
with quick_links[3]:
    st.page_link("pages/16_Mixed_Workload_Analysis.py", label="Mixed Workload", icon="📋")

st.markdown(
    """
**How to run**

```bash
streamlit run streamlit_app.py
```
"""
)

st.subheader("Algorithms")

family_cards = st.columns(2)
for index, (family, meta) in enumerate(ALGORITHM_FAMILIES.items()):
    with family_cards[index % 2]:
        variants = ", ".join(meta.get("variants", {}).keys())
        st.markdown(f"**{family}**")
        st.caption(meta["label"])
        st.write(variants)

if special_methods:
    st.markdown("**Specialized analyses**")
    st.write(" · ".join(special_methods))

st.info(
    "Start with Algorithm Explorer in the sidebar for the main workflow, or use the"
    " specialized pages for cyclic executive, time demand, priority inversion, and slack stealing."
)