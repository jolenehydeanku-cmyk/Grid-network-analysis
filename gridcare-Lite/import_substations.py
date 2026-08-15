import sqlite3
import csv

DATABASE_NAME = "gridcare.db"
CSV_FILE = "substations.csv"


def import_substations():

    db = sqlite3.connect(DATABASE_NAME)
    cursor = db.cursor()

    try:

        with open(CSV_FILE, "r", newline="", encoding="utf-8-sig") as file:

            reader = csv.DictReader(file)

            for row in reader:

                substation_id = int(row["Substation ID"])
                name = row["Name"].strip()
                short_name = row["Short Name"].strip()

                # Use the short name as the location
                location = short_name

                # Create a simple code such as SUB-001
                substation_code = f"SUB-{substation_id:03d}"

                # Check whether this substation already exists
                cursor.execute("""
                    SELECT substation_id
                    FROM substations
                    WHERE substation_id = ?
                """, (substation_id,))

                existing = cursor.fetchone()

                if existing:

                    # Update the existing record
                    cursor.execute("""
                        UPDATE substations
                        SET substation_code = ?,
                            name = ?,
                            location = ?
                        WHERE substation_id = ?
                    """, (
                        substation_code,
                        name,
                        location,
                        substation_id
                    ))

                else:

                    # Add a new substation
                    cursor.execute("""
                        INSERT INTO substations (
                            substation_id,
                            substation_code,
                            name,
                            location
                        )
                        VALUES (?, ?, ?, ?)
                    """, (
                        substation_id,
                        substation_code,
                        name,
                        location
                    ))

        db.commit()

        print("Substations imported successfully!")

        cursor.execute("""
            SELECT COUNT(*)
            FROM substations
        """)

        total = cursor.fetchone()[0]

        print("Total substations in database:", total)

    except Exception as error:

        db.rollback()

        print("Import failed.")
        print("Error:", error)

    finally:

        db.close()


if __name__ == "__main__":
    import_substations()