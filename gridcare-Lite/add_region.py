import sqlite3
import os


# ============================================================
# DATABASE LOCATION
# ============================================================

PROJECT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATABASE_FILE = os.path.join(
    PROJECT_DIR,
    "gridcare.db"
)


# ============================================================
# ADD REGION COLUMN
# ============================================================

def add_region_column():

    print("=" * 60)
    print("GRIDCARE-LITE REGION COLUMN SETUP")
    print("=" * 60)

    print()
    print("Database:")
    print(DATABASE_FILE)

    if not os.path.exists(DATABASE_FILE):
        print()
        print("ERROR: Database does not exist.")
        return

    db = sqlite3.connect(DATABASE_FILE)
    cursor = db.cursor()

    try:

        # Check existing columns
        cursor.execute("PRAGMA table_info(substations)")
        columns = [
            row[1]
            for row in cursor.fetchall()
        ]

        print()
        print("Current substations columns:")

        for column in columns:
            print("  -", column)

        # Add region only if it does not already exist
        if "region" in columns:

            print()
            print("The 'region' column already exists.")
            print("No changes were necessary.")

        else:

            cursor.execute(
                """
                ALTER TABLE substations
                ADD COLUMN region TEXT
                """
            )

            db.commit()

            print()
            print("SUCCESS!")
            print("The 'region' column has been added to")
            print("the 'substations' table.")

        # Verify
        cursor.execute("PRAGMA table_info(substations)")

        print()
        print("Updated substations columns:")

        for row in cursor.fetchall():
            print("  -", row[1])

        print()
        print("=" * 60)
        print("SETUP COMPLETE")
        print("=" * 60)

    except Exception as error:

        db.rollback()

        print()
        print("ERROR:")
        print(error)

    finally:

        db.close()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    add_region_column()