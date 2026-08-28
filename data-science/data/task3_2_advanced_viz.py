"""
Task 3.2 — Advanced Visualizations and Insights
Visualization Specialist (Team Member 3)

Produces:
  1. animated_growth_map.html   - substations appearing over time by commissioning year (plotly)
  2. network_3d.html            - interactive 3D network diagram (plotly)
  3. interregional_chord.png    - chord diagram of inter-regional line connections
  4. utility_comparison.png     - comparative bar charts across utilities
  5. style_guide.md             - design documentation for the whole viz suite
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.path import Path
import matplotlib.patches as patches
import networkx as nx
import plotly.express as px
import plotly.graph_objects as go

substations = pd.read_csv('substations_clean.csv')
lines = pd.read_csv('lines_clean.csv')
utilities = pd.read_csv('utilities_clean.csv')

# Shared style constants — referenced again in style_guide.md
VOLTAGE_COLORS = {11: '#2ca02c', 33: '#1f77b4', 69: '#ff7f0e', 161: '#d62728', 330: '#7f0e0e'}
UTILITY_COLORS = {1: '#1f77b4', 2: '#ff7f0e', 3: '#2ca02c', 4: '#d62728',
                   5: '#9467bd', 6: '#8c564b', 7: '#e377c2', 9: '#7f7f7f'}
FONT = 'DejaVu Sans'

# ---------------------------------------------------------------------
# 1. Animated growth map — substations appear as the network was built
# ---------------------------------------------------------------------
sub_sorted = substations.sort_values('Commissioning Year').copy()
# Build cumulative frames: for each year, show every substation commissioned
# up to and including that year (so the map "fills in" rather than flickering
# single points frame to frame).
years = sorted(sub_sorted['Commissioning Year'].unique())
frames = []
for y in years:
    active = sub_sorted[sub_sorted['Commissioning Year'] <= y].copy()
    active['Frame Year'] = y
    frames.append(active)
animation_df = pd.concat(frames, ignore_index=True)

fig = px.scatter_geo(
    animation_df,
    lat='Latitude', lon='Longitude',
    color='Voltage (kV)',
    size='Capacity (MVA)',
    hover_name='Name',
    hover_data={'Region': True, 'Commissioning Year': True, 'Latitude': False, 'Longitude': False},
    animation_frame='Frame Year',
    color_continuous_scale='Viridis',
    projection='natural earth',
    title='Ghana Grid Network Growth by Commissioning Year',
    scope='africa',
)
fig.update_geos(center=dict(lat=7.5, lon=-1), lataxis_range=[3, 12], lonaxis_range=[-4, 3])
fig.write_html('animated_growth_map.html')
print('Saved animated_growth_map.html')

# ---------------------------------------------------------------------
# 2. 3D network diagram — substations as nodes, lines as edges, elevation
#    encodes voltage tier so higher-voltage backbone stands out visually
# ---------------------------------------------------------------------
sub_by_id = substations.set_index('Substation ID')
voltage_z = {11: 0, 33: 1, 69: 2, 161: 3, 330: 4}

node_x = substations['Longitude']
node_y = substations['Latitude']
node_z = substations['Voltage (kV)'].map(voltage_z)
node_color = substations['Voltage (kV)'].map(VOLTAGE_COLORS)

edge_x, edge_y, edge_z = [], [], []
for _, ln in lines.iterrows():
    src = sub_by_id.loc[ln['Source Substation ID']]
    dst = sub_by_id.loc[ln['Destination Substation ID']]
    edge_x += [src['Longitude'], dst['Longitude'], None]
    edge_y += [src['Latitude'], dst['Latitude'], None]
    edge_z += [voltage_z[src['Voltage (kV)']], voltage_z[dst['Voltage (kV)']], None]

edge_trace = go.Scatter3d(x=edge_x, y=edge_y, z=edge_z, mode='lines',
                           line=dict(color='rgba(150,150,150,0.5)', width=2), hoverinfo='none')
node_trace = go.Scatter3d(
    x=node_x, y=node_y, z=node_z, mode='markers',
    marker=dict(size=5, color=node_color, opacity=0.9),
    text=substations['Name'] + '<br>' + substations['Voltage (kV)'].astype(str) + ' kV',
    hoverinfo='text',
)
fig3d = go.Figure(data=[edge_trace, node_trace])
fig3d.update_layout(
    title='3D Grid Network — Elevation Encodes Voltage Tier',
    scene=dict(xaxis_title='Longitude', yaxis_title='Latitude', zaxis_title='Voltage Tier'),
    showlegend=False,
)
fig3d.write_html('network_3d.html')
print('Saved network_3d.html')

# ---------------------------------------------------------------------
# 3. Chord-style diagram — inter-regional line connections
# ---------------------------------------------------------------------
region_of = substations.set_index('Substation ID')['Region']
lines2 = lines.copy()
lines2['Src Region'] = lines2['Source Substation ID'].map(region_of)
lines2['Dst Region'] = lines2['Destination Substation ID'].map(region_of)
interregional = lines2[lines2['Src Region'] != lines2['Dst Region']]

pair_counts = (interregional.groupby(['Src Region', 'Dst Region']).size()
               .reset_index(name='count'))

regions = sorted(set(pair_counts['Src Region']) | set(pair_counts['Dst Region']))
n = len(regions)
angle = {r: 2 * np.pi * i / n for i, r in enumerate(regions)}
pos = {r: (np.cos(angle[r]), np.sin(angle[r])) for r in regions}

fig_chord, ax = plt.subplots(figsize=(9, 9), subplot_kw={'aspect': 'equal'})
cmap = plt.cm.tab20
region_color = {r: cmap(i / n) for i, r in enumerate(regions)}

for r in regions:
    x, y = pos[r]
    ax.scatter(x, y, s=300, color=region_color[r], zorder=3, edgecolors='white')
    ax.annotate(r, (x, y), xytext=(x * 1.18, y * 1.18), ha='center', va='center', fontsize=8)

for _, row in pair_counts.iterrows():
    x1, y1 = pos[row['Src Region']]
    x2, y2 = pos[row['Dst Region']]
    # Bezier curve bowing toward the center for a "chord" look
    verts = [(x1, y1), (0, 0), (x2, y2)]
    codes = [Path.MOVETO, Path.CURVE3, Path.CURVE3]
    path = Path(verts, codes)
    patch = patches.PathPatch(path, facecolor='none',
                               edgecolor=region_color[row['Src Region']],
                               lw=0.5 + row['count'] * 0.8, alpha=0.55, zorder=1)
    ax.add_patch(patch)

ax.set_xlim(-1.4, 1.4)
ax.set_ylim(-1.4, 1.4)
ax.axis('off')
ax.set_title('Inter-Regional Transmission Connections\n(line width = number of connecting lines)')
plt.tight_layout()
plt.savefig('interregional_chord.png', dpi=150)
plt.close()
print('Saved interregional_chord.png')

# ---------------------------------------------------------------------
# 4. Comparative utility charts
# ---------------------------------------------------------------------
lines_per_utility = lines['Utility ID'].value_counts().sort_index()
capacity_per_utility = lines.groupby('Utility ID')['Capacity (MVA)'].sum().sort_index()
utility_names = utilities.set_index('Utility ID')['Alias']

fig_cmp, axes = plt.subplots(1, 2, figsize=(13, 5))

names1 = [utility_names.get(i, str(i)) for i in lines_per_utility.index]
axes[0].bar(names1, lines_per_utility.values,
            color=[UTILITY_COLORS.get(i, '#999999') for i in lines_per_utility.index])
axes[0].set_title('Lines Operated per Utility')
axes[0].set_ylabel('Number of lines')
axes[0].tick_params(axis='x', rotation=45)

names2 = [utility_names.get(i, str(i)) for i in capacity_per_utility.index]
axes[1].bar(names2, capacity_per_utility.values,
            color=[UTILITY_COLORS.get(i, '#999999') for i in capacity_per_utility.index])
axes[1].set_title('Total Line Capacity per Utility (MVA)')
axes[1].set_ylabel('Capacity (MVA)')
axes[1].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig('utility_comparison.png', dpi=150)
plt.close()
print('Saved utility_comparison.png')

# ---------------------------------------------------------------------
# 5. Style guide
# ---------------------------------------------------------------------
style_guide = f"""# Visualization Style Guide — Ghana Grid Project

## Color encoding
**Voltage tiers** (used consistently across the folium map, 3D network, and
any future charts):
- 11 kV  → {VOLTAGE_COLORS[11]} (green)
- 33 kV  → {VOLTAGE_COLORS[33]} (blue)
- 69 kV  → {VOLTAGE_COLORS[69]} (orange)
- 161 kV → {VOLTAGE_COLORS[161]} (red)
- 330 kV → {VOLTAGE_COLORS[330]} (dark red)

**Utilities** get a fixed qualitative palette (tab10-style) so the same
utility is always the same color across every chart in the project —
important for Member 2's business-intelligence charts too, since we're
sharing this data.

## Typography
Default matplotlib/plotly sans-serif ({FONT}). Titles: bold, ~14pt.
Axis labels: regular, ~11pt.

## Chart conventions
- Bar charts: utility names on x-axis are always rotated 45° to stay readable.
- Line width in network/chord diagrams encodes connection count/capacity —
  never used purely decoratively.
- Geographic maps center on Ghana (lat ~7.5, lon ~-1) with a bounding box
  that includes the immediate cross-border neighbors (WAPP interconnects).

## File naming
Each task's outputs are prefixed by their content, not the task number
(e.g. `grid_map.html`, not `task2_2_output.html`) so files stay meaningful
once combined into the final dashboard/report.
"""
with open('style_guide.md', 'w') as f:
    f.write(style_guide)
print('Saved style_guide.md')

print('\n--- Done ---')
