import streamlit as st
import networkx as nx
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components

def create_graph():
    df = pd.read_csv("all_ga4_edges.csv")
    dt = pd.read_csv("all_ga4_nodes.csv")

    # Transform data in 'all_ga4_edges.csv'
    df['from_page'] = df['from_page'].astype(str).apply(lambda x: 'productsheet_page' if '/productsheet/' in x else x)
    df['to_page'] = df['to_page'].astype(str).apply(lambda x: 'productsheet_page' if '/productsheet/' in x else x)

    # Transform data in 'all_ga4_nodes.csv'
    dt['page_location'] = dt['page_location'].astype(str).apply(lambda x: 'productsheet_page' if '/productsheet/' in x else x)

    # Create a directed graph
    G = nx.DiGraph()
    
    # Add Edges to networkX Graph object
    for index, row in df.iterrows():
        title_node = str(row['transition_count'])
        G.add_edge(row['from_page'], row['to_page'], transition_count=row['transition_count'], title=title_node)
    
    # Add Nodes to networkX Graph object
    for index, row in dt.iterrows():
        title_edge = str(row['pageview_count'])
        G.add_node(row['page_location'], page_view_count=row['pageview_count'], title= title_edge)

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

    # Save graph as HTML
    graph_html = net.generate_html()
    return graph_html

def main():
    st.title("Network Graph")
    graph_html = create_graph()

    # Display the graph using st.components.v1
    components.html(graph_html, height=800, scrolling=True)

if __name__ == "__main__":
    main()
