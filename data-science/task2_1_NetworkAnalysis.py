import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

# Load your Task 1.3 outputs
substations = pd.read_csv('substations_clean.csv')
lines = pd.read_csv('lines_clean.csv')

# Create an undirected graph
G = nx.Graph()

# Add substations as nodes, with useful info attached to each one
for _, row in substations.iterrows():
    G.add_node(
        row['Substation ID'],
        name=row['Name'],
        region=row['Region'],
        voltage=row['Voltage (kV)'],
        lat=row['Latitude'],
        lon=row['Longitude']
    )

# Add lines as edges, with length/capacity attached as "weights"
for _, row in lines.iterrows():
    G.add_edge(
        row['Source Substation ID'],
        row['Destination Substation ID'],
        length=row['Length (km)'],
        capacity=row['Capacity (MVA)']
    )

print(f"Graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")


# Step 2: Centrality measures
degree_centrality = nx.degree_centrality(G)
betweenness_centrality = nx.betweenness_centrality(G)
closeness_centrality = nx.closeness_centrality(G)
pagerank = nx.pagerank(G)

# Put them all into one table for easy comparison
centrality_df = pd.DataFrame({
    'Substation ID': list(G.nodes()),
    'Name': [G.nodes[n]['name'] for n in G.nodes()],
    'Region': [G.nodes[n]['region'] for n in G.nodes()],
    'Degree Centrality': [degree_centrality[n] for n in G.nodes()],
    'Betweenness Centrality': [betweenness_centrality[n] for n in G.nodes()],
    'Closeness Centrality': [closeness_centrality[n] for n in G.nodes()],
    'PageRank': [pagerank[n] for n in G.nodes()],
})

# Sort by betweenness centrality (most critical "bridge" substations first)
centrality_df = centrality_df.sort_values('Betweenness Centrality', ascending=False)

print("\nTop 10 most critical substations (by betweenness centrality):")
print(centrality_df.head(10)[['Name', 'Region', 'Betweenness Centrality', 'Degree Centrality']])

# Step 3: Network-wide structure metrics
if nx.is_connected(G):
    diameter = nx.diameter(G)
    avg_path_length = nx.average_shortest_path_length(G)
else:
    print("Network is NOT fully connected — measuring largest component only")
    largest_cc = max(nx.connected_components(G), key=len)
    subgraph = G.subgraph(largest_cc)
    diameter = nx.diameter(subgraph)
    avg_path_length = nx.average_shortest_path_length(subgraph)

avg_clustering = nx.average_clustering(G)

print(f"\nNetwork diameter: {diameter}")
print(f"Average shortest path length: {avg_path_length:.2f}")
print(f"Average clustering coefficient: {avg_clustering:.3f}")
print(f"Is the network fully connected: {nx.is_connected(G)}")
print(f"Number of connected components: {nx.number_connected_components(G)}")

# Step 4: Community detection
from networkx.algorithms import community

# Run on the largest connected component (community detection needs a connected graph)
largest_cc = max(nx.connected_components(G), key=len)
subgraph = G.subgraph(largest_cc)

communities = community.greedy_modularity_communities(subgraph)

print(f"\nNumber of communities detected: {len(communities)}")
for i, comm in enumerate(communities):
    regions_in_community = set(G.nodes[n]['region'] for n in comm)
    print(f"\nCommunity {i+1}: {len(comm)} substations")
    print(f"  Regions represented: {regions_in_community}")

    # Step 5: N-1 Contingency Analysis
print("\n" + "=" * 60)
print("N-1 CONTINGENCY ANALYSIS")
print("=" * 60)

# Test the top 5 most critical substations (by betweenness centrality)
top_critical = centrality_df.head(5)

results = []
for _, row in top_critical.iterrows():
    sub_id = row['Substation ID']
    sub_name = row['Name']

    # Make a copy of the graph and remove this one substation
    G_test = G.copy()
    G_test.remove_node(sub_id)

    # Check how many separate pieces the network splits into
    components_before = nx.number_connected_components(G)
    components_after = nx.number_connected_components(G_test)

    # Check the size of the largest remaining piece
    largest_before = len(max(nx.connected_components(G), key=len))
    largest_after = len(max(nx.connected_components(G_test), key=len))

    results.append({
        'Substation': sub_name,
        'Components Before': components_before,
        'Components After': components_after,
        'New Splits Caused': components_after - components_before,
        'Largest Piece Before': largest_before,
        'Largest Piece After': largest_after,
        'Substations Cut Off': largest_before - largest_after
    })

n1_results = pd.DataFrame(results)
print(n1_results.to_string(index=False))


# Save your results
centrality_df.to_csv('network_centrality_analysis.csv', index=False)
n1_results.to_csv('n1_contingency_results.csv', index=False)

# Draw and save a visualization of the network
plt.figure(figsize=(14, 10))
pos = {n: (G.nodes[n]['lon'], G.nodes[n]['lat']) for n in G.nodes()}

node_sizes = [centrality_df.set_index('Substation ID').loc[n, 'Betweenness Centrality'] * 3000 + 50
              for n in G.nodes()]

nx.draw(G, pos, node_size=node_sizes, node_color='#4A90D9', 
        edge_color='#cccccc', with_labels=False, alpha=0.8)

plt.title('Ghana Electricity Grid Network — Node size = Betweenness Centrality')
plt.savefig('network_visualization.png', dpi=150, bbox_inches='tight')
print("\nSaved: network_centrality_analysis.csv, n1_contingency_results.csv, network_visualization.png")



# Save network-wide metrics summary
with open('network_metrics_summary.md', 'w') as f:
    f.write("# Task 2.1 - Network Metrics Summary\n\n")
    f.write(f"- Total substations (nodes): {G.number_of_nodes()}\n")
    f.write(f"- Total lines (edges): {G.number_of_edges()}\n")
    f.write(f"- Network diameter: {diameter}\n")
    f.write(f"- Average shortest path length: {avg_path_length:.2f}\n")
    f.write(f"- Average clustering coefficient: {avg_clustering:.3f}\n")
    f.write(f"- Fully connected: {nx.is_connected(G)}\n")
    f.write(f"- Number of connected components: {nx.number_connected_components(G)}\n")
    f.write(f"- Communities detected: {len(communities)}\n\n")
    f.write("## Top 5 Critical Substations (by Betweenness Centrality)\n\n")
    f.write(top_critical[['Name', 'Region', 'Betweenness Centrality']].to_string(index=False))
    f.write("\n\n## N-1 Contingency Results\n\n")
    f.write(n1_results.to_string(index=False))
print("Saved network_metrics_summary.md")