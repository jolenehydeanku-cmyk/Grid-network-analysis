import sqlite3

DATABASE_NAME = "gridcare.db"

db = sqlite3.connect(DATABASE_NAME)
cursor = db.cursor()

# Add substation_id to the outages table
cursor.execute("""
    ALTER TABLE outages
    ADD COLUMN substation_id INTEGER
""")

# Link the existing outage to SUB-001
cursor.execute("""
    UPDATE outages
    SET substation_id = 1
    WHERE outage_id = 1
""")

db.commit()
db.close()

print("Database updated successfully!")
print("Outage #1 is now linked to Substation #1.")