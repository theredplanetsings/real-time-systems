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

st.markdown(
    """
This project collects real-time scheduling algorithms and visualisations in a
single, interactive scheduling dashboard. The dashboard lets you build custom task
sets, check schedulability tests, and generate schedules with hoverable job and
resource details. Schedules can be exported as PNG, and task sets as CSV.
"""
)

st.subheader("What You Can Explore")
metrics = st.columns(3)
metrics[0].metric("Algorithm Families", family_count)
metrics[1].metric("Family Variants", variant_count)
metrics[2].metric("Total Methods", method_count)

st.markdown(
    f"""
The dashboard currently includes **{family_count} core scheduling families**
(EDF, EDD, RM, DM) with **{variant_count} selectable family variants** across
uniprocessor, global, and partitioned formulations.

In addition, the project contains **{method_count} total implemented methods**,
including advanced topics such as cyclic executive, time-demand analysis, and
priority inversion studies.
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

algorithm_lines = []
for family, meta in ALGORITHM_FAMILIES.items():
    variants = meta.get("variants", {})
    algorithm_lines.append(f"- **{family}**")
    for variant_name in variants:
        algorithm_lines.append(f"  - {variant_name}")

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

if special_methods:
    algorithm_lines.append("- **Specialized**")
    for name in special_methods:
        algorithm_lines.append(f"  - {name}")

st.markdown("\n".join(algorithm_lines))

st.info(
    "Use Algorithm Explorer in the sidebar to pick a family first, then pick a "
    "variant (Uniprocessor, Global, or Partitioned) and configure task parameters."
)