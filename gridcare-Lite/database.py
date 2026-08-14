import sqlite3

DATABASE_NAME = "gridcare.db"


def create_tables():
    db = sqlite3.connect(DATABASE_NAME)
    cursor = db.cursor()

    cursor.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS substations (
        substation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        substation_code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        location TEXT NOT NULL
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS technicians (
        technician_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        specialization TEXT,
        availability TEXT DEFAULT 'Available'
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS outages (
        outage_id INTEGER PRIMARY KEY AUTOINCREMENT,
        substation_id INTEGER NOT NULL,
        description TEXT NOT NULL,
        reported_by INTEGER NOT NULL,
        date_reported TEXT NOT NULL,
        priority TEXT DEFAULT 'Medium',
        status TEXT DEFAULT 'Reported',
        FOREIGN KEY (substation_id) REFERENCES substations(substation_id),
        FOREIGN KEY (reported_by) REFERENCES users(user_id)
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS work_orders (
        work_order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        outage_id INTEGER NOT NULL,
        technician_id INTEGER,
        date_created TEXT NOT NULL,
        scheduled_date TEXT,
        status TEXT DEFAULT 'Pending',
        description TEXT,
        FOREIGN KEY (outage_id) REFERENCES outages(outage_id),
        FOREIGN KEY (technician_id) REFERENCES technicians(technician_id)
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS maintenance (
        maintenance_id INTEGER PRIMARY KEY AUTOINCREMENT,
        work_order_id INTEGER NOT NULL,
        technician_id INTEGER NOT NULL,
        start_time TEXT,
        end_time TEXT,
        action_taken TEXT,
        notes TEXT,
        FOREIGN KEY (work_order_id) REFERENCES work_orders(work_order_id),
        FOREIGN KEY (technician_id) REFERENCES technicians(technician_id)
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS status_updates (
        update_id INTEGER PRIMARY KEY AUTOINCREMENT,
        outage_id INTEGER NOT NULL,
        old_status TEXT,
        new_status TEXT NOT NULL,
        update_time TEXT NOT NULL,
        updated_by INTEGER,
        FOREIGN KEY (outage_id) REFERENCES outages(outage_id),
        FOREIGN KEY (updated_by) REFERENCES users(user_id)
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS complaints (
        complaint_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        customer_contact TEXT,
        complaint_text TEXT NOT NULL,
        outage_id INTEGER,
        date_reported TEXT NOT NULL,
        status TEXT DEFAULT 'Open',
        recorded_by INTEGER NOT NULL,
        FOREIGN KEY (outage_id) REFERENCES outages(outage_id),
        FOREIGN KEY (recorded_by) REFERENCES users(user_id)
    )""")

    db.commit()
    db.close()

    print("GridCare-Lite database created successfully!")
    print("8 tables are ready.")


def check_tables():
    db = sqlite3.connect(DATABASE_NAME)
    cursor = db.cursor()

    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name;
    """)

    tables = cursor.fetchall()

    print("\nTables in GridCare-Lite database:")

    for table in tables:
        print("-", table[0])

    db.close()


if __name__ == "__main__":
    create_tables()
    check_tables()







