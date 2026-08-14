import sqlite3
from datetime import datetime

DATABASE_NAME = "gridcare.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def connect_db():
    return sqlite3.connect(DATABASE_NAME)


# ============================================================
# USER OPERATIONS
# ============================================================

def add_user(name, role, username, password):
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO users (name, role, username, password)
        VALUES (?, ?, ?, ?)
    """, (name, role, username, password))

    db.commit()
    db.close()

    print("User added successfully!")


def get_users():
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT user_id, name, role, username
        FROM users
    """)

    users = cursor.fetchall()

    db.close()

    return users


# ============================================================
# SUBSTATION OPERATIONS
# ============================================================

def add_substation(substation_code, name, location):
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO substations (
            substation_code,
            name,
            location
        )
        VALUES (?, ?, ?)
    """, (substation_code, name, location))

    db.commit()
    db.close()

    print("Substation added successfully!")


def get_substations():
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT
            substation_id,
            substation_code,
            name,
            location
        FROM substations
    """)

    substations = cursor.fetchall()

    db.close()

    return substations


# ============================================================
# OUTAGE OPERATIONS
# ============================================================

def report_outage(
    substation_id,
    location,
    description,
    reported_by,
    date_reported,
    priority="Medium"
):
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO outages (
            substation_id,
            location,
            description,
            reported_by,
            date_reported,
            priority
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        substation_id,
        location,
        description,
        reported_by,
        date_reported,
        priority
    ))

    db.commit()

    outage_id = cursor.lastrowid

    db.close()

    print("Outage reported successfully!")
    print("Outage ID:", outage_id)

    return outage_id


def get_outages():
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT
            outage_id,
            substation_id,
            location,
            description,
            reported_by,
            date_reported,
            priority,
            status
        FROM outages
        ORDER BY outage_id
    """)

    outages = cursor.fetchall()

    db.close()

    return outages


# ============================================================
# OUTAGE STATUS OPERATIONS
# ============================================================

def update_outage_status(outage_id, new_status, updated_by):
    db = connect_db()
    cursor = db.cursor()

    # Get the current status
    cursor.execute("""
        SELECT status
        FROM outages
        WHERE outage_id = ?
    """, (outage_id,))

    result = cursor.fetchone()

    if result is None:
        print("Outage not found.")
        db.close()
        return

    old_status = result[0]

    # Update the outage status
    cursor.execute("""
        UPDATE outages
        SET status = ?
        WHERE outage_id = ?
    """, (new_status, outage_id))

    # Record the status change
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO status_updates (
            outage_id,
            old_status,
            new_status,
            update_time,
            updated_by
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        outage_id,
        old_status,
        new_status,
        update_time,
        updated_by
    ))

    db.commit()
    db.close()

    print("Outage status updated successfully!")
    print("Old status:", old_status)
    print("New status:", new_status)


def get_status_updates():
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT
            update_id,
            outage_id,
            old_status,
            new_status,
            update_time,
            updated_by
        FROM status_updates
        ORDER BY update_id
    """)

    updates = cursor.fetchall()

    db.close()

    return updates


# ============================================================
# TECHNICIAN OPERATIONS
# ============================================================

def add_technician(
    name,
    phone,
    specialization,
    availability="Available"
):
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO technicians (
            name,
            phone,
            specialization,
            availability
        )
        VALUES (?, ?, ?, ?)
    """, (
        name,
        phone,
        specialization,
        availability
    ))

    db.commit()

    technician_id = cursor.lastrowid

    db.close()

    print("Technician added successfully!")
    print("Technician ID:", technician_id)

    return technician_id


def get_technicians():
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT
            technician_id,
            name,
            phone,
            specialization,
            availability
        FROM technicians
        ORDER BY technician_id
    """)

    technicians = cursor.fetchall()

    db.close()

    return technicians


# ============================================================
# WORK ORDER OPERATIONS
# ============================================================

def create_work_order(
    outage_id,
    technician_id,
    description,
    date_created
):
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO work_orders (
            outage_id,
            technician_id,
            date_created,
            status,
            description
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        outage_id,
        technician_id,
        date_created,
        "Pending",
        description
    ))

    db.commit()

    work_order_id = cursor.lastrowid

    db.close()

    print("Work order created successfully!")
    print("Work Order ID:", work_order_id)

    return work_order_id


def get_work_orders():
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT
            work_order_id,
            outage_id,
            technician_id,
            date_created,
            status,
            description
        FROM work_orders
        ORDER BY work_order_id
    """)

    work_orders = cursor.fetchall()

    db.close()

    return work_orders


def update_work_order_status(work_order_id, new_status):
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE work_orders
        SET status = ?
        WHERE work_order_id = ?
    """, (
        new_status,
        work_order_id
    ))

    db.commit()

    db.close()

    print("Work order status updated successfully!")


# ============================================================
# MAINTENANCE OPERATIONS
# ============================================================

def record_maintenance(
    work_order_id,
    technician_id,
    start_time,
    end_time,
    action_taken,
    notes
):
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO maintenance (
            work_order_id,
            technician_id,
            start_time,
            end_time,
            action_taken,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        work_order_id,
        technician_id,
        start_time,
        end_time,
        action_taken,
        notes
    ))

    db.commit()

    maintenance_id = cursor.lastrowid

    db.close()

    print("Maintenance record created successfully!")
    print("Maintenance ID:", maintenance_id)

    return maintenance_id


def get_maintenance_records():
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT
            maintenance_id,
            work_order_id,
            technician_id,
            start_time,
            end_time,
            action_taken,
            notes
        FROM maintenance
        ORDER BY maintenance_id
    """)

    maintenance_records = cursor.fetchall()

    db.close()

    return maintenance_records


# ============================================================
# MAIN TEST PROGRAM
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # USERS
    # --------------------------------------------------------

    print("\nUsers in GridCare-Lite:")

    users = get_users()

    for user in users:
        print(user)

    # --------------------------------------------------------
    # SUBSTATIONS
    # --------------------------------------------------------

    print("\nSubstations in GridCare-Lite:")

    substations = get_substations()

    for substation in substations:
        print(substation)

    # --------------------------------------------------------
    # OUTAGES
    # --------------------------------------------------------

    print("\nOutages in GridCare-Lite:")

    outages = get_outages()

    for outage in outages:
        print(outage)

    # --------------------------------------------------------
    # TECHNICIANS
    # --------------------------------------------------------

    print("\nTechnicians in GridCare-Lite:")

    technicians = get_technicians()

    for technician in technicians:
        print(technician)

    # --------------------------------------------------------
    # WORK ORDERS
    # --------------------------------------------------------

    print("\nWork orders in GridCare-Lite:")

    work_orders = get_work_orders()

    for work_order in work_orders:
        print(work_order)

    # --------------------------------------------------------
    # UPDATE AN EXISTING WORK ORDER
    # --------------------------------------------------------

    print("\nUpdating Work Order #1 to In Progress...")

    update_work_order_status(
        1,
        "In Progress"
    )

    # --------------------------------------------------------
    # UPDATE OUTAGE STATUS
    # --------------------------------------------------------

    print("\nUpdating Outage #1 to In Progress...")

    update_outage_status(
        1,
        "In Progress",
        1
    )

    # --------------------------------------------------------
    # RECORD MAINTENANCE
    # --------------------------------------------------------

    print("\nRecording maintenance for Work Order #1...")

    maintenance_id = record_maintenance(
        1,
        1,
        "2026-08-10 10:00:00",
        "2026-08-10 14:00:00",
        "Inspected the electrical equipment and repaired the faulty connection.",
        "Equipment tested successfully after the repair."
    )

    # --------------------------------------------------------
    # DISPLAY MAINTENANCE
    # --------------------------------------------------------

    print("\nMaintenance records in GridCare-Lite:")

    maintenance_records = get_maintenance_records()

    for record in maintenance_records:
        print(record)

    # --------------------------------------------------------
    # COMPLETE WORK ORDER
    # --------------------------------------------------------

    print("\nUpdating Work Order #1 to Completed...")

    update_work_order_status(
        1,
        "Completed"
    )

    # --------------------------------------------------------
    # RESOLVE OUTAGE
    # --------------------------------------------------------

    print("\nUpdating Outage #1 to Resolved...")

    update_outage_status(
        1,
        "Resolved",
        1
    )

    # --------------------------------------------------------
    # DISPLAY FINAL STATUS
    # --------------------------------------------------------

    print("\nFinal outage information:")

    outages = get_outages()

    for outage in outages:
        print(outage)

    print("\nFinal work order information:")

    work_orders = get_work_orders()

    for work_order in work_orders:
        print(work_order)

    print("\nStatus update history:")

    status_updates = get_status_updates()

    for update in status_updates:
        print(update)