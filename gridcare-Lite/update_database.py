import sqlite3
import os
from datetime import datetime

DATABASE_NAME = "gridcare.db"


def column_exists(cursor, table_name, column_name):
    """
    Check whether a column already exists in a table.
    """
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()

    return any(column[1] == column_name for column in columns)


def table_exists(cursor, table_name):
    """
    Check whether a table already exists.
    """
    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
    """, (table_name,))

    return cursor.fetchone() is not None


def create_backup():
    """
    Create a backup of the existing database before making changes.
    The original database is NOT deleted or replaced.
    """

    if not os.path.exists(DATABASE_NAME):
        print("ERROR: gridcare.db was not found.")
        print("Make sure database_update.py is in the same folder as gridcare.db.")
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"gridcare_backup_{timestamp}.db"

    source = sqlite3.connect(DATABASE_NAME)
    backup = sqlite3.connect(backup_name)

    with backup:
        source.backup(backup)

    source.close()
    backup.close()

    print(f"Backup created successfully: {backup_name}")

    return backup_name


def update_database():
    """
    Safely update the existing GridCare-Lite database.

    This function:
    - preserves existing data
    - adds the lines table
    - adds region to substations
    - adds resolved_at to outages
    - changes old outage status 'Reported' to 'Open'
    - keeps the existing database file
    """

    if not os.path.exists(DATABASE_NAME):
        print("ERROR: gridcare.db does not exist.")
        return False

    db = sqlite3.connect(DATABASE_NAME)
    cursor = db.cursor()

    try:

        # ---------------------------------------------------------
        # 1. Add REGION to substations
        # ---------------------------------------------------------

        if not column_exists(cursor, "substations", "region"):

            cursor.execute("""
                ALTER TABLE substations
                ADD COLUMN region TEXT
            """)

            print("✓ Added 'region' column to substations.")

        else:

            print("✓ 'region' column already exists in substations.")

        # ---------------------------------------------------------
        # 2. Add RESOLVED_AT to outages
        # ---------------------------------------------------------

        if not column_exists(cursor, "outages", "resolved_at"):

            cursor.execute("""
                ALTER TABLE outages
                ADD COLUMN resolved_at TEXT
            """)

            print("✓ Added 'resolved_at' column to outages.")

        else:

            print("✓ 'resolved_at' column already exists in outages.")

        # ---------------------------------------------------------
        # 3. Create LINES table
        # ---------------------------------------------------------

        if not table_exists(cursor, "lines"):

            cursor.execute("""
                CREATE TABLE lines (

                    line_id INTEGER PRIMARY KEY AUTOINCREMENT,

                    line_code TEXT UNIQUE NOT NULL,

                    name TEXT NOT NULL,

                    from_substation_id INTEGER,

                    to_substation_id INTEGER,

                    voltage TEXT,

                    region TEXT,

                    FOREIGN KEY (from_substation_id)
                        REFERENCES substations(substation_id),

                    FOREIGN KEY (to_substation_id)
                        REFERENCES substations(substation_id)

                )
            """)

            print("✓ Created 'lines' table.")

        else:

            print("✓ 'lines' table already exists.")

        # ---------------------------------------------------------
        # 4. Change old outage status Reported → Open
        # ---------------------------------------------------------

        cursor.execute("""
            UPDATE outages
            SET status = 'Open'
            WHERE status = 'Reported'
        """)

        changed_outages = cursor.rowcount

        if changed_outages > 0:
            print(
                f"✓ Updated {changed_outages} outage(s): "
                "'Reported' → 'Open'."
            )
        else:
            print("✓ No 'Reported' outage statuses needed updating.")

        # ---------------------------------------------------------
        # 5. Update status history
        # ---------------------------------------------------------

        cursor.execute("""
            UPDATE status_updates
            SET old_status = 'Open'
            WHERE old_status = 'Reported'
        """)

        cursor.execute("""
            UPDATE status_updates
            SET new_status = 'Open'
            WHERE new_status = 'Reported'
        """)

        print("✓ Status history checked and updated.")

        # ---------------------------------------------------------
        # 6. Commit all changes
        # ---------------------------------------------------------

        db.commit()

        print("\nDatabase migration completed successfully!")

        return True

    except Exception as error:

        db.rollback()

        print("\nERROR: Database migration failed.")
        print("No changes from this migration were committed.")
        print(f"Details: {error}")

        return False

    finally:

        db.close()


def verify_database():
    """
    Verify that the required tables and columns now exist.
    """

    db = sqlite3.connect(DATABASE_NAME)
    cursor = db.cursor()

    print("\n" + "=" * 60)
    print("GRIDCARE-LITE DATABASE VERIFICATION")
    print("=" * 60)

    # ---------------------------------------------------------
    # List tables
    # ---------------------------------------------------------

    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
    """)

    tables = [row[0] for row in cursor.fetchall()]

    print("\nTables found:")

    for table in tables:
        print(f"  ✓ {table}")

    # ---------------------------------------------------------
    # Check substations.region
    # ---------------------------------------------------------

    print("\nChecking substations table:")

    if column_exists(cursor, "substations", "region"):
        print("  ✓ region column exists")
    else:
        print("  ✗ region column is missing")

    # ---------------------------------------------------------
    # Check outages.resolved_at
    # ---------------------------------------------------------

    print("\nChecking outages table:")

    if column_exists(cursor, "outages", "resolved_at"):
        print("  ✓ resolved_at column exists")
    else:
        print("  ✗ resolved_at column is missing")

    # ---------------------------------------------------------
    # Check lines table
    # ---------------------------------------------------------

    print("\nChecking lines table:")

    if table_exists(cursor, "lines"):
        print("  ✓ lines table exists")

        cursor.execute("PRAGMA table_info(lines)")
        columns = cursor.fetchall()

        print("  Columns:")

        for column in columns:
            print(f"    - {column[1]}")

    else:
        print("  ✗ lines table is missing")

    # ---------------------------------------------------------
    # Count existing data
    # ---------------------------------------------------------

    print("\nExisting data:")

    for table in [
        "users",
        "substations",
        "technicians",
        "outages",
        "work_orders",
        "maintenance",
        "status_updates",
        "complaints"
    ]:

        if table_exists(cursor, table):

            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]

            print(f"  {table}: {count} record(s)")

    # ---------------------------------------------------------
    # Check outage statuses
    # ---------------------------------------------------------

    print("\nOutage statuses:")

    cursor.execute("""
        SELECT status, COUNT(*)
        FROM outages
        GROUP BY status
    """)

    statuses = cursor.fetchall()

    if statuses:

        for status, count in statuses:
            print(f"  {status}: {count}")

    else:

        print("  No outages found.")

    db.close()

    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)


def main():

    print("=" * 60)
    print("GRIDCARE-LITE DATABASE MIGRATION")
    print("=" * 60)

    print("\nDatabase:", DATABASE_NAME)

    # ---------------------------------------------------------
    # Step 1: Backup
    # ---------------------------------------------------------

    print("\nStep 1: Creating backup...")

    backup_file = create_backup()

    if backup_file is None:
        return

    # ---------------------------------------------------------
    # Step 2: Update
    # ---------------------------------------------------------

    print("\nStep 2: Updating database...")

    success = update_database()

    if not success:
        print("\nMigration stopped.")
        return

    # ---------------------------------------------------------
    # Step 3: Verify
    # ---------------------------------------------------------

    print("\nStep 3: Verifying database...")

    verify_database()

    print("\n✓ GridCare-Lite database is ready.")
    print(f"✓ Original database preserved: {DATABASE_NAME}")
    print(f"✓ Backup available: {backup_file}")


if __name__ == "__main__":
    main()