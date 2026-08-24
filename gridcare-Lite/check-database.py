import sqlite3

conn = sqlite3.connect("gridcare.db")
cursor = conn.cursor()

tables = [
    "users",
    "substations",
    "outages",
    "work_orders",
    "technicians",
    "maintenance",
    "status_updates",
    "complaints"
]

for table in tables:
    print("\n==============================")
    print("TABLE:", table)
    print("==============================")

    cursor.execute(f"PRAGMA table_info({table})")

    for column in cursor.fetchall():
        print(column)

conn.close()