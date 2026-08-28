import sqlite3
import os


DATABASE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "gridcare.db"
)

print("=" * 60)
print("DATABASE VERIFICATION")
print("=" * 60)

print()
print("Python is checking this database:")
print(DATABASE_FILE)

print()
print("Database exists:", os.path.exists(DATABASE_FILE))

if os.path.exists(DATABASE_FILE):
    print("Database size:", os.path.getsize(DATABASE_FILE), "bytes")

db = sqlite3.connect(DATABASE_FILE)
cursor = db.cursor()

print()
print("Actual SQLite database:")
print(db.execute("PRAGMA database_list").fetchall())

print()
print("TABLES:")

cursor.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    ORDER BY name
""")

tables = cursor.fetchall()

for table in tables:
    print(" -", table[0])

print()
print("LINES TABLE:")

cursor.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    AND name = 'lines'
""")

result = cursor.fetchone()

if result:
    print("EXISTS")
else:
    print("DOES NOT EXIST")

db.close()

print()
print("=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)