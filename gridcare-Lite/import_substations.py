import sqlite3
import csv
import os


# ============================================================
# FILE LOCATIONS
# ============================================================

# Project root:
# Grid-network-analysis
PROJECT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

# Database currently used by the project
DATABASE_FILE = os.path.join(
    PROJECT_DIR,
    "gridcare.db"
)

# Real substations dataset created by the group
CSV_FILE = os.path.join(
    PROJECT_DIR,
    "data-science",
    "substations.csv"
)


# ============================================================
# IMPORT SUBSTATIONS
# ============================================================

def import_substations():

    db = sqlite3.connect(DATABASE_FILE)
    cursor = db.cursor()

    try:

        # Check whether CSV exists
        if not os.path.exists(CSV_FILE):

            print("Import failed.")
            print("Could not find:")
            print(CSV_FILE)

            return

        print("Reading substations from:")
        print(CSV_FILE)

        with open(
            CSV_FILE,
            "r",
            newline="",
            encoding="utf-8-sig"
        ) as file:

            reader = csv.DictReader(file)

            rows_processed = 0

            for row in reader:

                substation_id = int(
                    row["Substation ID"]
                )

                name = row["Name"].strip()

                short_name = row["Short Name"].strip()

                location = short_name

                # Example:
                # SUB-001
                # SUB-002
                # SUB-003
                substation_code = (
                    f"SUB-{substation_id:03d}"
                )

                # Check if substation already exists
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

                rows_processed += 1

        db.commit()

        print()
        print("Substations imported successfully!")
        print(
            "Rows processed:",
            rows_processed
        )

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM substations
            """
        )

        total = cursor.fetchone()[0]

        print(
            "Total substations in database:",
            total
        )

        print()
        print("First few substations:")

        cursor.execute(
            """
            SELECT
                substation_id,
                substation_code,
                name,
                location
            FROM substations
            ORDER BY substation_id
            LIMIT 10
            """
        )

        for substation in cursor.fetchall():

            print(substation)

    except Exception as error:

        db.rollback()

        print("Import failed.")
        print("Error:", error)

    finally:

        db.close()


# ============================================================
# RUN PROGRAM
# ============================================================

if __name__ == "__main__":
    import_substations()