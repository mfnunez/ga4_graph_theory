# (mêmes imports que précédemment)
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

# ---- CONFIGURATION ----
st.set_page_config(page_title="Avisia GA4 Navigator", page_icon="🧠", layout="wide")

# ---- CSS ----
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(145deg, #f3f6fa 0%, #eaf0f8 100%);
}
.hero-section {
    padding: 2rem;
    background: linear-gradient(90deg, #5e72e4, #825ee4);
    color: white;
    border-radius: 16px;
    margin-bottom: 2rem;
}
.kpi-grid {
    display: flex;
    flex-direction: column;
    margin-bottom: 2rem;
}
.kpi-card {
    background: linear-gradient(135deg, #5e72e4 0%, #825ee4 100%);
    border-radius: 16px;
    color: white;
    padding: 1rem 1.5rem;
    box-shadow: 0 8px 20px rgba(0,0,0,0.1);
    margin-bottom: 1.5rem;
    display: block;
}
.kpi-title {
    font-size: 1rem;
    font-weight: bold;
    margin-bottom: 0.5rem;
}
.kpi-explanation {
    font-size: 0.85rem;
    margin-bottom: 1rem;
    opacity: 0.85;
}
.kpi-value {
    font-size: 1.4rem;
    font-weight: bold;
    line-height: 1.5;
}
</style>
""", unsafe_allow_html=True)

# ---- SIDEBAR ----
if 'page_started' not in st.session_state:
    st.session_state.page_started = False

with st.sidebar:
    st.image("logo_avisia.png", width=180)

    # Add refresh button
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.success("Cache cleared! Data will be refreshed.")
        st.rerun()

    st.divider()  # Visual separator

    selected = option_menu(
        menu_title="Menu",
        options=["Accueil", "Graph Analyse", "Contact"],
        icons=["house", "graph-up", "envelope"],
        menu_icon="cast",
        default_index=0,
    )
    dark_mode = st.toggle("🌗 Mode sombre")
if not st.session_state.page_started:
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

# ---- BQ CONFIG ----
PROJECT_ID = "avisia-training"
DATASET_ID = "avisia_graph_theory_analytics"
TABLE_NODES = "avisia_ga4_nodes"
TABLE_EDGES = "avisia_ga4_edges"

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_edges():
    client = bigquery.Client(project=PROJECT_ID)
    query = f"SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_EDGES}`"
    return client.query(query).result().to_dataframe()

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_nodes():
    client = bigquery.Client(project=PROJECT_ID)
    query = f"SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_NODES}`"
    return client.query(query).result().to_dataframe()

# ---- GRAPH CREATION ----
def create_graph():
    df = load_edges()
    dt = load_nodes()
    df['from_page'] = df['from_page'].astype(str).apply(lambda x: 'productsheet_page' if '/productsheet/' in x else x)
    df['to_page'] = df['to_page'].astype(str).apply(lambda x: 'productsheet_page' if '/productsheet/' in x else x)
    dt['page_location'] = dt['page_location'].astype(str).apply(lambda x: 'productsheet_page' if '/productsheet/' in x else x)
    G = nx.DiGraph()
    for _, row in df.iterrows():
        G.add_edge(row['from_page'], row['to_page'], transition_count=row['transition_count'])
    for _, row in dt.iterrows():
        G.add_node(row['page_location'], page_view_count=row['pageview_count'])
    return G

# ---- PYVIS ----
def create_pyvis_graph(G):
    net = Network(height="700px", width="100%", directed=True, select_menu=True, filter_menu=True, cdn_resources='remote')
    net.force_atlas_2based(gravity=-6000, central_gravity=0.005, spring_length=900, damping=0.9)
    net.toggle_physics(True)
    net.show_buttons(filter_=['physics'])
    net.from_nx(G)
    return net.generate_html()

# ---- KPIS ----
def calculate_kpis(G):
    kpis = {}
    degree = nx.degree_centrality(G)
    pagerank = nx.pagerank(G, alpha=st.sidebar.slider("PageRank Alpha", 0.05, 0.95, 0.85, 0.05))
    betweenness = nx.betweenness_centrality(G)
    components = list(nx.weakly_connected_components(G))

    kpis['degree'] = sorted(degree, key=degree.get, reverse=True)[:5]
    kpis['pagerank'] = sorted(pagerank, key=pagerank.get, reverse=True)[:5]
    kpis['betweenness'] = sorted(betweenness, key=betweenness.get, reverse=True)[:5]
    kpis['orphan'] = [f"{len([c for c in components if len(c) <= 10])} groupes détectés"]

    source = st.sidebar.text_input("Page source", value=list(G.nodes)[0])
    target = st.sidebar.text_input("Page cible", value=list(G.nodes)[1])
    try:
        kpis['shortest_path'] = nx.shortest_path(G, source=source, target=target)
    except:
        kpis['shortest_path'] = "Aucun chemin trouvé."

    partition = community_louvain.best_partition(G.to_undirected())
    colors = {c: np.random.rand(3,) for c in set(partition.values())}
    node_colors = [colors[partition[n]] for n in G.nodes()]
    pos = nx.spring_layout(G, k=0.6, seed=42)
    plt.figure(figsize=(14, 10))
    nx.draw(G, pos, node_color=node_colors, with_labels=True, edge_color='gray', node_size=800, font_size=10, font_weight='bold')
    plt.title("Détection de communautés (Louvain)")
    plt.tight_layout()
    kpis['community_plot'] = plt

    kpis['explanations'] = {
        "degree": "🌐 *Mesure du nombre de connexions d’une page.*",
        "pagerank": "⭐ *Mesure l’influence d’une page selon les liens entrants.*",
        "betweenness": "🚣 *Repère les pages-ponts.*",
        "orphan": "🚧 *Groupes de pages isolées.*",
        "shortest": "🧱 *Chemin optimal entre deux pages.*",
        "community": "🧹 *Clusters de navigation cohérents.*"
    }
    return kpis

# ---- PAGE ANALYSE ----
if selected == "Graph Analyse":
    st.title("📊 Analyse Graphique")
    G = create_graph()
    html = create_pyvis_graph(G)
    components.html(html, height=720, scrolling=True)

    kpis = calculate_kpis(G)

    st.markdown("<div class='kpi-grid'>", unsafe_allow_html=True)
    for key, title in {
        "degree": "Top Pages (Degré)",
        "pagerank": "Pages Influentes (PageRank)",
        "betweenness": "Bottlenecks (Betweenness)",
        "orphan": "Orphaned Clusters"
    }.items():
        st.markdown(f"""
            <div class='kpi-card'>
                <div class='kpi-title'>{title}</div>
                <div class='kpi-explanation'>{kpis['explanations'][key]}</div>
                <div class='kpi-value'>{'<br>'.join(kpis[key]) if isinstance(kpis[key], list) else kpis[key]}</div>
            </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.subheader("🔗 Chemin le plus court")
    st.write(kpis['explanations']['shortest'])
    st.write(kpis['shortest_path'])

    st.subheader("🧹 Détection de communautés (Louvain)")
    st.write(kpis['explanations']['community'])
    st.pyplot(kpis['community_plot'])

elif selected == "Accueil":
    st.markdown("""
        <div class="hero-section">
            <h1>Let's Ride the Future.</h1>
            <p>Une interface élégante pour explorer la navigation GA4, powered by Avisia.</p>
        </div>
    """, unsafe_allow_html=True)

elif selected == "Contact":
    st.title("📬 Contact")
    st.info("📩 Pour toute question, contactez l’équipe Avisia : mnunez@avisia.fr")
