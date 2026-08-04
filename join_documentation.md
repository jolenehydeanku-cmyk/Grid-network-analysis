# Task 1.3 - Join Operation Documentation

## Source tables
- utilities_clean.csv: 10 rows
- substations_clean.csv: 44 rows
- lines_clean.csv: 55 rows

## Orphan check
- Lines with invalid Source Substation ID: 0
- Lines with invalid Destination Substation ID: 0
- Lines with invalid Utility ID: 0

## Join strategy
- lines LEFT JOIN substations ON Source Substation ID = Substation ID
- result LEFT JOIN substations ON Destination Substation ID = Substation ID
- result LEFT JOIN utilities ON Utility ID = Utility ID

## Validation results
- Rows before merge: 55
- Rows after merge: 55
- Row counts match: True
