import streamlit as st
import plotly.graph_objects as go
from rt_utils import ALGORITHMS, ALGORITHM_FAMILIES

NAV_SECTIONS = [
    {
        "title": "Quick Start",
        "note": "Use these first when exploring a new workload.",
        "columns": 3,
        "items": [
            {
                "label": "Task Set Builder",
                "icon": "🧱",
                "path": "pages/01_Task_Set_Builder.py",
                "blurb": "Author or import task sets and export quickly.",
                "trend": [0.25, 0.32, 0.38, 0.47, 0.6, 0.72],
            },
            {
                "label": "Algorithm Explorer",
                "icon": "🧭",
                "path": "pages/00_Algorithm_Explorer.py",
                "blurb": "Tune scheduler options and inspect timelines.",
                "trend": [0.18, 0.25, 0.28, 0.41, 0.55, 0.66],
            },
            {
                "label": "Compare Mode",
                "icon": "⚖️",
                "path": "pages/02_Compare_Mode.py",
                "blurb": "Run side-by-side algorithm comparisons.",
                "trend": [0.1, 0.18, 0.29, 0.34, 0.44, 0.58],
            },
        ],
    },
    {
        "title": "Specialized Analysis",
        "note": "Go deeper on cyclic schedules, demand checks, slack reclamation, and mixed workloads.",
        "columns": 2,
        "items": [
            {
                "label": "Cyclic Executive",
                "icon": "🗓️",
                "path": "pages/06_Cyclic_Executive.py",
                "blurb": "Frame-size checks and schedule synthesis.",
                "trend": [0.15, 0.2, 0.26, 0.31, 0.37, 0.42],
            },
            {
                "label": "Time Demand",
                "icon": "📈",
                "path": "pages/10_Time_Demand.py",
                "blurb": "Demand curve feasibility analysis.",
                "trend": [0.08, 0.17, 0.23, 0.28, 0.36, 0.49],
            },
            {
                "label": "Slack Stealing",
                "icon": "🌙",
                "path": "pages/15_Slack_Stealing.py",
                "blurb": "Reclaim idle time for aperiodic jobs.",
                "trend": [0.04, 0.1, 0.16, 0.26, 0.34, 0.53],
            },
            {
                "label": "Mixed Workload",
                "icon": "📋",
                "path": "pages/16_Mixed_Workload_Analysis.py",
                "blurb": "Baseline EDF versus slack-stealing behavior.",
                "trend": [0.06, 0.13, 0.19, 0.3, 0.45, 0.63],
            },
        ],
    },
]

RECENT_UPDATES = [
    {"title": "Task presets", "detail": "One-click starter task sets in the builder."},
    {"title": "JSON import/export", "detail": "Task sets now move cleanly across tools and runs."},
    {
        "title": "Seeded generation",
        "detail": "Reproducible randomized task creation with a fixed seed.",
    },
    {
        "title": "Miss detail table",
        "detail": "Compare Mode now explains exactly which jobs missed.",
    },
    {
        "title": "Scenario snapshots",
        "detail": "Save and reload named task-set states inside the builder.",
    },
]

st.set_page_config(
    page_title="Dashboard Home",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Real-Time Scheduling Dashboard")
st.caption(
    "Design task sets, stress-test schedulers, and inspect timing behavior with one unified control surface."
)

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

metrics = st.columns(3)
metrics[0].metric("Families", family_count)
metrics[1].metric("Variants", variant_count)
metrics[2].metric("Methods", method_count)

st.markdown(
    "Core families span EDF, EDD, RM, and DM variants plus focused analysis modules.",
)


def render_sparkline(values: list[float], key: str) -> None:
    fig = go.Figure(
        go.Scatter(
            y=values,
            mode="lines",
            line={"color": "#385b82", "width": 2},
            fill="tozeroy",
            fillcolor="rgba(56, 91, 130, 0.13)",
            hoverinfo="skip",
        )
    )
    fig.update_layout(
        height=80,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis={"visible": False},
        yaxis={"visible": False},
    )
    st.plotly_chart(fig, use_container_width=True, key=key)


nav_col, updates_col = st.columns([2.2, 1])

with nav_col:
    for section in NAV_SECTIONS:
        st.subheader(str(section["title"]))
        st.caption(str(section["note"]))
        section_columns = st.columns(int(section["columns"]))
        items = section["items"]
        for idx, item in enumerate(items):
            with section_columns[idx % int(section["columns"])]:
                st.caption(str(item["blurb"]))
                st.page_link(str(item["path"]), label=str(item["label"]), icon=str(item["icon"]))
                render_sparkline(item["trend"], key=f"spark_{section['title']}_{idx}")

with updates_col:
    st.subheader("Recent Updates")
    for update in RECENT_UPDATES:
        st.markdown(f"**{update['title']}**")
        st.caption(str(update["detail"]))

st.subheader("Run Locally")
st.code("streamlit run streamlit_app.py", language="bash")

st.subheader("Algorithms")
st.caption("EDF · EDD · RM · DM")

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

st.success("Recommended flow: Task Set Builder -> Algorithm Explorer -> Compare Mode.")
