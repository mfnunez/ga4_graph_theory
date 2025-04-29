import streamlit as st
import networkx as nx
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import numpy as np
import matplotlib.pyplot as plt
from google.cloud import bigquery
from community import community_louvain


PROJECT_ID = "avisia-training"

DATASET_ID = "avisia_graph_theory_analytics" 

TABLE_NODES = "avisia_ga4_nodes"
TABLE_EDGES = "avisia_ga4_edges"

@st.cache_data  # Use caching for better performance
def load_edges_data_from_bigquery():
    """Loads data from BigQuery."""
    client = bigquery.Client(project=PROJECT_ID)
    query = f"""
        SELECT *
        FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_EDGES}`
    """
    query_job = client.query(query)  # Make an API request.
    rows = query_job.result()  # Waits for query to finish.
    df = rows.to_dataframe()
    return df

def load_nodes_data_from_bigquery():
    """Loads data from BigQuery."""
    client = bigquery.Client(project=PROJECT_ID)
    query = f"""
        SELECT *
        FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_NODES}`
    """
    query_job = client.query(query)  # Make an API request.
    rows = query_job.result()  # Waits for query to finish.
    dt = rows.to_dataframe()
    return dt

def create_graph():

    df = load_edges_data_from_bigquery()
    dt = load_nodes_data_from_bigquery()
    # Transform data in 'all_ga4_edges.csv'
    df['from_page'] = df['from_page'].astype(str).apply(lambda x: 'productsheet_page' if '/productsheet/' in x else x)
    df['to_page'] = df['to_page'].astype(str).apply(lambda x: 'productsheet_page' if '/productsheet/' in x else x)

    # Transform data in 'all_ga4_nodes.csv'
    dt['page_location'] = dt['page_location'].astype(str).apply(lambda x: 'productsheet_page' if '/productsheet/' in x else x)

    # Create a directed graph
    G = nx.DiGraph()
    
    # Add Edges to networkX Graph object
    for index, row in df.iterrows():
        title_edge = str(row['transition_count'])
        G.add_edge(row['from_page'], row['to_page'], transition_count=row['transition_count'], title=title_edge)
    
    # Add Nodes to networkX Graph object
    for index, row in dt.iterrows():
        title_node = str(row['pageview_count'])
        G.add_node(row['page_location'], page_view_count=row['pageview_count'], title= title_node)
    return G

def create_pyvis_graph(G):
    # Create interactive Pyvis network
    net = Network(height="800px", width="100%", directed=True, select_menu=True, filter_menu=True, cdn_resources='remote')
    # Disable physics to stop continuous movement
    net.toggle_physics(True)

    # Use ForceAtlas2 for better node spreading
    net.force_atlas_2based(
        gravity=-6000,  # Stronger repulsion (negative value)
        central_gravity=0.005,  # Less central attraction
        spring_length=900,  # Nodes spread further apart
        damping=0.9  # Stabilizes movement
    )
    
    # For adding all physics parameters in menu, not needed since found best representation for now
    net.show_buttons(filter_=['physics'])
    net.from_nx(G)
    graph_html = net.generate_html()
    return graph_html

def calculate_kpis(G):
    kpis = {}

    # 1. Degree Centrality
    degree_centrality = nx.degree_centrality(G)
    kpis['degree_centrality'] = degree_centrality
    kpis['most_visited_pages'] = sorted(degree_centrality, key=degree_centrality.get, reverse=True)[:5]  # Top 5
    kpis['degree_centrality_explanation'] = "Degree Centrality: Measures the number of connections a node has. Higher values indicate more central (visited) pages."

    # 2. PageRank
    alpha = st.sidebar.slider("PageRank Alpha", min_value=0.05, max_value=0.95, value=0.85, step=0.05)
    kpis['pagerank_alpha'] = alpha
    pagerank = nx.pagerank(G, alpha=alpha)
    kpis['pagerank'] = pagerank
    kpis['most_influential_pages'] = sorted(pagerank, key=pagerank.get, reverse=True)[:5]  # Top 5
    kpis['pagerank_explanation'] = f"PageRank: Measures the influence of pages based on the number and quality of incoming links (user flow). Alpha (damping factor) is set to {alpha} : It represents the probability that a user will continue navigating the site rather than randomly jumping to another page."

    # 3. Betweenness Centrality
    betweenness_centrality = nx.betweenness_centrality(G)
    kpis['betweenness_centrality'] = betweenness_centrality
    kpis['bottleneck_pages'] = sorted(betweenness_centrality, key=betweenness_centrality.get, reverse=True)[:5]  # Top 5
    kpis['betweenness_centrality_explanation'] = "Betweenness Centrality: Identifies pages that act as bridges in the user flow. Higher values indicate pages that are critical for connecting different parts of the site (potential bottlenecks)."

    # 4. Weakly Connected Components
    weakly_connected_components = list(nx.weakly_connected_components(G))
    kpis['num_orphaned_components'] = len(weakly_connected_components)
    kpis['orphaned_components'] = [component for component in weakly_connected_components if len(component) <= 5]
    kpis['weakly_connected_explanation'] = "Weakly Connected Components: Identifies groups of pages that are reachable from each other, but not necessarily in a directed way. A large number of components with very few nodes each, are Orphaned pages (pages not connected to the rest of the site)."

    # 5. Shortest Path Analysis
    source = st.sidebar.text_input("Shortest Path Source Page", value=betweenness_centrality[0])
    target = st.sidebar.text_input("Shortest Path Target Page", value=betweenness_centrality[1])
    kpis['shortest_path_source'] = source
    kpis['shortest_path_target'] = target
    try:
        shortest_path = nx.shortest_path(G, source=source, target=target)
        kpis['shortest_path'] = shortest_path
    except nx.NetworkXNoPath:
        kpis['shortest_path'] = "No path found between the source and target pages."
    kpis['shortest_path_explanation'] = f"Shortest Path Analysis: Finds the shortest sequence of pages a user would navigate from a source ({source}) page to a target ({target}) page. It can help identify the most efficient user flows."

    # 6. Community Detection (Louvain)
    G_undirected = G.to_undirected()
    partition = community_louvain.best_partition(G_undirected)
    kpis['community_partition'] = partition

    # Create a color map for each community
    unique_clusters = list(set(partition.values()))
    colors = {cluster: np.random.rand(3,) for cluster in unique_clusters}  # Random colors

    # Assign colors to nodes based on their community
    node_colors = [colors[partition[node]] for node in G_undirected.nodes()]

    # Draw the graph
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G_undirected, seed=42)  # Compute node positions
    nx.draw(
        G_undirected, pos, node_color=node_colors, with_labels=True,
        edge_color='gray', node_size=500, font_size=8
    )

    plt.title("GA4 Navigation Graph with Louvain Community Clusters")
    kpis['community_plot'] = plt  # Store the plot object to display in Streamlit
    kpis['community_explanation'] = "Community Detection: Uses the Louvain algorithm to identify clusters of pages with high internal connectivity (pages that users tend to visit together).  This can reveal natural groupings of content or user interests."

    return kpis

def main():
    st.title("GA4 Navigation Graph Analysis")

    G = create_graph()

    # Display the pyvis graph
    graph_html = create_pyvis_graph(G)
    components.html(graph_html, height=800, scrolling=True)

    st.header("Key Performance Indicators (KPIs)")

    kpis = calculate_kpis(G)

    # Display KPIs with explanations
    st.subheader("1. Degree Centrality (Most Visited Pages)")
    st.write(kpis['degree_centrality_explanation'])
    st.write("Most visited pages:", kpis['most_visited_pages'])

    st.subheader("2. PageRank (User Flow Influence)")
    st.write(kpis['pagerank_explanation'])
    st.write("Most influential pages:", kpis['most_influential_pages'])

    st.subheader("3. Betweenness Centrality (Bottlenecks)")
    st.write(kpis['betweenness_centrality_explanation'])
    st.write("Bottleneck pages:", kpis['bottleneck_pages'])

    st.subheader("4. Weakly Connected Components (Orphaned Pages)")
    st.write(kpis['weakly_connected_explanation'])
    st.write(f"Number of orphaned components: {kpis['num_orphaned_components']}")
    st.write("Orphaned components (<= 5 pages):", kpis['orphaned_components'])

    st.subheader("5. Shortest Path Analysis")
    st.write(kpis['shortest_path_explanation'])
    st.write(f"Shortest path from {kpis['shortest_path_source']} to {kpis['shortest_path_target']}:")
    st.write(kpis['shortest_path'])

    st.subheader("6. Community Detection (Louvain)")
    st.write(kpis['community_explanation'])
    st.pyplot(kpis['community_plot'])

if __name__ == "__main__":
    main()
