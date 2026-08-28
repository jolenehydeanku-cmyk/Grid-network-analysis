# Visualization Documentation — Team Member 3 (Visualization Specialist)

This document covers the geographic and advanced visualization deliverables
for the National Electricity Grid Network Analysis project (Tasks 2.2 and 3.2).

## Task 2.2 — Geographic and Geospatial Analysis

### `grid_map.html`
Interactive Folium map of the full grid network, centered on Ghana with
neighboring WAPP interconnects visible. Four toggleable layers:
- **Substations (by voltage)** — circle markers colored by voltage tier
  (green=11kV, blue=33kV, orange=69kV, red=161kV, dark red=330kV), sized by
  capacity (MVA). Clicking a marker shows region, voltage, capacity, and status.
- **Transmission/Distribution Lines** — colored by operating utility so each
  utility's network footprint is visually distinct.
- **Substation Density Heatmap** — shows where substations cluster most
  heavily (off by default to keep the initial view uncluttered).
- **Cross-border Connections** — highlighted in gold to call out the
  international interconnections with Côte d'Ivoire, Togo, Benin, and
  Burkina Faso.

### `regional_analysis.txt`
Substation counts per region, with regions having 1 or fewer substations
flagged as possible coverage gaps (mostly border regions, as expected).

### `distance_distribution.png`
Histogram of line lengths. Recorded route lengths average about 1.17× the
straight-line (haversine) distance between substations — consistent with
real transmission routes not running perfectly straight.

## Task 3.2 — Advanced Visualizations and Insights

### `animated_growth_map.html`
Substations appear on the map cumulatively by commissioning year (1967–2022),
letting a viewer watch the grid's historical build-out. Play/pause and a year
slider are included.

### `network_3d.html`
3D interactive network where elevation (z-axis) encodes voltage tier, so the
high-voltage transmission backbone visually separates from the lower-voltage
distribution layer. Built with Plotly; substations are colored to match the
same voltage palette used in `grid_map.html` for consistency.

### `interregional_chord.png`
Chord-style diagram showing which regions are connected by transmission
lines that cross regional boundaries. Line thickness encodes the number of
connecting lines between each region pair.

### `utility_comparison.png`
Side-by-side bar charts comparing utilities by (1) number of lines operated
and (2) total line capacity (MVA). GRIDCo, as the national transmission
utility, unsurprisingly leads on both metrics.

### `style_guide.md`
Documents the shared color/typography conventions used across all
visualizations in this task, so charts stay visually consistent with each
other and with teammates' business-intelligence charts.

## Design rationale

Color encoding is consistent across every visualization in this set:
voltage tier always maps to the same 5-color scale, and utility identity
always maps to the same qualitative palette. This was a deliberate choice
so that a reader moving between the interactive map, the 3D network view,
and the static charts doesn't have to re-learn the color key each time.

## How to reproduce

From `data-science/data/`, with the CSVs from Task 1.1 present:
```bash
python task2_2_geospatial.py
python task3_2_advanced_viz.py
```
Both scripts read `substations_clean.csv`, `lines_clean.csv`, and (for
Task 3.2) `utilities_clean.csv`, and write their outputs to the same folder.
