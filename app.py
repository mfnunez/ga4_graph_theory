from flask import Flask, render_template
import networkx as nx
import pandas as pd
from pyvis.network import Network
import os

app = Flask(__name__)

def create_graph():
    df = pd.read_csv("ga4_edges.csv")

    # Create a directed graph
    G = nx.DiGraph()
    for _, row in df.iterrows():
        G.add_edge(row['from_page'], row['to_page'], weight=row['transition_count'])

    # Create interactive Pyvis network
    net = Network(height="800px", width="100%", directed=True)
    
    # Use a better layout
    net.barnes_hut(gravity=53000, central_gravity=0.01, spring_length=300, damping=0.8)

    # Disable physics to stop continuous movement
    net.toggle_physics(False)

    for node in G.nodes():
        degree = G.degree(node)
        net.add_node(node, label=node, size=degree * 5)  # Scale size

    # Add edges with weight labels
    for edge in G.edges(data=True):
        net.add_edge(edge[0], edge[1], title=f"Count: {edge[2]['weight']}")

    net.from_nx(G)

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