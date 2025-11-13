#!/usr/bin/env python
# coding: utf-8

# In[43]:


import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
## Do not forget pip install pyvis in network
from pyvis.network import Network
import webbrowser
import os
import community.community_louvain as community_louvain
import numpy as np
from collections import defaultdict


# In[19]:


# Load the CSV file into a DataFrame
df = pd.read_csv("bquxjob_2cc2bb9e_194dd152a8e.csv")


# In[15]:


# Create a directed graph
G = nx.DiGraph()


# In[20]:


# Add edges with weights
for _, row in df.iterrows():
    G.add_edge(row['from_page'], row['to_page'], weight=row['transition_count'])


# In[21]:


# Increase figure size for better readability
plt.figure(figsize=(200, 120))  # Increase the size

# Adjust node layout to reduce overlap
pos = nx.spring_layout(G, k=1.2, seed=42)  # Higher k spreads out nodes

# Draw the graph
nx.draw(G, pos, with_labels=True, node_size=300, font_size=12, edge_color="gray", alpha=0.6)

# Draw edge labels (transition count)
edge_labels = {(u, v): f"{d['weight']}" for u, v, d in G.edges(data=True)}
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=10, bbox=dict(facecolor="white", edgecolor="none", alpha=0.6))

plt.title("GA4 Pageview Transition Graph", fontsize=16)

# Saving image for good vector format zooming
plt.savefig("ga4_network_graph.svg", bbox_inches="tight")

plt.show()

# Part 2 : Create Pyvis network with proper settings for a Dynamic HTML page that will allow zooms 
net = Network(notebook=True, directed=True, height="800px", width="100%", cdn_resources="in_line")

# Disable physics to stop continuous movement
net.toggle_physics(False)

# Add nodes and edges from NetworkX graph
for node in G.nodes():
    net.add_node(node, label=node)

for edge in G.edges(data=True):
    net.add_edge(edge[0], edge[1], title=str(edge[2]['weight']))

# Define file path
file_name = "ga4_network.html"
net.show(file_name)  # Save file

# Get full file path
file_path = os.path.abspath(file_name)

# Open in default web browser
webbrowser.open("file://" + file_path)


# # 1. Identify Key Pages (Nodes)
# ## Degree Centrality (Most Visited Pages)
# ### Definition: 
# Count the number of edges (links) connected to a node (page).
# ### Insight: 
# Helps identify the most frequently visited pages.
# ### Actionable Insight: 
# Prioritize these pages for SEO, UX optimization, or A/B testing.
# ### Implementation:

# In[22]:


degree_centrality = nx.degree_centrality(G)
top_pages = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
print(top_pages)


# # 2. Find the Most Important Pages in User Journeys
# ## PageRank (User Flow & Influence)
# 
# ### Definition: 
# Measures the importance of a page based on incoming links and their importance.
# ### Insight: 
# Identifies pages where users converge, acting as key steps in conversion.
# ### Actionable Insight: 
# Optimize content, CTAs, or promotions on these pages.
# ### Implementation:

# In[23]:


pagerank = nx.pagerank(G, alpha=0.85)
top_pagerank_pages = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:10]
print(top_pagerank_pages)


# # 3. Detect Bottlenecks or Dead-Ends
# ## Betweenness Centrality (Bottlenecks)
# ### Definition: 
# Measures how often a page appears in shortest paths between other pages.
# ### Insight: 
# Pages with high betweenness are critical for navigation, and users depend on them to continue their journey.
# ### Actionable Insight: 
# Ensure these pages load fast, are user-friendly, and have clear paths forward.
# ### Implementation:

# In[24]:


betweenness = nx.betweenness_centrality(G)
critical_pages = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:10]
print(critical_pages)


# # 4. Detect Siloed Pages & Lost Traffic
# ## Weakly Connected Components (Orphaned Pages)
# ### Definition: 
# Groups of pages isolated from the main navigation.
# ### Insight: 
# Pages that don’t connect well with the user journey.
# ### Actionable Insight: 
# Improve internal linking to integrate these pages into the main user flow.
# ### Implementation:

# In[32]:


components = list(nx.weakly_connected_components(G))
isolated_pages = [comp for comp in components if len(comp) < 3]
print(isolated_pages)


# # 5. Optimize Navigation Paths
# ## Shortest Path Analysis (Conversion Funnels)
# ## Definition: 
# Finds the shortest navigation route from landing pages to purchase confirmation.
# ## Insight: 
# Discover the most efficient or common paths to conversion.
# ## Actionable Insight: 
# Remove unnecessary steps, improve breadcrumbs, and reduce friction.
# ## Implementation:
# 

# In[34]:


shortest_paths = nx.shortest_path(G, source='https://formation-ecommerce.avisia.fr/', target='https://formation-ecommerce.avisia.fr/panier?action=show')
print(shortest_paths)


# # 6. Cluster User Behavior Segments
# ## Community Detection (User Segments)
# ## Definition: 
# Groups pages that users frequently navigate together.
# ## Insight: 
# Helps identify content clusters and user intent segments.
# The goal of the Louvain algorithm is to group pages that are frequently visited together, revealing user behavior patterns.
# This helps identify navigation silos, user intents, and optimize conversion paths.
# ## Actionable Insight: 
# Create personalized content recommendations for each segment.
# ## Implementation (Louvain Algorithm with NetworkX & community module):

# In[40]:


# Convert directed graph to undirected graph
G_undirected = G.to_undirected()
partition = community_louvain.best_partition(G_undirected)
print(partition)  # Returns a dictionary of node -> cluster


# In[42]:


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
plt.show()


# In[44]:


# Group pages by their detected community
community_pages = defaultdict(list)
for page, cluster in partition.items():
    community_pages[cluster].append(page)

# Print pages in each community
for cluster, pages in community_pages.items():
    print(f"Cluster {cluster}: {len(pages)} pages")
    print(pages[:10])  # Show first 10 pages in each cluster
    print("-" * 50)


# In[45]:


# Define common keywords for qualitative labeling
labels = {
    "product": "Product Exploration",
    "checkout": "Checkout Process",
    "cart": "Shopping Cart",
    "blog": "Content & Research",
    "support": "Help & FAQ",
    "category": "Category Browsing"
}

# Assign labels to each community
community_labels = {}
for cluster, pages in community_pages.items():
    keywords = []
    for page in pages:
        for keyword, label in labels.items():
            if keyword in page.lower():
                keywords.append(label)
    
    # Get most frequent label in the cluster
    if keywords:
        common_label = max(set(keywords), key=keywords.count)
    else:
        common_label = "Miscellaneous"  # Default if no clear label
    
    community_labels[cluster] = common_label

# Print labeled communities
for cluster, label in community_labels.items():
    print(f"Cluster {cluster}: {label}")


# In[ ]:




