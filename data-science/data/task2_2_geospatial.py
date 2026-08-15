"""
Task 2.2 — Geographic and Geospatial Analysis
Visualization Specialist (Team Member 3)

Produces:
  1. grid_map.html            - interactive folium map (layered)
  2. regional_analysis.txt    - substation density + coverage report
  3. distance_distribution.png - histogram of line lengths
"""
import math
import pandas as pd
import matplotlib.pyplot as plt
import folium
from folium.plugins import HeatMap

substations = pd.read_csv('substations_clean.csv')
lines = pd.read_csv('lines_clean.csv')

report = []


def log(msg=""):
    print(msg)
    report.append(str(msg))


# ---------------------------------------------------------------------
# 1. Regional density analysis
# ---------------------------------------------------------------------
log("=" * 70)
log("TASK 2.2 — GEOGRAPHIC / GEOSPATIAL ANALYSIS")
log("=" * 70)

log("\n--- Substation count by region ---")
region_counts = substations['Region'].value_counts()
log(region_counts.to_string())

log("\n--- Substations by voltage tier ---")
log(substations['Voltage (kV)'].value_counts().sort_index().to_string())

# Simple "coverage gap" flag: regions with only 1 substation are thin on
# redundancy — worth calling out in the write-up.
sparse_regions = region_counts[region_counts <= 1]
log(f"\nRegions with 1 or fewer substations (possible coverage gap): "
    f"{list(sparse_regions.index)}")

# ---------------------------------------------------------------------
# 2. Distance distribution (haversine, recomputed independently as a
#    cross-check against the 'Length (km)' column already in lines.csv)
# ---------------------------------------------------------------------
sub_by_id = substations.set_index('Substation ID')


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


computed = []
for _, row in lines.iterrows():
    src = sub_by_id.loc[row['Source Substation ID']]
    dst = sub_by_id.loc[row['Destination Substation ID']]
    computed.append(haversine_km(src['Latitude'], src['Longitude'],
                                  dst['Latitude'], dst['Longitude']))
lines['Straight-line Distance (km)'] = computed

log("\n--- Line length statistics (recorded route length) ---")
log(lines['Length (km)'].describe().to_string())

log("\n--- Recorded vs straight-line distance ---")
log(f"Average recorded length is "
    f"{(lines['Length (km)'] / lines['Straight-line Distance (km)']).mean():.2f}x "
    f"the straight-line distance (expected — real routes aren't straight lines).")

plt.figure(figsize=(8, 5))
plt.hist(lines['Length (km)'], bins=15, color='#2b6cb0', edgecolor='white')
plt.xlabel('Line length (km)')
plt.ylabel('Number of lines')
plt.title('Distribution of Transmission/Distribution Line Lengths')
plt.tight_layout()
plt.savefig('distance_distribution.png', dpi=150)
plt.close()
log("\nSaved distance_distribution.png")

# ---------------------------------------------------------------------
# 3. Interactive folium map
# ---------------------------------------------------------------------
center_lat = substations['Latitude'].mean()
center_lon = substations['Longitude'].mean()

m = folium.Map(location=[center_lat, center_lon], zoom_start=7, tiles='CartoDB positron')

voltage_colors = {11: 'green', 33: 'blue', 69: 'orange', 161: 'red', 330: 'darkred'}

sub_layer = folium.FeatureGroup(name='Substations (by voltage)')
for _, s in substations.iterrows():
    color = voltage_colors.get(s['Voltage (kV)'], 'gray')
    folium.CircleMarker(
        location=[s['Latitude'], s['Longitude']],
        radius=5 + (s['Capacity (MVA)'] / 100),
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.75,
        popup=folium.Popup(
            f"<b>{s['Name']}</b><br>"
            f"Region: {s['Region']}<br>"
            f"Voltage: {s['Voltage (kV)']} kV<br>"
            f"Capacity: {s['Capacity (MVA)']} MVA<br>"
            f"Status: {s['Status']}",
            max_width=250
        ),
    ).add_to(sub_layer)
sub_layer.add_to(m)

# Lines layer, colored by utility so each utility's network stands out
utility_colors = {1: '#1f77b4', 2: '#ff7f0e', 3: '#2ca02c', 4: '#d62728',
                   5: '#9467bd', 6: '#8c564b', 7: '#e377c2', 9: '#7f7f7f'}
lines_layer = folium.FeatureGroup(name='Transmission/Distribution Lines')
for _, ln in lines.iterrows():
    src = sub_by_id.loc[ln['Source Substation ID']]
    dst = sub_by_id.loc[ln['Destination Substation ID']]
    color = utility_colors.get(ln['Utility ID'], 'black')
    folium.PolyLine(
        locations=[[src['Latitude'], src['Longitude']],
                   [dst['Latitude'], dst['Longitude']]],
        color=color,
        weight=2 + ln['Voltage (kV)'] / 165,
        opacity=0.6,
        popup=f"{ln['Source Substation']} → {ln['Destination Substation']}<br>"
              f"{ln['Length (km)']} km, {ln['Voltage (kV)']} kV",
    ).add_to(lines_layer)
lines_layer.add_to(m)

# Heatmap of substation density
heat_layer = folium.FeatureGroup(name='Substation Density Heatmap', show=False)
HeatMap(substations[['Latitude', 'Longitude']].values.tolist(), radius=25).add_to(heat_layer)
heat_layer.add_to(m)

# Cross-border connections highlighted separately
border_layer = folium.FeatureGroup(name='Cross-border Connections')
border_countries = {'Cote d\'Ivoire', 'Cote d\'Ivoire border', 'Togo', 'Togo border',
                     'Benin', 'Burkina Faso', 'Burkina Faso border', 'Guinea'}
for _, ln in lines.iterrows():
    src = sub_by_id.loc[ln['Source Substation ID']]
    dst = sub_by_id.loc[ln['Destination Substation ID']]
    if src['Country'] in border_countries or dst['Country'] in border_countries:
        folium.PolyLine(
            locations=[[src['Latitude'], src['Longitude']],
                       [dst['Latitude'], dst['Longitude']]],
            color='gold', weight=4, opacity=0.9,
            popup=f"Cross-border: {ln['Source Substation']} → {ln['Destination Substation']}",
        ).add_to(border_layer)
border_layer.add_to(m)

folium.LayerControl(collapsed=False).add_to(m)
m.save('grid_map.html')
log("\nSaved grid_map.html")

with open('regional_analysis.txt', 'w') as f:
    f.write("\n".join(report))

log("\n--- Done ---")
