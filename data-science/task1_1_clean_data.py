"""
Task 1.1: Data Cleaning and Preprocessing
National Electricity Grid Network Analysis

Loads the three raw CSVs, checks them for missing values, duplicates,
type problems, and broken relationships, then writes clean versions
plus a short data-quality report.
"""
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------
# Step 1: Load and examine raw data
# ---------------------------------------------------------------------
utilities = pd.read_csv('utilities.csv')
substations = pd.read_csv('substations.csv')
lines = pd.read_csv('lines.csv')

report_lines = []


def log(msg=""):
    print(msg)
    report_lines.append(str(msg))


log("=" * 70)
log("TASK 1.1 — DATA CLEANING REPORT")
log("=" * 70)

log("\n--- Shapes ---")
log(f"utilities:   {utilities.shape}")
log(f"substations: {substations.shape}")
log(f"lines:       {lines.shape}")

# ---------------------------------------------------------------------
# Step 2: Missing values
# ---------------------------------------------------------------------
log("\n--- Missing values (before cleaning) ---")
for name, df in [("utilities", utilities), ("substations", substations), ("lines", lines)]:
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if missing.empty:
        log(f"{name}: no missing values")
    else:
        log(f"{name}:\n{missing}")

# Imputation policy (documented, even though the seeded generator produces
# clean data — a real asset register would need this):
#  - Numeric fields (Latitude, Longitude, Capacity, Length): leave as NaN
#    rather than guessing a fake value; flag the row for manual follow-up.
#  - Categorical fields (Region, Status, Type): fill with 'Unknown' so
#    group-by/plotting code doesn't silently drop the row.
categorical_fill = {
    'substations': ['Region', 'Country', 'Type', 'Status'],
    'lines': ['Status', 'Line Type'],
}
for col in categorical_fill['substations']:
    if col in substations.columns:
        substations[col] = substations[col].fillna('Unknown')
for col in categorical_fill['lines']:
    if col in lines.columns:
        lines[col] = lines[col].fillna('Unknown')

# ---------------------------------------------------------------------
# Step 3: Data type consistency
# ---------------------------------------------------------------------
log("\n--- Enforcing numeric types ---")
numeric_cols_substations = ['Latitude', 'Longitude', 'Voltage (kV)',
                             'Capacity (MVA)', 'Commissioning Year']
for col in numeric_cols_substations:
    before_nulls = substations[col].isnull().sum()
    substations[col] = pd.to_numeric(substations[col], errors='coerce')
    after_nulls = substations[col].isnull().sum()
    if after_nulls > before_nulls:
        log(f"substations['{col}']: {after_nulls - before_nulls} value(s) could not be "
            f"parsed as numeric and were coerced to NaN")

numeric_cols_lines = ['Voltage (kV)', 'Length (km)', 'Capacity (MVA)']
for col in numeric_cols_lines:
    before_nulls = lines[col].isnull().sum()
    lines[col] = pd.to_numeric(lines[col], errors='coerce')
    after_nulls = lines[col].isnull().sum()
    if after_nulls > before_nulls:
        log(f"lines['{col}']: {after_nulls - before_nulls} value(s) coerced to NaN")

# ---------------------------------------------------------------------
# Step 4: Duplicates
# ---------------------------------------------------------------------
log("\n--- Duplicate rows ---")
log(f"utilities:   {utilities.duplicated().sum()}")
log(f"substations: {substations.duplicated().sum()}")
log(f"lines:       {lines.duplicated().sum()}")

# Also check duplicate primary keys specifically (a duplicated ID is worse
# than a duplicated full row — it breaks joins even if other columns differ)
for name, df, key in [("utilities", utilities, "Utility ID"),
                       ("substations", substations, "Substation ID"),
                       ("lines", lines, "Line ID")]:
    dup_ids = df[key].duplicated().sum()
    log(f"{name}: {dup_ids} duplicate '{key}' value(s)")

utilities = utilities.drop_duplicates()
substations = substations.drop_duplicates()
lines = lines.drop_duplicates()

# ---------------------------------------------------------------------
# Step 5: Referential integrity — every FK in lines/substations must resolve
# ---------------------------------------------------------------------
log("\n--- Referential integrity checks ---")
valid_sub_ids = set(substations['Substation ID'])
orphan_src = lines[~lines['Source Substation ID'].isin(valid_sub_ids)]
orphan_dst = lines[~lines['Destination Substation ID'].isin(valid_sub_ids)]
log(f"Lines with an unknown Source Substation ID: {len(orphan_src)}")
log(f"Lines with an unknown Destination Substation ID: {len(orphan_dst)}")

valid_utility_ids = set(utilities['Utility ID'])
orphan_utility = lines[~lines['Utility ID'].isin(valid_utility_ids)]
log(f"Lines with an unknown Utility ID: {len(orphan_utility)}")

# Self-loops: a line whose source and destination are the same substation
self_loops = lines[lines['Source Substation ID'] == lines['Destination Substation ID']]
log(f"Self-loop lines (source == destination): {len(self_loops)}")

# ---------------------------------------------------------------------
# Step 6: Geographic bounds — West Africa is roughly lat 4-25N, lon -18-15E
# ---------------------------------------------------------------------
log("\n--- Coordinate bounds check (West Africa: lat 4-25, lon -18 to 15) ---")
bad_coords = substations[
    (substations['Latitude'] < 4) | (substations['Latitude'] > 25) |
    (substations['Longitude'] < -18) | (substations['Longitude'] > 15)
]
log(f"Substations with out-of-range coordinates: {len(bad_coords)}")
if not bad_coords.empty:
    log(bad_coords[['Substation ID', 'Name', 'Latitude', 'Longitude']].to_string(index=False))

# ---------------------------------------------------------------------
# Step 7: Categorical value sanity checks
# ---------------------------------------------------------------------
log("\n--- Categorical value checks ---")
log(f"substations['Status'] values: {sorted(substations['Status'].unique())}")
log(f"substations['Type'] values: {sorted(substations['Type'].unique())}")
log(f"lines['Status'] values: {sorted(lines['Status'].unique())}")
log(f"lines['Line Type'] values: {sorted(lines['Line Type'].unique())}")
log(f"substations['Voltage (kV)'] values: {sorted(substations['Voltage (kV)'].unique())}")

# ---------------------------------------------------------------------
# Step 8: Basic statistics summary
# ---------------------------------------------------------------------
log("\n--- Basic statistics: substations ---")
log(substations[['Latitude', 'Longitude', 'Voltage (kV)', 'Capacity (MVA)',
                  'Commissioning Year']].describe().to_string())

log("\n--- Basic statistics: lines ---")
log(lines[['Voltage (kV)', 'Length (km)', 'Capacity (MVA)']].describe().to_string())

# ---------------------------------------------------------------------
# Save clean CSVs + report
# ---------------------------------------------------------------------
utilities.to_csv('utilities_clean.csv', index=False)
substations.to_csv('substations_clean.csv', index=False)
lines.to_csv('lines_clean.csv', index=False)

with open('data_cleaning_report.txt', 'w') as f:
    f.write("\n".join(report_lines))

log("\n--- Done ---")
log("Wrote: utilities_clean.csv, substations_clean.csv, lines_clean.csv, data_cleaning_report.txt")
