"""
Task 3.1 — Comprehensive Dashboard
National Electricity Grid Network Analysis

Run locally with:
    streamlit run app.py

This file is intended to sit as a sibling folder to data-science/, e.g.
    <repo root>/dashboard/app.py
so that "../master_grid_dataset.csv" reaches the repo root. Adjust
MASTER_PATH below if your team places it elsewhere.

Tab ownership (fill in as teammates finish their pieces):
    Overview     - all members / whoever owns app.py structure (DONE, basic version)
    Network      - Task 2.1, network metrics + N-1 contingency (DONE - see build_graph_and_metrics)
    Geography    - Task 2.2, Louange (DONE - see build_folium_map)
    Reliability  - Task 2.3, Idi (DONE - see build_reliability_tab)
    Search       - substation finder / utility comparison (DONE)

Note: Task 3.2 (advanced/publication-quality visualizations) is a
SEPARATE task from this dashboard, owned by Jolene. Not built here.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

import plotly.graph_objects as go
import networkx as nx
from networkx.algorithms import community
import folium
from folium.plugins import HeatMap
import streamlit.components.v1 as components

# ---------------------------------------------------------------------------
# Page config (must be the first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="National Grid Analysis Dashboard",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
# Two possible data layouts are supported, tried in this order:
#
#   1. Direct clean CSVs (preferred): substations_clean.csv, lines_clean.csv,
#      utilities_clean.csv - the Task 1.1 output. This is simpler and doesn't
#      lose any rows, unlike option 2 below.
#   2. master_grid_dataset.csv fallback: a LINES-CENTRIC merged table (one
#      row per line, with source/destination substation details merged in
#      as *_Source/*_Dest columns, utility details as *_Utility columns).
#      Reconstructing substations/utilities from this only recovers rows
#      that appear on at least one line - a substation or utility with zero
#      lines would be silently dropped. Prefer option 1 when both exist.
#
# EDIT THESE if your folder layout differs. Both assume dashboard/app.py
# sits as a sibling folder to wherever the CSVs actually live.
CLEAN_DIR = "../data-science/"       # for substations_clean.csv etc.
MASTER_PATH = "../master_grid_dataset.csv"  # fallback


@st.cache_data
def load_data():
    """
    Tries the direct clean CSVs first, falls back to reconstructing from
    master_grid_dataset.csv if those aren't found.
    """
    try:
        substations = pd.read_csv(f"{CLEAN_DIR}substations_clean.csv")
        lines = pd.read_csv(f"{CLEAN_DIR}lines_clean.csv")
        utilities = pd.read_csv(f"{CLEAN_DIR}utilities_clean.csv")
        return substations, lines, utilities
    except FileNotFoundError:
        pass  # fall through to master file reconstruction below

    master = pd.read_csv(MASTER_PATH)

    def extract_side(df: pd.DataFrame, id_col: str, suffix: str) -> pd.DataFrame:
        # Exclude the redundant "Substation ID_Source"/"Substation ID_Dest" column
        # if present - it duplicates the same info as id_col and would otherwise
        # produce two columns both named "Substation ID" after stripping the suffix.
        redundant_id_col = f"Substation ID{suffix}"
        cols = [c for c in df.columns if c.endswith(suffix) and c != redundant_id_col]
        side = df[[id_col] + cols].copy()
        side = side.rename(columns={id_col: "Substation ID"})
        side.columns = ["Substation ID"] + [c[: -len(suffix)] for c in cols]
        return side

    source_side = extract_side(master, "Source Substation ID", "_Source")
    dest_side = extract_side(master, "Destination Substation ID", "_Dest")
    substations = (
        pd.concat([source_side, dest_side], ignore_index=True)
        .drop_duplicates(subset="Substation ID")
        .reset_index(drop=True)
    )

    line_cols = [
        "Line ID", "Utility ID", "Source Substation ID", "Source Substation",
        "Destination Substation ID", "Destination Substation", "Voltage (kV)",
        "Length (km)", "Capacity (MVA)", "Status", "Line Type",
    ]
    lines = master[[c for c in line_cols if c in master.columns]].drop_duplicates().reset_index(drop=True)

    util_cols = [c for c in master.columns if c.endswith("_Utility") and c != "Utility ID_Utility"]
    utilities = (
        master[["Utility ID"] + util_cols]
        .drop_duplicates(subset="Utility ID")
        .reset_index(drop=True)
    )
    utilities.columns = ["Utility ID"] + [c[: -len("_Utility")] for c in util_cols]

    return substations, lines, utilities


try:
    substations, lines, utilities = load_data()
    DATA_LOADED = True
except FileNotFoundError as e:
    DATA_LOADED = False
    LOAD_ERROR = str(e)


# ---------------------------------------------------------------------------
# Tab layout
# ---------------------------------------------------------------------------
st.title("National Electricity Grid Analysis")
st.caption("Ghana and West African regional interconnections")

if not DATA_LOADED:
    st.error(
        f"Could not find the data files. Check DATA_DIR at the top of app.py.\n\n{LOAD_ERROR}"
    )
    st.stop()

tab_overview, tab_network, tab_geo, tab_reliability, tab_search = st.tabs(
    ["Overview", "Network", "Geography", "Reliability", "Search"]
)


# ---------------------------------------------------------------------------
# Overview tab (stub - fill in later)
# ---------------------------------------------------------------------------
with tab_overview:
    st.header("Overview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Substations", len(substations))
    col2.metric("Transmission lines", len(lines))
    col3.metric("Utilities", len(utilities))
    col4.metric("Regions", substations["Region"].nunique())
    st.info("TODO: executive summary, key findings, headline chart. Owner TBC.")


# ---------------------------------------------------------------------------
# Network tab (Task 2.1 - network metrics + N-1 contingency, WORKING)
# ---------------------------------------------------------------------------
@st.cache_data
def build_graph_and_metrics(substations: pd.DataFrame, lines: pd.DataFrame):
    """
    Ports the Task 2.1 script (graph build + centrality + community
    detection + N-1 contingency) into a cached function so it only runs
    once per data load instead of on every Streamlit rerun.
    Returns the graph plus three dataframes: centrality, community
    summary, and N-1 results, along with a small dict of headline stats.
    """
    G = nx.Graph()
    for _, row in substations.iterrows():
        G.add_node(
            row["Substation ID"],
            name=row["Name"],
            region=row["Region"],
            voltage=row["Voltage (kV)"],
            lat=row["Latitude"],
            lon=row["Longitude"],
        )
    for _, row in lines.iterrows():
        G.add_edge(
            row["Source Substation ID"],
            row["Destination Substation ID"],
            length=row["Length (km)"],
            capacity=row["Capacity (MVA)"],
        )

    degree_centrality = nx.degree_centrality(G)
    betweenness_centrality = nx.betweenness_centrality(G)
    closeness_centrality = nx.closeness_centrality(G)
    pagerank = nx.pagerank(G)

    centrality_df = pd.DataFrame({
        "Substation ID": list(G.nodes()),
        "Name": [G.nodes[n]["name"] for n in G.nodes()],
        "Region": [G.nodes[n]["region"] for n in G.nodes()],
        "Degree Centrality": [degree_centrality[n] for n in G.nodes()],
        "Betweenness Centrality": [betweenness_centrality[n] for n in G.nodes()],
        "Closeness Centrality": [closeness_centrality[n] for n in G.nodes()],
        "PageRank": [pagerank[n] for n in G.nodes()],
    }).sort_values("Betweenness Centrality", ascending=False)

    is_connected = nx.is_connected(G)
    if is_connected:
        diameter = nx.diameter(G)
        avg_path_length = nx.average_shortest_path_length(G)
    else:
        largest_cc = max(nx.connected_components(G), key=len)
        subgraph_conn = G.subgraph(largest_cc)
        diameter = nx.diameter(subgraph_conn)
        avg_path_length = nx.average_shortest_path_length(subgraph_conn)

    avg_clustering = nx.average_clustering(G)

    largest_cc = max(nx.connected_components(G), key=len)
    subgraph = G.subgraph(largest_cc)
    communities = community.greedy_modularity_communities(subgraph)

    community_rows = []
    for i, comm in enumerate(communities):
        regions_in_community = sorted(set(G.nodes[n]["region"] for n in comm))
        community_rows.append({
            "Community": i + 1,
            "Substations": len(comm),
            "Regions represented": ", ".join(regions_in_community),
        })
    community_df = pd.DataFrame(community_rows)

    # N-1 contingency on the top 5 most critical substations
    top_critical = centrality_df.head(5)
    n1_rows = []
    for _, row in top_critical.iterrows():
        sub_id = row["Substation ID"]
        G_test = G.copy()
        G_test.remove_node(sub_id)

        components_before = nx.number_connected_components(G)
        components_after = nx.number_connected_components(G_test)
        largest_before = len(max(nx.connected_components(G), key=len))
        largest_after = len(max(nx.connected_components(G_test), key=len)) if G_test.number_of_nodes() else 0

        n1_rows.append({
            "Substation": row["Name"],
            "Components Before": components_before,
            "Components After": components_after,
            "New Splits Caused": components_after - components_before,
            "Substations Cut Off": largest_before - largest_after,
        })
    n1_df = pd.DataFrame(n1_rows)

    stats = {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "diameter": diameter,
        "avg_path_length": avg_path_length,
        "avg_clustering": avg_clustering,
        "is_connected": is_connected,
        "num_components": nx.number_connected_components(G),
        "num_communities": len(communities),
    }

    return G, centrality_df, community_df, n1_df, stats


def build_network_plot(G: nx.Graph, centrality_df: pd.DataFrame) -> go.Figure:
    """
    Interactive Plotly version of the Task 2.1 matplotlib network plot.
    Node size still reflects betweenness centrality; positions use each
    substation's actual lon/lat so the layout roughly mirrors the map.
    """
    centrality_lookup = centrality_df.set_index("Substation ID")["Betweenness Centrality"].to_dict()
    pos = {n: (G.nodes[n]["lon"], G.nodes[n]["lat"]) for n in G.nodes()}

    edge_x, edge_y = [], []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(width=0.7, color="#cccccc"), hoverinfo="none",
    )

    node_x, node_y, node_text, node_size = [], [], [], []
    for n in G.nodes():
        x, y = pos[n]
        node_x.append(x)
        node_y.append(y)
        bc = centrality_lookup.get(n, 0)
        node_text.append(f"{G.nodes[n]['name']}<br>Region: {G.nodes[n]['region']}<br>Betweenness: {bc:.3f}")
        node_size.append(bc * 3000 + 8)

    node_trace = go.Scatter(
        x=node_x, y=node_y, mode="markers", hoverinfo="text", text=node_text,
        marker=dict(size=node_size, color="#4A90D9", line=dict(width=0.5, color="white")),
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        margin=dict(l=0, r=0, t=0, b=0),
        height=550,
    )
    return fig


with tab_network:
    st.header("Network")

    G, centrality_df, community_df, n1_df, stats = build_graph_and_metrics(substations, lines)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Nodes / edges", f"{stats['nodes']} / {stats['edges']}")
    col2.metric("Avg shortest path", f"{stats['avg_path_length']:.2f}")
    col3.metric("Avg clustering coeff.", f"{stats['avg_clustering']:.3f}")
    col4.metric("Connected components", stats["num_components"])

    if not stats["is_connected"]:
        st.warning(
            f"The network is **not** fully connected "
            f"({stats['num_components']} separate components). "
            "Diameter and average path length are computed on the largest component only."
        )

    st.divider()

    st.subheader("Network graph")
    st.caption("Node size reflects betweenness centrality — larger nodes are more critical bridge points")
    st.plotly_chart(build_network_plot(G, centrality_df), use_container_width=True)

    st.subheader("Top 10 most critical substations")
    st.caption("Ranked by betweenness centrality — substations that connect otherwise separate parts of the network")
    st.dataframe(
        centrality_df.head(10)[
            ["Name", "Region", "Betweenness Centrality", "Degree Centrality", "PageRank"]
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader(f"Community structure ({stats['num_communities']} communities detected)")
    st.dataframe(community_df, use_container_width=True, hide_index=True)

    st.divider()

    st.subheader("N-1 contingency analysis")
    st.caption(
        "Simulates removing each of the top 5 most critical substations one at a time "
        "and measures the impact on network connectivity. This is a structural/graph-based "
        "approximation, not a power-flow study."
    )
    st.dataframe(n1_df, use_container_width=True, hide_index=True)

    with st.expander("How to read the N-1 results"):
        st.markdown(
            """
            - **New Splits Caused**: how many additional disconnected pieces
              the network breaks into after removing this substation. `0`
              means the network stayed in one piece without it.
            - **Substations Cut Off**: how many substations became
              unreachable from the main network as a result.
            - These numbers reflect *structural* redundancy only — they do
              not account for electrical load, voltage stability, or
              protection behaviour.
            """
        )


# ---------------------------------------------------------------------------
# Geography tab (Task 2.2 - geospatial analysis, WORKING)
# ---------------------------------------------------------------------------
@st.cache_resource
def build_folium_map(substations: pd.DataFrame, lines: pd.DataFrame) -> folium.Map:
    """
    Ports the Task 2.2 script's folium map build. Cached with
    cache_resource (not cache_data) since folium.Map objects aren't
    naturally serializable the way dataframes are.
    """
    sub_by_id = substations.set_index("Substation ID")

    center_lat = substations["Latitude"].mean()
    center_lon = substations["Longitude"].mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=7, tiles="CartoDB positron")

    voltage_colors = {11: "green", 33: "blue", 69: "orange", 161: "red", 330: "darkred"}

    sub_layer = folium.FeatureGroup(name="Substations (by voltage)")
    for _, s in substations.iterrows():
        color = voltage_colors.get(s["Voltage (kV)"], "gray")
        folium.CircleMarker(
            location=[s["Latitude"], s["Longitude"]],
            radius=5 + (s["Capacity (MVA)"] / 100),
            color=color, fill=True, fill_color=color, fill_opacity=0.75,
            popup=folium.Popup(
                f"<b>{s['Name']}</b><br>"
                f"Region: {s['Region']}<br>"
                f"Voltage: {s['Voltage (kV)']} kV<br>"
                f"Capacity: {s['Capacity (MVA)']} MVA<br>"
                f"Status: {s['Status']}",
                max_width=250,
            ),
        ).add_to(sub_layer)
    sub_layer.add_to(m)

    utility_colors = {1: "#1f77b4", 2: "#ff7f0e", 3: "#2ca02c", 4: "#d62728",
                       5: "#9467bd", 6: "#8c564b", 7: "#e377c2", 9: "#7f7f7f"}
    lines_layer = folium.FeatureGroup(name="Transmission/Distribution Lines")
    for _, ln in lines.iterrows():
        if ln["Source Substation ID"] not in sub_by_id.index or ln["Destination Substation ID"] not in sub_by_id.index:
            continue
        src = sub_by_id.loc[ln["Source Substation ID"]]
        dst = sub_by_id.loc[ln["Destination Substation ID"]]
        color = utility_colors.get(ln["Utility ID"], "black")
        folium.PolyLine(
            locations=[[src["Latitude"], src["Longitude"]], [dst["Latitude"], dst["Longitude"]]],
            color=color,
            weight=2 + ln["Voltage (kV)"] / 165,
            opacity=0.6,
            popup=f"{ln['Source Substation']} \u2192 {ln['Destination Substation']}<br>"
                  f"{ln['Length (km)']} km, {ln['Voltage (kV)']} kV",
        ).add_to(lines_layer)
    lines_layer.add_to(m)

    heat_layer = folium.FeatureGroup(name="Substation Density Heatmap", show=False)
    HeatMap(substations[["Latitude", "Longitude"]].values.tolist(), radius=25).add_to(heat_layer)
    heat_layer.add_to(m)

    # Cross-border connections, if a Country column with border-ish values exists
    if "Country" in substations.columns:
        border_layer = folium.FeatureGroup(name="Cross-border Connections")
        border_countries = {
            "Cote d'Ivoire", "Cote d'Ivoire border", "Togo", "Togo border",
            "Benin", "Burkina Faso", "Burkina Faso border", "Guinea",
        }
        for _, ln in lines.iterrows():
            if ln["Source Substation ID"] not in sub_by_id.index or ln["Destination Substation ID"] not in sub_by_id.index:
                continue
            src = sub_by_id.loc[ln["Source Substation ID"]]
            dst = sub_by_id.loc[ln["Destination Substation ID"]]
            if src.get("Country") in border_countries or dst.get("Country") in border_countries:
                folium.PolyLine(
                    locations=[[src["Latitude"], src["Longitude"]], [dst["Latitude"], dst["Longitude"]]],
                    color="gold", weight=4, opacity=0.9,
                    popup=f"Cross-border: {ln['Source Substation']} \u2192 {ln['Destination Substation']}",
                ).add_to(border_layer)
        border_layer.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m


with tab_geo:
    st.header("Geography")
    st.caption("Layers: substations by voltage, lines by utility, density heatmap, cross-border links")

    region_counts = substations["Region"].value_counts()
    sparse_regions = region_counts[region_counts <= 1]

    col1, col2 = st.columns(2)
    col1.metric("Regions covered", substations["Region"].nunique())
    col2.metric("Regions with \u22641 substation (coverage gap)", len(sparse_regions))
    if len(sparse_regions) > 0:
        st.warning(f"Possible coverage gaps in: {', '.join(sparse_regions.index)}")

    fmap = build_folium_map(substations, lines)
    components.html(fmap._repr_html_(), height=600, scrolling=False)

    st.subheader("Substation count by region")
    st.bar_chart(region_counts)

    st.subheader("Line length distribution")
    fig_dist = px.histogram(lines, x="Length (km)", nbins=15)
    fig_dist.update_layout(xaxis_title="Line length (km)", yaxis_title="Number of lines")
    st.plotly_chart(fig_dist, use_container_width=True)


# ---------------------------------------------------------------------------
# Reliability tab (Task 2.3 - Idi, WORKING)
# ---------------------------------------------------------------------------
def build_reliability_tab(substations: pd.DataFrame, lines: pd.DataFrame, utilities: pd.DataFrame):
    """
    Reliability / Business Intelligence tab.
    Ports the Task 2.3 analysis from task2_3.ipynb into interactive Plotly
    charts. Replace the placeholder logic in each section below with your
    actual notebook code - the structure (filters -> charts -> findings)
    is ready to receive it.
    """
    st.header("Reliability & business intelligence")

    # --- Filters -----------------------------------------------------
    regions = ["All"] + sorted(substations["Region"].dropna().unique().tolist())
    selected_region = st.selectbox("Filter by region", regions, key="reliability_region")

    if selected_region != "All":
        sub_view = substations[substations["Region"] == selected_region]
    else:
        sub_view = substations

    # --- Key metrics row ----------------------------------------------
    col1, col2, col3 = st.columns(3)
    col1.metric("Substations in view", len(sub_view))
    col2.metric("Total capacity (MVA)", f"{sub_view['Capacity (MVA)'].sum():,.0f}")

    lines_maint = lines[lines["Status"] == "Under Maintenance"]
    pct_maint = (len(lines_maint) / len(lines) * 100) if len(lines) else 0
    col3.metric("Lines under maintenance", f"{pct_maint:.1f}%")

    st.divider()

    # --- Chart 1: Utility footprint (replace with your Task 2.3 logic) --
    # TODO: swap in your actual "GRIDCo dominates 43.6% of lines" analysis
    st.subheader("Utility footprint by line count")
    if "Utility ID" in lines.columns and not utilities.empty:
        line_counts = (
            lines.merge(utilities, on="Utility ID", how="left")
            .groupby("Name")
            .size()
            .reset_index(name="Line count")
            .sort_values("Line count", ascending=False)
        )
        fig1 = px.bar(
            line_counts,
            x="Name",
            y="Line count",
            title=None,
        )
        fig1.update_layout(xaxis_title="Utility", yaxis_title="Number of lines")
        st.plotly_chart(fig1, use_container_width=True)

    # --- Chart 2: Capacity concentration (top substations) --------------
    # TODO: swap in your "top 10 substations hold 53.5% of total capacity" finding
    st.subheader("Capacity concentration")
    top_n = st.slider("Show top N substations by capacity", 5, 20, 10, key="reliability_topn")
    top_capacity = substations.nlargest(top_n, "Capacity (MVA)")[["Name", "Capacity (MVA)", "Region"]]
    fig2 = px.bar(
        top_capacity.sort_values("Capacity (MVA)"),
        x="Capacity (MVA)",
        y="Name",
        color="Region",
        orientation="h",
    )
    st.plotly_chart(fig2, use_container_width=True)

    # --- Chart 3: Substation strain (capacity per connected line) --------
    st.subheader("Substation strain (MVA per connected line)")
    st.caption("Lower values indicate a substation's capacity is spread thin across many connections \u2014 a proxy for upgrade priority")

    line_counts_per_sub = pd.concat([
        lines["Source Substation ID"], lines["Destination Substation ID"]
    ]).value_counts().rename_axis("Substation ID").reset_index(name="Connected Lines")

    strain_df = substations.merge(line_counts_per_sub, on="Substation ID", how="inner")
    strain_df["MVA per Line"] = strain_df["Capacity (MVA)"] / strain_df["Connected Lines"]
    strain_df = strain_df.sort_values("MVA per Line").head(10)

    fig_strain = px.bar(
        strain_df.sort_values("MVA per Line", ascending=False),
        x="MVA per Line",
        y="Name",
        color="Region",
        orientation="h",
        hover_data=["Capacity (MVA)", "Connected Lines"],
    )
    st.plotly_chart(fig_strain, use_container_width=True)

    # --- Chart 4: Asset age profile --------------------------------------
    if "Commissioning Year" in sub_view.columns:
        st.subheader("Substation age distribution")
        fig4 = px.histogram(
            sub_view,
            x="Commissioning Year",
            nbins=20,
            color="Type" if "Type" in sub_view.columns else None,
        )
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info(
            "Commissioning Year isn't available in the current dataset, "
            "so the asset-age chart is skipped."
        )

    # --- Chart 5: Highest loss-risk lines ---------------------------------
    st.subheader("Highest loss-risk lines")
    st.caption("Loss Proxy = Length (km) \u00f7 Voltage (kV) \u2014 longer lines at lower voltage carry higher resistive-loss risk")

    loss_df = lines.copy()
    loss_df["Loss Proxy"] = loss_df["Length (km)"] / loss_df["Voltage (kV)"]
    loss_df = loss_df.sort_values("Loss Proxy", ascending=False).head(10)
    loss_df["Line"] = loss_df["Source Substation"] + " \u2192 " + loss_df["Destination Substation"]

    fig_loss = px.bar(
        loss_df.sort_values("Loss Proxy"),
        x="Loss Proxy",
        y="Line",
        orientation="h",
        hover_data=["Length (km)", "Voltage (kV)"],
    )
    st.plotly_chart(fig_loss, use_container_width=True)

    st.divider()

    # --- Written findings (from Task 2.3 output, verified) ----------------
    with st.expander("Key findings", expanded=True):
        st.markdown(
            """
            - **Dominant utility:** GRIDCo operates 24 of 55 lines (43.6% of the network)
            - **Most strained substation:** Achimota Substation, at 1.6 MVA of capacity
              per connected line
            - **Highest loss-risk line:** Hohoe Substation \u2192 Sogakope Substation
              (loss proxy score: 13.86)
            - **Most underserved region:** Upper West \u2014 just 1 substation,
              27.1 MVA of total capacity
            - **Oldest substation:** Aboadze Substation, commissioned 59 years ago
            - **Capacity concentration risk:** the top 10 substations by capacity
              hold 53.5% of total network capacity
            """
        )


with tab_reliability:
    build_reliability_tab(substations, lines, utilities)


# ---------------------------------------------------------------------------
# Search tab (substation finder + utility comparison, WORKING)
# ---------------------------------------------------------------------------
with tab_search:
    st.header("Search")

    search_mode = st.radio(
        "Search mode", ["Substation finder", "Utility comparison"],
        horizontal=True, key="search_mode",
    )

    if search_mode == "Substation finder":
        col1, col2, col3 = st.columns(3)
        name_query = col1.text_input("Search by name")
        region_filter = col2.multiselect(
            "Filter by region", sorted(substations["Region"].dropna().unique().tolist())
        )
        voltage_filter = col3.multiselect(
            "Filter by voltage (kV)", sorted(substations["Voltage (kV)"].dropna().unique().tolist())
        )

        results = substations.copy()
        if name_query:
            results = results[results["Name"].str.contains(name_query, case=False, na=False)]
        if region_filter:
            results = results[results["Region"].isin(region_filter)]
        if voltage_filter:
            results = results[results["Voltage (kV)"].isin(voltage_filter)]

        st.caption(f"{len(results)} of {len(substations)} substations match")
        st.dataframe(
            results[["Name", "Region", "Country", "Voltage (kV)", "Capacity (MVA)", "Type", "Status"]]
            .sort_values("Name"),
            use_container_width=True,
            hide_index=True,
        )

        if len(results) == 1:
            sub = results.iloc[0]
            sub_id = sub["Substation ID"]
            connected = lines[
                (lines["Source Substation ID"] == sub_id) | (lines["Destination Substation ID"] == sub_id)
            ]
            st.subheader(f"Lines connected to {sub['Name']}")
            if len(connected) > 0:
                st.dataframe(
                    connected[["Source Substation", "Destination Substation", "Voltage (kV)",
                               "Length (km)", "Capacity (MVA)", "Status"]],
                    use_container_width=True, hide_index=True,
                )
            else:
                st.info("No lines found for this substation in the current dataset.")

    else:  # Utility comparison
        util_names = sorted(utilities["Name"].dropna().unique().tolist())
        selected_utils = st.multiselect(
            "Select utilities to compare", util_names, default=util_names[: min(3, len(util_names))]
        )

        if selected_utils:
            comparison_rows = []
            for util_name in selected_utils:
                util_row = utilities[utilities["Name"] == util_name].iloc[0]
                util_id = util_row["Utility ID"]
                util_lines = lines[lines["Utility ID"] == util_id]

                comparison_rows.append({
                    "Utility": util_name,
                    "Type": util_row.get("Type", "\u2013"),
                    "Country": util_row.get("Country", "\u2013"),
                    "Lines operated": len(util_lines),
                    "Total line length (km)": round(util_lines["Length (km)"].sum(), 1),
                    "Total capacity (MVA)": round(util_lines["Capacity (MVA)"].sum(), 1),
                })

            comparison_df = pd.DataFrame(comparison_rows)
            st.dataframe(comparison_df, use_container_width=True, hide_index=True)

            fig_compare = px.bar(
                comparison_df, x="Utility", y="Lines operated", color="Utility",
            )
            st.plotly_chart(fig_compare, use_container_width=True)
        else:
            st.info("Select at least one utility above to compare.")
