from flask import Flask, render_template
import networkx as nx
import pandas as pd
from pyvis.network import Network
import os

app = Flask(__name__)

def create_graph():
    df = pd.read_csv("ga4_edges.csv")
    dt = pd.read_csv("ga4_nodes.csv")
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
    net = Network(height="800px", width="100%", directed=True,select_menu=True, filter_menu=True, cdn_resources='remote')
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

    

    # Use a better layout with other algorithm Thant Force Atlas 2
    # net.barnes_hut(gravity=53000, central_gravity=0.01, spring_length=300, damping=0.8)
    
    

    # Get traffic range (for scaling colors)
    max_degree = max(dict(G.degree()).values()) if G.number_of_nodes() > 0 else 1

    # Define a function to get color based on traffic
    #def get_node_color(degree, max_degree):
        #if degree > max_degree * 0.66:
            #return "#FF5733"  # High traffic → RED
        #elif degree > max_degree * 0.33:
            #return "#FFA500"  # Medium traffic → ORANGE
        #else:
            #return "#3498DB"  # Low traffic → BLUE

    # Add nodes with colors based on traffic
    #for node in G.nodes():
        #degree = G.degree(node)
        #color = get_node_color(degree, max_degree)
        #net.add_node(node, label=node, size=degree, color=color)


    # Add edges with weight labels
    #for edge in G.edges(data=True):
         #net.add_edge(edge[0], edge[1], title=f"Count: {edge[2]['weight']}")

    


    # Save graph in templates folder
    graph_path = "templates/graph.html"
    net.save_graph(graph_path)

    return graph_path

@app.route("/")
def index():
    create_graph()
    return render_template("graph.html")

if __name__ == "__main__":
    app.run(debug=True)