import sqlite3

DATABASE_NAME = "gridcare.db"

db = sqlite3.connect(DATABASE_NAME)
cursor = db.cursor()

tables = cursor.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    AND name NOT LIKE 'sqlite_%'
    ORDER BY name
""").fetchall()

print("GridCare-Lite database data:")
print()

for table in tables:
    table_name = table[0]

    print(f"--- {table_name} ---")

    rows = cursor.execute(
        f"SELECT * FROM {table_name}"
    ).fetchall()

    if rows:
        for row in rows:
            print(row)
    else:
        print("(empty)")

    print()

db.close()