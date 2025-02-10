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

    # Use ForceAtlas2 for better node spreading
    net.force_atlas_2based(
        gravity=-6000,  # Stronger repulsion (negative value)
        central_gravity=0.005,  # Less central attraction
        spring_length=900,  # Nodes spread further apart
        damping=0.9  # Stabilizes movement
    )

    # Use a better layout
    net.barnes_hut(gravity=53000, central_gravity=0.01, spring_length=300, damping=0.8)

    # Get traffic range (for scaling colors)
    max_degree = max(dict(G.degree()).values()) if G.number_of_nodes() > 0 else 1

    # Define a function to get color based on traffic
    def get_node_color(degree, max_degree):
        if degree > max_degree * 0.66:
            return "#FF5733"  # High traffic → RED
        elif degree > max_degree * 0.33:
            return "#FFA500"  # Medium traffic → ORANGE
        else:
            return "#3498DB"  # Low traffic → BLUE

    # Add nodes with colors based on traffic
    for node in G.nodes():
        degree = G.degree(node)
        color = get_node_color(degree, max_degree)
        net.add_node(node, label=node, size=degree * 8, color=color)

    # Add edges with weight labels
    for edge in G.edges(data=True):
        net.add_edge(edge[0], edge[1], title=f"Count: {edge[2]['weight']}")

    net.from_nx(G)

    # Save graph in templates folder
    graph_path = "templates/graph.html"
    net.save_graph(graph_path)

    # Inject JavaScript for on-click repositioning
    custom_js = """
    <script type="text/javascript">
    function repositionGraph(params) {
        if (params.nodes.length > 0) {
            var nodeId = params.nodes[0];
            var edges = network.body.data.edges.get();

            var incoming = edges.filter(edge => edge.to === nodeId).map(edge => edge.from);
            var outgoing = edges.filter(edge => edge.from === nodeId).map(edge => edge.to);

            var positions = network.getPositions();
            var centerX = 0;
            var centerY = 0;

            // Move selected node to center
            positions[nodeId] = {x: centerX, y: centerY};

            // Arrange incoming nodes to the left
            incoming.forEach((node, index) => {
                positions[node] = {x: centerX - 300, y: centerY + index * 50};
            });

            // Arrange outgoing nodes to the right
            outgoing.forEach((node, index) => {
                positions[node] = {x: centerX + 300, y: centerY + index * 50};
            });

            // Apply new positions
            network.moveTo({position: {x: centerX, y: centerY}, scale: 1});
            network.setOptions({layout: {randomSeed: 2}});
            network.setData({nodes: network.body.data.nodes, edges: network.body.data.edges});
        }
    }

    // Bind click event to function
    network.on("click", repositionGraph);
    </script>
    """

    # Inject JavaScript manually into the saved HTML
    with open(graph_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Append the JavaScript code before </body>
    html_content = html_content.replace("</body>", custom_js + "</body>")

    # Save the modified HTML file
    with open(graph_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return graph_path

@app.route("/")
def index():
    create_graph()
    return render_template("graph.html")

if __name__ == "__main__":
    app.run(debug=True)
