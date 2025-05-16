import streamlit as st
import pandas as pd
import numpy as np
import networkx as nx
from pyvis.network import Network
import matplotlib.pyplot as plt
from community import community_louvain
from streamlit_option_menu import option_menu
import streamlit.components.v1 as components
from google.cloud import bigquery

# ---- CONFIGURATION DE LA PAGE ----
st.set_page_config(page_title="Avisia GA4 Navigator", page_icon="🧠", layout="wide")

# ---- BIGQUERY CONFIG ----
PROJECT_ID = "avisia-training"
DATASET_ID = "avisia_graph_theory_analytics"
TABLE_NODES = "avisia_ga4_nodes"
TABLE_EDGES = "avisia_ga4_edges"

# ---- CSS DE LA PAGE D'ACCUEIL ----
landing_css = """
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(145deg, #f3f6fa 0%, #eaf0f8 100%);
}
.centered {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 90vh;
    text-align: center;
}
.centered h1 {
    font-size: 3.4rem;
    font-weight: 800;
    margin-bottom: 1rem;
    color: #005493;
}
.centered p {
    font-size: 1.3rem;
    color: #4a5568;
    margin-bottom: 2rem;
}
div.stButton > button {
    background-color: #005493;
    color: white;
    padding: 0.8rem 2rem;
    font-size: 1.1rem;
    border-radius: 40px;
    border: none;
    transition: all 0.3s ease;
}
div.stButton > button:hover {
    background-color: #003b6f;
    transform: scale(1.05);
    color: #ffffff;
}
</style>
"""

# ---- ÉTAT SESSION POUR LA LANDING PAGE ----
if 'page_started' not in st.session_state:
    st.session_state.page_started = False

# ---- AFFICHAGE LANDING ----
if not st.session_state.page_started:
    st.markdown(landing_css, unsafe_allow_html=True)
    st.image("logo_avisia.png", width=130)
    st.markdown("""
    <div class="centered">
        <h1>Bienvenue chez Avisia</h1>
        <p>Visualisez et analysez vos parcours GA4 avec style et précision.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚀 Get Started"):
        st.session_state.page_started = True
        st.rerun()
    st.stop()

# ---- SIDEBAR ----
with st.sidebar:
    st.image("logo_avisia.png", width=180)
    selected = option_menu(
        menu_title="Menu",
        options=["Accueil", "Graph Analyse", "Contact"],
        icons=["house", "graph-up", "envelope"],
        menu_icon="cast",
        default_index=0,
    )
    dark_mode = st.toggle("🌗 Mode sombre")

# ---- THEME ----
if dark_mode:
    st.markdown("""
    <style>
    body { background-color: #1e1e1e; color: #e2e2e2; }
    .kpi-card { background: #333; color: #f1f1f1; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    .hero-section {
        padding: 2rem;
        background: linear-gradient(90deg, #5e72e4, #825ee4);
        color: white;
        border-radius: 16px;
        margin-bottom: 2rem;
    }
    .kpi-grid {
        display: flex;
        gap: 1.5rem;
        flex-wrap: wrap;
        margin-bottom: 2rem;
    }
    .kpi-card {
        flex: 1;
        min-width: 220px;
        background: linear-gradient(135deg, #5e72e4 0%, #825ee4 100%);
        border-radius: 16px;
        color: white;
        padding: 1rem 1.5rem;
        box-shadow: 0 8px 20px rgba(0,0,0,0.1);
        transition: transform 0.2s ease;
    }
    .kpi-card:hover { transform: translateY(-4px); }
    .kpi-title { font-size: 0.95rem; opacity: 0.85; }
    .kpi-value { font-size: 1.5rem; font-weight: bold; margin-top: 0.3rem; }
    </style>
    """, unsafe_allow_html=True)

# ---- CHARGEMENT DES DONNÉES DEPUIS BIGQUERY ----
@st.cache_data
def load_edges_data_from_bigquery():
    client = bigquery.Client(project=PROJECT_ID)
    query = f"SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_EDGES}`"
    return client.query(query).to_dataframe()

@st.cache_data
def load_nodes_data_from_bigquery():
    client = bigquery.Client(project=PROJECT_ID)
    query = f"SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_NODES}`"
    return client.query(query).to_dataframe()

# ---- CRÉATION DU GRAPH ----
def create_graph():
    df = load_edges_data_from_bigquery()
    dt = load_nodes_data_from_bigquery()
    df['from_page'] = df['from_page'].astype(str).apply(lambda x: 'productsheet_page' if '/productsheet/' in x else x)
    df['to_page'] = df['to_page'].astype(str).apply(lambda x: 'productsheet_page' if '/productsheet/' in x else x)
    dt['page_location'] = dt['page_location'].astype(str).apply(lambda x: 'productsheet_page' if '/productsheet/' in x else x)
    G = nx.DiGraph()
    for _, row in df.iterrows():
        G.add_edge(row['from_page'], row['to_page'], transition_count=row['transition_count'])
    for _, row in dt.iterrows():
        G.add_node(row['page_location'], page_view_count=row['pageview_count'])
    return G

def create_pyvis_graph(G):
    net = Network(height="700px", width="100%", directed=True, select_menu=True, filter_menu=True, cdn_resources='remote')
    net.force_atlas_2based(gravity=-6000, central_gravity=0.005, spring_length=900, damping=0.9)
    net.toggle_physics(True)
    net.show_buttons(filter_=['physics'])
    net.from_nx(G)
    return net.generate_html()

def calculate_kpis(G):
    kpis = {}
    degree = nx.degree_centrality(G)
    pagerank = nx.pagerank(G, alpha=st.sidebar.slider("PageRank Alpha", 0.05, 0.95, 0.85, 0.05))
    betweenness = nx.betweenness_centrality(G)
    components = list(nx.weakly_connected_components(G))
    kpis['top_degree'] = sorted(degree, key=degree.get, reverse=True)[:5]
    kpis['top_pagerank'] = sorted(pagerank, key=pagerank.get, reverse=True)[:5]
    kpis['top_betweenness'] = sorted(betweenness, key=betweenness.get, reverse=True)[:5]
    kpis['orphaned_count'] = len([c for c in components if len(c) <= 10])
    source = st.sidebar.text_input("Source", value=list(G.nodes)[0])
    target = st.sidebar.text_input("Target", value=list(G.nodes)[1])
    try:
        kpis['shortest_path'] = nx.shortest_path(G, source=source, target=target)
    except:
        kpis['shortest_path'] = "Pas de chemin trouvé."
    partition = community_louvain.best_partition(G.to_undirected())
    colors = {c: np.random.rand(3,) for c in set(partition.values())}
    node_colors = [colors[partition[n]] for n in G.nodes()]
    pos = nx.spring_layout(G, seed=42)
    plt.figure(figsize=(12, 8))
    nx.draw(G, pos, node_color=node_colors, with_labels=True, edge_color='gray', node_size=600, font_size=9)
    plt.title("Détection de communautés (Louvain)")
    kpis['community_plot'] = plt
    return kpis

# ---- ROUTING ----
if selected == "Accueil":
    st.markdown("""
        <div class="hero-section">
            <h1>Let's Ride the Future.</h1>
            <p>Une interface élégante pour explorer la navigation GA4, powered by Avisia.</p>
        </div>
    """, unsafe_allow_html=True)

elif selected == "Graph Analyse":
    st.title("📊 Analyse Graphique")
    G = create_graph()
    html = create_pyvis_graph(G)
    components.html(html, height=720, scrolling=True)

    kpis = calculate_kpis(G)
    st.markdown("<div class='kpi-grid'>", unsafe_allow_html=True)
    for label, values in {
        "Top Pages (Degré)": kpis['top_degree'],
        "Pages Influentes (PageRank)": kpis['top_pagerank'],
        "Bottlenecks (Betweenness)": kpis['top_betweenness'],
        "Orphaned Clusters": [f"{kpis['orphaned_count']} groupes détectés"]
    }.items():
        st.markdown(f"""
            <div class='kpi-card'>
                <div class='kpi-title'>{label}</div>
                <div class='kpi-value'>{'<br>'.join(values)}</div>
            </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.subheader("🔗 Chemin le plus court")
    st.write(kpis['shortest_path'])

    st.subheader("🧩 Clusters Louvain")
    st.pyplot(kpis['community_plot'])

elif selected == "Contact":
    st.title("📬 Contact")
    st.info("📩 Pour toute question, contactez l’équipe Avisia : contact@avisia.fr")
