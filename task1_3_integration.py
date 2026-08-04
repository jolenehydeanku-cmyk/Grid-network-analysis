
from collections import defaultdict
import pandas as pd
utilities = pd.read_csv('data-science/utilities_clean.csv')
substations = pd.read_csv('data-science/substations_clean.csv')
lines = pd.read_csv('data-science/lines_clean.csv')

print(utilities.columns.tolist())
print(substations.columns.tolist())
print(lines.columns.tolist())

# Checking  for orphans 

valid_sub_ids = set(substations['Substation ID'])
valid_utility_ids = set(utilities['Utility ID'])

orphan_source = lines[~lines['Source Substation ID'].isin(valid_sub_ids)]
orphan_dest = lines[~lines['Destination Substation ID'].isin(valid_sub_ids)]
orphan_utility = lines[~lines['Utility ID'].isin(valid_utility_ids)]

print(f"Lines with invalid Source Substation ID: {len(orphan_source)}")
print(f"Lines with invalid Destination Substation ID: {len(orphan_dest)}")
print(f"Lines with invalid Utility ID: {len(orphan_utility)}")

# Creating a master database by joining three tables 

sub_cols = ['Substation ID', 'Name', 'Short Name', 'Region', 'Country',
            'Latitude', 'Longitude', 'Voltage (kV)', 'Capacity (MVA)',
            'Type', 'Status']

sub_source = substations[sub_cols].add_suffix('_Source')
sub_dest = substations[sub_cols].add_suffix('_Dest')

merged = lines.merge(
    sub_source, left_on='Source Substation ID', right_on='Substation ID_Source',
    how='left'
)
merged = merged.merge(
    sub_dest, left_on='Destination Substation ID', right_on='Substation ID_Dest',
    how='left'
)
master_dataset = merged.merge(
    utilities.add_suffix('_Utility'), left_on='Utility ID', right_on='Utility ID_Utility',
    how='left'
)

print(f"Master dataset shape: {master_dataset.shape[0]} rows x {master_dataset.shape[1]} columns")

# Step 4: Validate the join

print(f"\nRows before merge (lines): {len(lines)}")
print(f"Rows after merge (master dataset): {len(master_dataset)}")
match = len(lines) == len(master_dataset)
print(f"Row counts match (no duplication from the join): {match}")

nulls = master_dataset[['Name_Source', 'Name_Dest']].isnull().sum()
print(f"\nRemaining nulls after merge:\n{nulls}")

# Step 5: Save outputs
master_dataset.to_csv('master_grid_dataset.csv', index=False)
print("\nSaved master_grid_dataset.csv")

# Data dictionary
data_dict_rows = []
for col in master_dataset.columns:
    dtype = str(master_dataset[col].dtype)
    sample = master_dataset[col].dropna().iloc[0] if master_dataset[col].notna().any() else ""
    data_dict_rows.append({"Column": col, "Data Type": dtype, "Example Value": sample})
data_dict = pd.DataFrame(data_dict_rows)
data_dict.to_csv('data_dictionary.csv', index=False)
print("Saved data_dictionary.csv")

# Join documentation
with open('join_documentation.md', 'w') as f:
    f.write("# Task 1.3 - Join Operation Documentation\n\n")
    f.write("## Source tables\n")
    f.write(f"- utilities_clean.csv: {len(utilities)} rows\n")
    f.write(f"- substations_clean.csv: {len(substations)} rows\n")
    f.write(f"- lines_clean.csv: {len(lines)} rows\n\n")
    f.write("## Orphan check\n")
    f.write(f"- Lines with invalid Source Substation ID: {len(orphan_source)}\n")
    f.write(f"- Lines with invalid Destination Substation ID: {len(orphan_dest)}\n")
    f.write(f"- Lines with invalid Utility ID: {len(orphan_utility)}\n\n")
    f.write("## Join strategy\n")
    f.write("- lines LEFT JOIN substations ON Source Substation ID = Substation ID\n")
    f.write("- result LEFT JOIN substations ON Destination Substation ID = Substation ID\n")
    f.write("- result LEFT JOIN utilities ON Utility ID = Utility ID\n\n")
    f.write("## Validation results\n")
    f.write(f"- Rows before merge: {len(lines)}\n")
    f.write(f"- Rows after merge: {len(master_dataset)}\n")
    f.write(f"- Row counts match: {match}\n")
print("Saved join_documentation.md")

# Step: Create lookup dictionaries for efficient querying
substation_lookup = substations.set_index('Substation ID').to_dict('index')
utility_lookup = utilities.set_index('Utility ID').to_dict('index')

from collections import defaultdict
substation_to_lines = defaultdict(list)
for _, row in lines.iterrows():
    substation_to_lines[row['Source Substation ID']].append(row['Line ID'])
    substation_to_lines[row['Destination Substation ID']].append(row['Line ID'])

print(f"substation_lookup: {len(substation_lookup)} entries")
print(f"utility_lookup: {len(utility_lookup)} entries")
print(f"substation_to_lines: {len(substation_to_lines)} entries")

connected_ids = set(substation_to_lines.keys())
all_ids = set(substations['Substation ID'])
isolated = all_ids - connected_ids
print("Isolated substations:", isolated)
for sid in isolated:
    print(substation_lookup[sid])