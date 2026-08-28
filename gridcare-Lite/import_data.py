import sqlite3
import csv
import os


# ============================================================
# GRIDCARE-LITE NETWORK DATA IMPORTER
# ============================================================

# import_data.py is inside gridcare-Lite
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Actual database used by GridCare-Lite
DATABASE_FILE = os.path.join(
    SCRIPT_DIR,
    "gridcare.db"
)

# Data-science directory is one level above gridcare-Lite
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)

DATA_DIR = os.path.join(
    PROJECT_DIR,
    "data-science"
)

SUBSTATIONS_CSV = os.path.join(
    DATA_DIR,
    "substations.csv"
)

LINES_CSV = os.path.join(
    DATA_DIR,
    "lines.csv"
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_value(value):
    """
    Clean CSV values.

    Removes:
    - leading/trailing whitespace
    - accidental ** formatting
    - surrounding whitespace after cleaning
    """
    if value is None:
        return ""

    value = str(value).strip()

    # Remove accidental ** markers found in some versions
    value = value.replace("**", "")

    return value.strip()


def required_value(row, column):
    """
    Get and clean a required CSV field.
    """
    value = clean_value(row.get(column))

    if not value:
        raise ValueError(
            f"Required field '{column}' is empty."
        )

    return value


def integer_value(row, column):
    """
    Read a required integer field.
    """
    value = required_value(row, column)

    try:
        return int(value)
    except ValueError:
        raise ValueError(
            f"Field '{column}' must be an integer. "
            f"Received: '{value}'."
        )


def float_value(row, column):
    """
    Read a required numeric field.
    """
    value = required_value(row, column)

    try:
        return float(value)
    except ValueError:
        raise ValueError(
            f"Field '{column}' must be numeric. "
            f"Received: '{value}'."
        )


def check_file(path, description):
    """
    Check whether a CSV file exists.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{description} not found:\n{path}"
        )


# ============================================================
# SUBSTATION IMPORT
# ============================================================

def import_substations(cursor):
    """
    Import substations.csv into the existing substations table.

    Existing substations are updated.
    New substations are inserted.
    """

    print()
    print("=" * 60)
    print("IMPORTING SUBSTATIONS")
    print("=" * 60)

    check_file(
        SUBSTATIONS_CSV,
        "Substations CSV"
    )

    # Inspect actual database columns
    cursor.execute("PRAGMA table_info(substations)")
    db_columns = {
        row[1]
        for row in cursor.fetchall()
    }

    print("Database columns:")
    for column in sorted(db_columns):
        print(f"  - {column}")

    # Required CSV columns
    required_columns = [
        "Substation ID",
        "Name",
        "Short Name"
    ]

    processed = 0
    inserted = 0
    updated = 0
    skipped = 0
    errors = 0

    with open(
        SUBSTATIONS_CSV,
        "r",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            raise ValueError(
                "substations.csv does not contain a header."
            )

        missing = [
            column
            for column in required_columns
            if column not in reader.fieldnames
        ]

        if missing:
            raise ValueError(
                "Substations CSV is missing required columns: "
                + ", ".join(missing)
            )

        for row_number, row in enumerate(
            reader,
            start=2
        ):
            processed += 1

            try:
                substation_id = integer_value(
                    row,
                    "Substation ID"
                )

                name = required_value(
                    row,
                    "Name"
                )

                short_name = required_value(
                    row,
                    "Short Name"
                )

                # Existing database design uses location.
                # Short Name is used as the location because
                # the current table does not store all CSV fields.
                location = short_name

                # Generate consistent code:
                # 1 -> SUB-001
                # 2 -> SUB-002
                substation_code = (
                    f"SUB-{substation_id:03d}"
                )

                # Optional region support.
                region = clean_value(
                    row.get("Region")
                )

                cursor.execute(
                    """
                    SELECT substation_id
                    FROM substations
                    WHERE substation_id = ?
                    """,
                    (substation_id,)
                )

                existing = cursor.fetchone()

                if existing:

                    # Update only columns that actually exist.
                    if "region" in db_columns:
                        cursor.execute(
                            """
                            UPDATE substations
                            SET substation_code = ?,
                                name = ?,
                                location = ?,
                                region = ?
                            WHERE substation_id = ?
                            """,
                            (
                                substation_code,
                                name,
                                location,
                                region,
                                substation_id
                            )
                        )
                    else:
                        cursor.execute(
                            """
                            UPDATE substations
                            SET substation_code = ?,
                                name = ?,
                                location = ?
                            WHERE substation_id = ?
                            """,
                            (
                                substation_code,
                                name,
                                location,
                                substation_id
                            )
                        )

                    updated += 1

                else:

                    if "region" in db_columns:
                        cursor.execute(
                            """
                            INSERT INTO substations (
                                substation_id,
                                substation_code,
                                name,
                                location,
                                region
                            )
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (
                                substation_id,
                                substation_code,
                                name,
                                location,
                                region
                            )
                        )
                    else:
                        cursor.execute(
                            """
                            INSERT INTO substations (
                                substation_id,
                                substation_code,
                                name,
                                location
                            )
                            VALUES (?, ?, ?, ?)
                            """,
                            (
                                substation_id,
                                substation_code,
                                name,
                                location
                            )
                        )

                    inserted += 1

            except Exception as error:
                errors += 1

                print(
                    f"  ERROR on CSV row {row_number}: {error}"
                )

    print()
    print("Substation import completed.")
    print(f"Rows processed : {processed}")
    print(f"Rows inserted  : {inserted}")
    print(f"Rows updated   : {updated}")
    print(f"Rows skipped   : {skipped}")
    print(f"Errors         : {errors}")

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM substations
        """
    )

    total = cursor.fetchone()[0]

    print(f"Total in DB    : {total}")

    return errors


# ============================================================
# LINES IMPORT
# ============================================================

def import_lines(cursor):
    """
    Import lines.csv into the existing lines table.

    Duplicate protection:
        line_id is checked before insertion.

    Foreign-key validation:
        source_substation_id and
        destination_substation_id
        must exist in substations.
    """

    print()
    print("=" * 60)
    print("IMPORTING TRANSMISSION LINES")
    print("=" * 60)

    check_file(
        LINES_CSV,
        "Lines CSV"
    )

    # Verify lines table exists
    cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name = 'lines'
        """
    )

    if cursor.fetchone() is None:
        raise RuntimeError(
            "The 'lines' table does not exist. "
            "Create it before running this importer."
        )

    # Get actual lines table columns
    cursor.execute("PRAGMA table_info(lines)")
    db_columns = {
        row[1]
        for row in cursor.fetchall()
    }

    print("Database columns:")
    for column in sorted(db_columns):
        print(f"  - {column}")

    required_db_columns = {
        "line_id",
        "utility_id",
        "source_substation_id",
        "destination_substation_id",
        "voltage_kv",
        "length_km",
        "capacity_mva",
        "status",
        "line_type"
    }

    missing_db_columns = (
        required_db_columns - db_columns
    )

    if missing_db_columns:
        raise RuntimeError(
            "The lines table is missing required columns: "
            + ", ".join(sorted(missing_db_columns))
        )

    # Exact CSV fields required for import
    required_csv_columns = [
        "Line ID",
        "Utility ID",
        "Source Substation ID",
        "Source Substation",
        "Destination Substation ID",
        "Destination Substation",
        "Voltage (kV)",
        "Length (km)",
        "Capacity (MVA)",
        "Status",
        "Line Type"
    ]

    processed = 0
    inserted = 0
    skipped = 0
    errors = 0

    with open(
        LINES_CSV,
        "r",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            raise ValueError(
                "lines.csv does not contain a header."
            )

        missing = [
            column
            for column in required_csv_columns
            if column not in reader.fieldnames
        ]

        if missing:
            raise ValueError(
                "Lines CSV is missing required columns: "
                + ", ".join(missing)
            )

        for row_number, row in enumerate(
            reader,
            start=2
        ):
            processed += 1

            try:
                # --------------------------------------------
                # READ AND CLEAN VALUES
                # --------------------------------------------

                line_id = integer_value(
                    row,
                    "Line ID"
                )

                utility_id = integer_value(
                    row,
                    "Utility ID"
                )

                source_substation_id = integer_value(
                    row,
                    "Source Substation ID"
                )

                destination_substation_id = integer_value(
                    row,
                    "Destination Substation ID"
                )

                source_name = required_value(
                    row,
                    "Source Substation"
                )

                destination_name = required_value(
                    row,
                    "Destination Substation"
                )

                voltage_kv = float_value(
                    row,
                    "Voltage (kV)"
                )

                length_km = float_value(
                    row,
                    "Length (km)"
                )

                capacity_mva = float_value(
                    row,
                    "Capacity (MVA)"
                )

                status = required_value(
                    row,
                    "Status"
                )

                line_type = required_value(
                    row,
                    "Line Type"
                )

                # --------------------------------------------
                # BASIC VALIDATION
                # --------------------------------------------

                if line_id <= 0:
                    raise ValueError(
                        "Line ID must be greater than 0."
                    )

                if utility_id <= 0:
                    raise ValueError(
                        "Utility ID must be greater than 0."
                    )

                if source_substation_id <= 0:
                    raise ValueError(
                        "Source Substation ID must be greater than 0."
                    )

                if destination_substation_id <= 0:
                    raise ValueError(
                        "Destination Substation ID must be greater than 0."
                    )

                if source_substation_id == destination_substation_id:
                    raise ValueError(
                        "Source and destination substations "
                        "cannot be the same."
                    )

                if voltage_kv <= 0:
                    raise ValueError(
                        "Voltage must be greater than 0."
                    )

                if length_km <= 0:
                    raise ValueError(
                        "Length must be greater than 0."
                    )

                if capacity_mva <= 0:
                    raise ValueError(
                        "Capacity must be greater than 0."
                    )

                # --------------------------------------------
                # FOREIGN-KEY CHECK: SOURCE SUBSTATION
                # --------------------------------------------

                cursor.execute(
                    """
                    SELECT substation_id, name
                    FROM substations
                    WHERE substation_id = ?
                    """,
                    (source_substation_id,)
                )

                source_substation = cursor.fetchone()

                if source_substation is None:
                    raise ValueError(
                        f"Source substation ID "
                        f"{source_substation_id} does not exist."
                    )

                # --------------------------------------------
                # FOREIGN-KEY CHECK: DESTINATION SUBSTATION
                # --------------------------------------------

                cursor.execute(
                    """
                    SELECT substation_id, name
                    FROM substations
                    WHERE substation_id = ?
                    """,
                    (destination_substation_id,)
                )

                destination_substation = cursor.fetchone()

                if destination_substation is None:
                    raise ValueError(
                        f"Destination substation ID "
                        f"{destination_substation_id} does not exist."
                    )

                # --------------------------------------------
                # NAME VALIDATION
                # --------------------------------------------
                # The CSV gives both IDs and names.
                # IDs are authoritative because they are the
                # database relationship.
                #
                # We warn if the CSV name doesn't correspond
                # to the database name, but do not reject the
                # row merely because of a name difference.

                database_source_name = (
                    source_substation[1] or ""
                ).strip()

                database_destination_name = (
                    destination_substation[1] or ""
                ).strip()

                if (
                    database_source_name.lower()
                    != source_name.lower()
                ):
                    print(
                        f"  WARNING row {row_number}: "
                        f"source name '{source_name}' "
                        f"does not match database name "
                        f"'{database_source_name}' "
                        f"for ID {source_substation_id}."
                    )

                if (
                    database_destination_name.lower()
                    != destination_name.lower()
                ):
                    print(
                        f"  WARNING row {row_number}: "
                        f"destination name '{destination_name}' "
                        f"does not match database name "
                        f"'{database_destination_name}' "
                        f"for ID {destination_substation_id}."
                    )

                # --------------------------------------------
                # DUPLICATE CHECK
                # --------------------------------------------

                cursor.execute(
                    """
                    SELECT line_id
                    FROM lines
                    WHERE line_id = ?
                    """,
                    (line_id,)
                )

                existing_line = cursor.fetchone()

                if existing_line:
                    skipped += 1

                    print(
                        f"  SKIPPED line {line_id}: "
                        f"already exists."
                    )

                    continue

                # --------------------------------------------
                # INSERT LINE
                # --------------------------------------------

                cursor.execute(
                    """
                    INSERT INTO lines (
                        line_id,
                        utility_id,
                        source_substation_id,
                        destination_substation_id,
                        voltage_kv,
                        length_km,
                        capacity_mva,
                        status,
                        line_type
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        line_id,
                        utility_id,
                        source_substation_id,
                        destination_substation_id,
                        voltage_kv,
                        length_km,
                        capacity_mva,
                        status,
                        line_type
                    )
                )

                inserted += 1

            except Exception as error:
                errors += 1

                print(
                    f"  ERROR on CSV row {row_number}: {error}"
                )

    print()
    print("Line import completed.")
    print(f"Rows processed : {processed}")
    print(f"Rows inserted  : {inserted}")
    print(f"Rows skipped   : {skipped}")
    print(f"Errors         : {errors}")

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM lines
        """
    )

    total = cursor.fetchone()[0]

    print(f"Total in DB    : {total}")

    return errors


# ============================================================
# DATABASE SUMMARY
# ============================================================

def print_database_summary(cursor):
    """
    Display final database counts.
    """

    print()
    print("=" * 60)
    print("DATABASE SUMMARY")
    print("=" * 60)

    cursor.execute(
        "SELECT COUNT(*) FROM substations"
    )
    substations = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM lines"
    )
    lines = cursor.fetchone()[0]

    print(f"Substations: {substations}")
    print(f"Lines:       {lines}")

    # Show a few imported lines
    if lines > 0:

        print()
        print("First 5 lines:")

        cursor.execute(
            """
            SELECT
                line_id,
                utility_id,
                source_substation_id,
                destination_substation_id,
                voltage_kv,
                length_km,
                capacity_mva,
                status,
                line_type
            FROM lines
            ORDER BY line_id
            LIMIT 5
            """
        )

        for line in cursor.fetchall():
            print(" ", line)


# ============================================================
# MAIN IMPORT PROCESS
# ============================================================

def main():

    print("=" * 60)
    print("GRIDCARE-LITE NETWORK DATA IMPORT")
    print("=" * 60)

    print()
    print("Database:")
    print(DATABASE_FILE)

    print()
    print("Data directory:")
    print(DATA_DIR)

    # --------------------------------------------------------
    # CHECK DATABASE
    # --------------------------------------------------------

    if not os.path.exists(DATABASE_FILE):
        print()
        print("ERROR: Database does not exist.")
        print(DATABASE_FILE)
        return

    print()
    print("Database connection successful.")

    # --------------------------------------------------------
    # CHECK CSV FILES
    # --------------------------------------------------------

    try:
        check_file(
            SUBSTATIONS_CSV,
            "Substations CSV"
        )

        check_file(
            LINES_CSV,
            "Lines CSV"
        )

    except Exception as error:
        print()
        print("ERROR:", error)
        return

    # --------------------------------------------------------
    # CONNECT
    # --------------------------------------------------------

    db = sqlite3.connect(
        DATABASE_FILE
    )

    try:

        # Enable foreign-key enforcement for this connection.
        db.execute(
            "PRAGMA foreign_keys = ON"
        )

        # ----------------------------------------------------
        # IMPORT DATA
        # ----------------------------------------------------

        substation_errors = import_substations(
            db.cursor()
        )

        line_errors = import_lines(
            db.cursor()
        )

        # ----------------------------------------------------
        # COMMIT
        # ----------------------------------------------------

        if substation_errors > 0 or line_errors > 0:

            print()
            print("=" * 60)
            print("IMPORT FINISHED WITH ERRORS")
            print("=" * 60)

            print(
                "Because one or more rows contained errors, "
                "the transaction will be rolled back."
            )

            db.rollback()

        else:

            db.commit()

            print()
            print("=" * 60)
            print("IMPORT SUCCESSFUL")
            print("=" * 60)

            print(
                "All valid CSV records were imported."
            )

            print(
                "Existing records were preserved."
            )

            print(
                "Duplicate lines were skipped."
            )

        # ----------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------

        print_database_summary(
            db.cursor()
        )

    except Exception as error:

        db.rollback()

        print()
        print("=" * 60)
        print("IMPORT FAILED")
        print("=" * 60)

        print("Error:", error)

        print()
        print(
            "No changes from this import were committed."
        )

    finally:

        db.close()

    print()
    print("=" * 60)
    print("IMPORT PROCESS COMPLETED")
    print("=" * 60)


# ============================================================
# RUN PROGRAM
# ============================================================

if __name__ == "__main__":
    main()