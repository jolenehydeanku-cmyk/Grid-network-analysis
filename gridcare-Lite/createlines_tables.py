import sqlite3
import os


# ============================================================
# DATABASE LOCATION
# ============================================================

SCRIPT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATABASE_FILE = os.path.join(
    SCRIPT_DIR,
    "gridcare.db"
)


# ============================================================
# CREATE LINES TABLE
# ============================================================

def create_lines_table():

    print("=" * 60)
    print("GRIDCARE-LITE LINES TABLE SETUP")
    print("=" * 60)

    print()
    print("Database:")
    print(DATABASE_FILE)

    if not os.path.exists(DATABASE_FILE):
        print()
        print("ERROR: Database does not exist.")
        return

    db = sqlite3.connect(DATABASE_FILE)

    try:

        cursor = db.cursor()

        # Enable foreign keys
        cursor.execute(
            "PRAGMA foreign_keys = ON"
        )

        # Check whether lines table already exists
        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name = 'lines'
        """)

        existing = cursor.fetchone()

        if existing:

            print()
            print("The 'lines' table already exists.")
            print("No changes were made.")
            return

        # Create lines table
        cursor.execute("""
            CREATE TABLE lines (

                line_id INTEGER PRIMARY KEY,

                utility_id INTEGER NOT NULL,

                source_substation_id INTEGER NOT NULL,

                destination_substation_id INTEGER NOT NULL,

                voltage_kv REAL NOT NULL,

                length_km REAL NOT NULL,

                capacity_mva REAL NOT NULL,

                status TEXT NOT NULL,

                line_type TEXT NOT NULL,

                FOREIGN KEY (
                    source_substation_id
                )
                REFERENCES substations(substation_id),

                FOREIGN KEY (
                    destination_substation_id
                )
                REFERENCES substations(substation_id)
            )
        """)

        db.commit()

        print()
        print("SUCCESS!")
        print("The 'lines' table has been created.")

        print()
        print("Columns:")

        cursor.execute(
            "PRAGMA table_info(lines)"
        )

        for column in cursor.fetchall():
            print(f"  - {column[1]}")

        print()
        print("Existing records were not modified.")

    except Exception as error:

        db.rollback()

        print()
        print("ERROR:")
        print(error)

    finally:

        db.close()

        print()
        print("=" * 60)
        print("SETUP COMPLETE")
        print("=" * 60)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    create_lines_table()