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
    {"title": "Seeded generation", "detail": "Reproducible randomized task creation with a fixed seed."},
    {"title": "Miss detail table", "detail": "Compare Mode now explains exactly which jobs missed."},
    {"title": "Scenario snapshots", "detail": "Save and reload named task-set states inside the builder."},
]

st.set_page_config(
    page_title="Dashboard Home",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
    color: #0f172a;
}

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at 12% 8%, rgba(255, 122, 89, 0.08), transparent 34%),
        radial-gradient(circle at 88% 18%, rgba(58, 124, 255, 0.09), transparent 36%),
        linear-gradient(180deg, #f8fafc 0%, #edf2f7 100%);
    color: #0f172a;
}

[data-testid="stAppViewContainer"] p,
[data-testid="stAppViewContainer"] li {
    color: #1f2937;
}

a {
    color: #1d4ed8;
}

a:hover {
    color: #0f3d91;
}

.hero {
    border: 1px solid rgba(15, 23, 42, 0.12);
    background: linear-gradient(130deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 255, 0.98));
    border-radius: 18px;
    padding: 1.2rem 1.3rem;
    margin-bottom: 1rem;
    box-shadow: 0 14px 32px rgba(15, 23, 42, 0.08);
}

.eyebrow {
    display: inline-block;
    padding: 0.2rem 0.55rem;
    border: 1px solid rgba(15, 23, 42, 0.14);
    border-radius: 999px;
    font-size: 0.73rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #0f3d91;
    background: rgba(255, 255, 255, 0.92);
    margin-bottom: 0.5rem;
    font-weight: 700;
}

.hero h1 {
    margin: 0;
    color: #0f172a;
    font-size: clamp(1.6rem, 2.8vw, 2.4rem);
    line-height: 1.12;
}

.hero p {
    margin-top: 0.55rem;
    color: #334155;
    font-size: 1rem;
}

.section-note {
    color: #334155;
    margin-top: -0.35rem;
    margin-bottom: 0.65rem;
}

.chip-row {
    margin-top: 0.25rem;
    margin-bottom: 0.65rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    color: #334155;
}

.chip {
    display: inline-block;
    border: 1px solid rgba(15, 23, 42, 0.14);
    border-radius: 999px;
    padding: 0.18rem 0.5rem;
    margin-right: 0.35rem;
    margin-bottom: 0.35rem;
    background: rgba(255, 255, 255, 0.96);
    color: #0f172a;
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);
}

.run-box {
    font-family: 'IBM Plex Mono', monospace;
    border: 1px solid rgba(15, 23, 42, 0.14);
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.96);
    color: #0f172a;
    padding: 0.65rem 0.75rem;
    box-shadow: 0 8px 20px rgba(15, 23, 42, 0.05);
}

.update-panel {
    border: 1px solid rgba(15, 23, 42, 0.14);
    border-radius: 14px;
    background: rgba(255, 255, 255, 0.96);
    padding: 0.85rem 0.95rem;
    box-shadow: 0 8px 20px rgba(15, 23, 42, 0.05);
}

.update-item {
    border-top: 1px solid rgba(15, 23, 42, 0.08);
    padding-top: 0.55rem;
    margin-top: 0.55rem;
}

.update-item:first-child {
    border-top: none;
    margin-top: 0;
    padding-top: 0;
}

.update-item-title {
    color: #0f172a;
    font-weight: 700;
    font-size: 0.96rem;
}

.update-item-detail {
    color: #475569;
    font-size: 0.88rem;
}

[data-testid="stCaptionContainer"] {
    color: #475569;
}

@media (max-width: 800px) {
    .hero {
        padding: 1rem;
    }
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="hero">
  <div class="eyebrow">Realtime Labs</div>
  <h1>Real-Time Scheduling Dashboard</h1>
  <p>Design task sets, stress-test schedulers, and inspect timing behavior with one unified control surface.</p>
</div>
""",
    unsafe_allow_html=True,
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
    '<div class="section-note">Core families span EDF, EDD, RM, and DM variants plus focused analysis modules.</div>',
    unsafe_allow_html=True,
)

def render_sparkline(values: list[float], key: str) -> None:
    fig = go.Figure(
        go.Scatter(
            y=values,
            mode="lines",
            line={"color": "#2c6ed6", "width": 2},
            fill="tozeroy",
            fillcolor="rgba(44, 110, 214, 0.14)",
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
        st.markdown(f'<div class="section-note">{section["note"]}</div>', unsafe_allow_html=True)
        section_columns = st.columns(int(section["columns"]))
        items = section["items"]
        for idx, item in enumerate(items):
            with section_columns[idx % int(section["columns"])]:
                st.caption(str(item["blurb"]))
                st.page_link(str(item["path"]), label=str(item["label"]), icon=str(item["icon"]))
                render_sparkline(item["trend"], key=f"spark_{section['title']}_{idx}")

with updates_col:
    st.subheader("Recent Updates")
    updates_html = ["<div class='update-panel'>"]
    for update in RECENT_UPDATES:
        updates_html.append(
            "<div class='update-item'>"
            f"<div class='update-item-title'>{update['title']}</div>"
            f"<div class='update-item-detail'>{update['detail']}</div>"
            "</div>"
        )
    updates_html.append("</div>")
    st.markdown("".join(updates_html), unsafe_allow_html=True)

st.subheader("Run Locally")
st.markdown('<div class="run-box">streamlit run streamlit_app.py</div>', unsafe_allow_html=True)

st.subheader("Algorithms")
st.markdown(
    '<div class="chip-row">'
    + "".join([f'<span class="chip">{name}</span>' for name in ["EDF", "EDD", "RM", "DM"]])
    + "</div>",
    unsafe_allow_html=True,
)

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