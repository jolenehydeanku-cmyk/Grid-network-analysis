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

    try:
        cursor.execute("""
            INSERT INTO users (name, role, username, password)
            VALUES (?, ?, ?, ?)
        """, (name, role, username, password))

        db.commit()
        print("User added successfully!")

    except sqlite3.IntegrityError:
        print("Username already exists.")

    finally:
        db.close()


def get_users():
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT user_id, name, role, username
        FROM users
        ORDER BY user_id
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

    try:
        cursor.execute("""
            INSERT INTO substations (
                substation_code,
                name,
                location
            )
            VALUES (?, ?, ?)
        """, (substation_code, name, location))

        db.commit()
        print("Substation added successfully!")

    except sqlite3.IntegrityError:
        print("Substation could not be added.")

    finally:
        db.close()


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
        ORDER BY substation_id
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

    try:
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

        print("Outage reported successfully!")
        print("Outage ID:", outage_id)

        return outage_id

    finally:
        db.close()


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

    try:
        cursor.execute("""
            SELECT status
            FROM outages
            WHERE outage_id = ?
        """, (outage_id,))

        result = cursor.fetchone()

        if result is None:
            return False, "Outage not found."

        old_status = result[0]

        cursor.execute("""
            UPDATE outages
            SET status = ?
            WHERE outage_id = ?
        """, (new_status, outage_id))

        update_time = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

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

        return True, f"Outage #{outage_id} updated successfully."

    finally:
        db.close()


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

    changed = cursor.rowcount > 0

    db.close()

    return changed


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