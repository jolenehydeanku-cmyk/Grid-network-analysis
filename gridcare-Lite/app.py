import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import hashlib


DATABASE_NAME = "gridcare.db"


# ============================================================
# DATABASE CONNECTION AND SETUP
# ============================================================

def connect_db():
    return sqlite3.connect(DATABASE_NAME)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def setup_database():
    """
    Makes small compatibility changes to the existing database.
    Existing data is preserved.
    """

    db = connect_db()
    cursor = db.cursor()

    # --------------------------------------------------------
    # Add password_hash if it does not already exist
    # --------------------------------------------------------

    cursor.execute("PRAGMA table_info(users)")
    user_columns = [row[1] for row in cursor.fetchall()]

    if "password_hash" not in user_columns:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN password_hash TEXT"
        )

    # --------------------------------------------------------
    # Add scheduled_date to work_orders
    # --------------------------------------------------------

    cursor.execute("PRAGMA table_info(work_orders)")
    work_order_columns = [row[1] for row in cursor.fetchall()]

    if "scheduled_date" not in work_order_columns:
        cursor.execute(
            "ALTER TABLE work_orders ADD COLUMN scheduled_date TEXT"
        )

    # --------------------------------------------------------
    # Add user_id to technicians
    # This connects a technician account to a technician record.
    # --------------------------------------------------------

    cursor.execute("PRAGMA table_info(technicians)")
    technician_columns = [row[1] for row in cursor.fetchall()]

    if "user_id" not in technician_columns:
        cursor.execute(
            "ALTER TABLE technicians ADD COLUMN user_id INTEGER"
        )

    # --------------------------------------------------------
    # Make sure complaints table exists
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS complaints (
            complaint_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            customer_contact TEXT,
            complaint_text TEXT NOT NULL,
            outage_id INTEGER,
            date_reported TEXT NOT NULL,
            status TEXT DEFAULT 'Open',
            recorded_by INTEGER NOT NULL
        )
        """
    )

    # --------------------------------------------------------
    # Convert old role names to lecturer-required roles
    # --------------------------------------------------------

    cursor.execute(
        """
        UPDATE users
        SET role = 'admin'
        WHERE LOWER(role) = 'manager'
        """
    )

    cursor.execute(
        """
        UPDATE users
        SET role = 'customer_service'
        WHERE LOWER(role) = 'customer'
        """
    )

    # --------------------------------------------------------
    # Create password hashes for existing users
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT user_id, password
        FROM users
        WHERE password_hash IS NULL
        """
    )

    users_without_hash = cursor.fetchall()

    for user_id, password in users_without_hash:
        if password is not None:
            cursor.execute(
                """
                UPDATE users
                SET password_hash = ?
                WHERE user_id = ?
                """,
                (
                    hash_password(password),
                    user_id
                )
            )

    db.commit()
    db.close()


# ============================================================
# LOGIN WINDOW
# ============================================================

class LoginWindow:

    def __init__(self, root):

        self.root = root

        self.root.title("GridCare-Lite - Login")
        self.root.geometry("480x420")
        self.root.resizable(False, False)

        frame = ttk.Frame(
            self.root,
            padding=30
        )

        frame.pack(expand=True)

        ttk.Label(
            frame,
            text="GRIDCARE-LITE",
            font=("Arial", 22, "bold")
        ).grid(
            row=0,
            column=0,
            columnspan=2,
            pady=10
        )

        ttk.Label(
            frame,
            text="Outage and Maintenance Management System"
        ).grid(
            row=1,
            column=0,
            columnspan=2,
            pady=10
        )

        ttk.Label(
            frame,
            text="Username:"
        ).grid(
            row=2,
            column=0,
            sticky="w",
            pady=8
        )

        self.username_entry = ttk.Entry(
            frame,
            width=30
        )

        self.username_entry.grid(
            row=2,
            column=1,
            pady=8
        )

        ttk.Label(
            frame,
            text="Password:"
        ).grid(
            row=3,
            column=0,
            sticky="w",
            pady=8
        )

        self.password_entry = ttk.Entry(
            frame,
            width=30,
            show="*"
        )

        self.password_entry.grid(
            row=3,
            column=1,
            pady=8
        )

        ttk.Button(
            frame,
            text="Log In",
            command=self.login
        ).grid(
            row=4,
            column=0,
            columnspan=2,
            pady=10
        )

        ttk.Button(
            frame,
            text="Create Account",
            command=self.open_register
        ).grid(
            row=5,
            column=0,
            columnspan=2,
            pady=10
        )

        self.username_entry.focus()

        self.root.bind(
            "<Return>",
            lambda event: self.login()
        )

    def open_register(self):

        RegisterWindow(self.root)

    def login(self):

        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:

            messagebox.showerror(
                "Login Failed",
                "Please enter both username and password."
            )

            return

        db = connect_db()
        cursor = db.cursor()

        cursor.execute(
            """
            SELECT
                user_id,
                name,
                role,
                username,
                password_hash,
                password
            FROM users
            WHERE username = ?
            """,
            (username,)
        )

        user = cursor.fetchone()

        if user is None:

            db.close()

            messagebox.showerror(
                "Login Failed",
                "Incorrect username or password."
            )

            return

        user_id = user[0]
        name = user[1]
        role = user[2]
        stored_hash = user[4]
        old_password = user[5]

        password_valid = False

        # New password verification
        if stored_hash:
            password_valid = (
                hash_password(password) == stored_hash
            )

        # Compatibility with old database passwords
        if not password_valid and old_password == password:

            password_valid = True

            cursor.execute(
                """
                UPDATE users
                SET password_hash = ?
                WHERE user_id = ?
                """,
                (
                    hash_password(password),
                    user_id
                )
            )

            db.commit()

        db.close()

        if not password_valid:

            messagebox.showerror(
                "Login Failed",
                "Incorrect username or password."
            )

            return

        user_data = (
            user_id,
            name,
            role,
            username
        )

        for widget in self.root.winfo_children():
            widget.destroy()

        Dashboard(
            self.root,
            user_data
        )


# ============================================================
# REGISTER WINDOW
# ============================================================

class RegisterWindow:

    def __init__(self, parent):

        self.window = tk.Toplevel(parent)

        self.window.title(
            "GridCare-Lite - Create Account"
        )

        self.window.geometry("480x450")
        self.window.resizable(False, False)

        frame = ttk.Frame(
            self.window,
            padding=30
        )

        frame.pack(
            fill="both",
            expand=True
        )

        ttk.Label(
            frame,
            text="CREATE ACCOUNT",
            font=("Arial", 20, "bold")
        ).grid(
            row=0,
            column=0,
            columnspan=2,
            pady=15
        )

        ttk.Label(
            frame,
            text="Name:"
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=8
        )

        self.name_entry = ttk.Entry(
            frame,
            width=30
        )

        self.name_entry.grid(
            row=1,
            column=1,
            pady=8
        )

        ttk.Label(
            frame,
            text="Username:"
        ).grid(
            row=2,
            column=0,
            sticky="w",
            pady=8
        )

        self.username_entry = ttk.Entry(
            frame,
            width=30
        )

        self.username_entry.grid(
            row=2,
            column=1,
            pady=8
        )

        ttk.Label(
            frame,
            text="Password:"
        ).grid(
            row=3,
            column=0,
            sticky="w",
            pady=8
        )

        self.password_entry = ttk.Entry(
            frame,
            width=30,
            show="*"
        )

        self.password_entry.grid(
            row=3,
            column=1,
            pady=8
        )

        ttk.Label(
            frame,
            text="Role:"
        ).grid(
            row=4,
            column=0,
            sticky="w",
            pady=8
        )

        self.role_combo = ttk.Combobox(
            frame,
            values=[
                "engineer",
                "technician",
                "customer_service"
            ],
            state="readonly",
            width=28
        )

        self.role_combo.set(
            "customer_service"
        )

        self.role_combo.grid(
            row=4,
            column=1,
            pady=8
        )

        ttk.Label(
            frame,
            text="Administrator accounts can only be created by an administrator.",
            wraplength=350
        ).grid(
            row=5,
            column=0,
            columnspan=2,
            pady=10
        )

        ttk.Button(
            frame,
            text="Register",
            command=self.register
        ).grid(
            row=6,
            column=0,
            columnspan=2,
            pady=15
        )

    def register(self):

        name = self.name_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        role = self.role_combo.get()

        if not name or not username or not password or not role:

            messagebox.showerror(
                "Registration Failed",
                "Please complete all fields."
            )

            return

        db = connect_db()
        cursor = db.cursor()

        cursor.execute(
            """
            SELECT user_id
            FROM users
            WHERE username = ?
            """,
            (username,)
        )

        if cursor.fetchone() is not None:

            db.close()

            messagebox.showerror(
                "Registration Failed",
                "That username is already in use."
            )

            return

        cursor.execute(
            """
            INSERT INTO users (
                name,
                role,
                username,
                password,
                password_hash
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                name,
                role,
                username,
                password,
                hash_password(password)
            )
        )

        db.commit()
        db.close()

        messagebox.showinfo(
            "Registration Successful",
            "Your account has been created successfully."
        )

        self.window.destroy()


# ============================================================
# DASHBOARD
# ============================================================

class Dashboard:

    def __init__(self, root, user):

        self.root = root
        self.user = user

        self.user_id = user[0]
        self.name = user[1]
        self.role = user[2]
        self.username = user[3]

        self.root.title(
            f"GridCare-Lite - {self.get_role_name()} Dashboard"
        )

        self.root.geometry("950x700")

        self.build_dashboard()

    def get_role_name(self):

        role_names = {
            "admin": "Administrator",
            "engineer": "Engineer",
            "technician": "Technician",
            "customer_service": "Customer Service"
        }

        return role_names.get(
            self.role,
            self.role
        )

    def build_dashboard(self):

        header = ttk.Frame(
            self.root,
            padding=20
        )

        header.pack(
            fill="x"
        )

        ttk.Label(
            header,
            text="GRIDCARE-LITE",
            font=("Arial", 22, "bold")
        ).pack(
            side="left"
        )

        ttk.Label(
            header,
            text=f"Welcome, {self.name} ({self.get_role_name()})"
        ).pack(
            side="right"
        )

        content = ttk.Frame(
            self.root,
            padding=20
        )

        content.pack(
            fill="both",
            expand=True
        )

        ttk.Label(
            content,
            text=f"{self.get_role_name()} Dashboard",
            font=("Arial", 18, "bold")
        ).pack(
            pady=15
        )

        buttons_frame = ttk.Frame(content)

        buttons_frame.pack(pady=10)

        # ====================================================
        # ADMINISTRATOR
        # ====================================================

        if self.role == "admin":

            self.add_button(
                buttons_frame,
                "View Outages",
                self.open_outages,
                0,
                0
            )

            self.add_button(
                buttons_frame,
                "Report New Outage",
                self.report_outage,
                0,
                1
            )

            self.add_button(
                buttons_frame,
                "Work Orders",
                self.open_work_orders,
                1,
                0
            )

            self.add_button(
                buttons_frame,
                "Technicians",
                self.open_technicians,
                1,
                1
            )

            self.add_button(
                buttons_frame,
                "Maintenance",
                self.open_maintenance,
                2,
                0
            )

            self.add_button(
                buttons_frame,
                "Complaints",
                self.open_complaints,
                2,
                1
            )

            self.add_button(
                buttons_frame,
                "User Management",
                self.open_users,
                3,
                0
            )

            self.add_button(
                buttons_frame,
                "Reports",
                self.open_reports,
                3,
                1
            )

        # ====================================================
        # ENGINEER
        # ====================================================

        elif self.role == "engineer":

            self.add_button(
                buttons_frame,
                "View Outages",
                self.open_outages,
                0,
                0
            )

            self.add_button(
                buttons_frame,
                "Report New Outage",
                self.report_outage,
                0,
                1
            )

            self.add_button(
                buttons_frame,
                "Update Outage Status",
                self.open_outages,
                1,
                0
            )

            self.add_button(
                buttons_frame,
                "Reports",
                self.open_reports,
                1,
                1
            )

        # ====================================================
        # TECHNICIAN
        # ====================================================

        elif self.role == "technician":

            self.add_button(
                buttons_frame,
                "My Work Orders",
                self.open_technician_work_orders,
                0,
                0
            )

            self.add_button(
                buttons_frame,
                "View Outages",
                self.open_outages,
                0,
                1
            )

            self.add_button(
                buttons_frame,
                "Maintenance",
                self.open_maintenance,
                1,
                0
            )

        # ====================================================
        # CUSTOMER SERVICE
        # ====================================================

        elif self.role == "customer_service":

            self.add_button(
                buttons_frame,
                "View Outages",
                self.open_outages,
                0,
                0
            )

            self.add_button(
                buttons_frame,
                "Log Customer Complaint",
                self.open_complaint_form,
                0,
                1
            )

            self.add_button(
                buttons_frame,
                "View Complaints",
                self.open_complaints,
                1,
                0
            )

        # ====================================================
        # REFRESH / LOGOUT
        # ====================================================

        self.add_button(
            buttons_frame,
            "Refresh Dashboard",
            self.refresh_dashboard,
            4,
            0
        )

        self.add_button(
            buttons_frame,
            "Logout",
            self.logout,
            4,
            1
        )

        self.summary_frame = ttk.LabelFrame(
            content,
            text="System Summary",
            padding=20
        )

        self.summary_frame.pack(
            fill="x",
            pady=15
        )

        self.load_summary()

    def add_button(
        self,
        parent,
        text,
        command,
        row,
        column
    ):

        ttk.Button(
            parent,
            text=text,
            width=25,
            command=command
        ).grid(
            row=row,
            column=column,
            padx=10,
            pady=8
        )

    def load_summary(self):

        for widget in self.summary_frame.winfo_children():
            widget.destroy()

        db = connect_db()
        cursor = db.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM outages"
        )

        total_outages = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM outages
            WHERE status != 'Resolved'
            """
        )

        open_outages = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM work_orders"
        )

        total_work_orders = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM technicians"
        )

        total_technicians = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM maintenance"
        )

        total_maintenance = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM complaints"
        )

        total_complaints = cursor.fetchone()[0]

        # Average resolution time in days
        cursor.execute(
            """
            SELECT AVG(
                julianday(
                    datetime(
                        date_reported || ' 00:00:00'
                    )
                )
            )
            FROM outages
            WHERE status = 'Resolved'
            """
        )

        # Calculate average resolution from status history
        cursor.execute(
            """
            SELECT outage_id
            FROM outages
            WHERE status = 'Resolved'
            """
        )

        resolved_ids = [
            row[0] for row in cursor.fetchall()
        ]

        resolution_times = []

        for outage_id in resolved_ids:

            cursor.execute(
                """
                SELECT
                    o.date_reported,
                    MAX(s.update_time)
                FROM outages o
                JOIN status_updates s
                    ON o.outage_id = s.outage_id
                WHERE o.outage_id = ?
                AND s.new_status = 'Resolved'
                """,
                (outage_id,)
            )

            result = cursor.fetchone()

            if result and result[0] and result[1]:

                try:

                    start = datetime.strptime(
                        result[0],
                        "%Y-%m-%d"
                    )

                    end = datetime.strptime(
                        result[1],
                        "%Y-%m-%d %H:%M:%S"
                    )

                    resolution_times.append(
                        (end - start).total_seconds()
                        / 86400
                    )

                except ValueError:
                    pass

        db.close()

        if resolution_times:

            average_resolution = (
                sum(resolution_times)
                / len(resolution_times)
            )

            average_text = (
                f"{average_resolution:.2f} days"
            )

        else:

            average_text = "No resolved outages yet"

        summary = [
            f"Total Outages: {total_outages}",
            f"Open Outages: {open_outages}",
            f"Work Orders: {total_work_orders}",
            f"Technicians: {total_technicians}",
            f"Maintenance Records: {total_maintenance}",
            f"Customer Complaints: {total_complaints}",
            f"Average Resolution Time: {average_text}"
        ]

        for item in summary:

            ttk.Label(
                self.summary_frame,
                text=item
            ).pack(
                anchor="w",
                pady=3
            )

    def refresh_dashboard(self):

        self.load_summary()

        messagebox.showinfo(
            "Dashboard Refreshed",
            "Dashboard information has been refreshed."
        )

    def open_outages(self):

        OutageWindow(
            self.root,
            self.user
        )

    def report_outage(self):

        ReportOutageWindow(
            self.root,
            self.user,
            self.load_summary
        )

    def open_work_orders(self):

        WorkOrderWindow(
            self.root,
            self.user
        )

    def open_technicians(self):

        TechnicianWindow(
            self.root
        )

    def open_maintenance(self):

        MaintenanceWindow(
            self.root
        )

    def open_complaints(self):

        ComplaintWindow(
            self.root,
            self.user
        )

    def open_complaint_form(self):

        ComplaintEntryWindow(
            self.root,
            self.user,
            self.refresh_dashboard
        )

    def open_users(self):

        UserManagementWindow(
            self.root
        )

    def open_reports(self):

        ReportsWindow(
            self.root
        )

    def open_technician_work_orders(self):

        TechnicianWorkOrderWindow(
            self.root,
            self.user
        )

    def logout(self):

        answer = messagebox.askyesno(
            "Logout",
            "Are you sure you want to logout?"
        )

        if answer:

            for widget in self.root.winfo_children():
                widget.destroy()

            LoginWindow(self.root)


# ============================================================
# OUTAGE WINDOW
# ============================================================

class OutageWindow:

    def __init__(self, parent, user):

        self.user = user

        self.window = tk.Toplevel(parent)

        self.window.title(
            "GridCare-Lite - Outages"
        )

        self.window.geometry("1150x600")

        ttk.Label(
            self.window,
            text="Outage Management",
            font=("Arial", 18, "bold")
        ).pack(pady=15)

        columns = (
            "id",
            "substation",
            "region",
            "location",
            "description",
            "reported_by",
            "date",
            "priority",
            "status"
        )

        self.tree = ttk.Treeview(
            self.window,
            columns=columns,
            show="headings"
        )

        headings = {
            "id": "Outage ID",
            "substation": "Substation",
            "region": "Region",
            "location": "Location",
            "description": "Description",
            "reported_by": "Reported By",
            "date": "Date",
            "priority": "Severity",
            "status": "Status"
        }

        for column in columns:

            self.tree.heading(
                column,
                text=headings[column]
            )

            self.tree.column(
                column,
                width=105
            )

        self.tree.column(
            "description",
            width=240
        )

        self.tree.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=10
        )

        buttons = ttk.Frame(self.window)

        buttons.pack(pady=10)

        if user[2] in (
            "admin",
            "engineer"
        ):

            ttk.Button(
                buttons,
                text="Update Status",
                command=self.update_status
            ).grid(
                row=0,
                column=0,
                padx=5
            )

        ttk.Button(
            buttons,
            text="Refresh",
            command=self.load_outages
        ).grid(
            row=0,
            column=1,
            padx=5
        )

        self.load_outages()

    def load_outages(self):

        for item in self.tree.get_children():
            self.tree.delete(item)

        db = connect_db()
        cursor = db.cursor()

        cursor.execute(
            """
            SELECT
                o.outage_id,
                o.substation_id,
                s.location,
                o.location,
                o.description,
                o.reported_by,
                o.date_reported,
                o.priority,
                o.status
            FROM outages o
            LEFT JOIN substations s
                ON o.substation_id = s.substation_id
            ORDER BY o.outage_id
            """
        )

        outages = cursor.fetchall()

        db.close()

        for outage in outages:

            self.tree.insert(
                "",
                "end",
                values=outage
            )

    def update_status(self):

        selected = self.tree.selection()

        if not selected:

            messagebox.showerror(
                "Error",
                "Please select an outage first."
            )

            return

        values = self.tree.item(
            selected[0],
            "values"
        )

        outage_id = values[0]
        current_status = values[8]

        StatusWindow(
            self.window,
            outage_id,
            current_status,
            self.user[0],
            self.load_outages
        )


# ============================================================
# STATUS UPDATE WINDOW
# ============================================================

class StatusWindow:

    def __init__(
        self,
        parent,
        outage_id,
        current_status,
        user_id,
        refresh_callback
    ):

        self.outage_id = outage_id
        self.user_id = user_id
        self.refresh_callback = refresh_callback

        self.window = tk.Toplevel(parent)

        self.window.title(
            "Update Outage Status"
        )

        self.window.geometry("400x250")

        frame = ttk.Frame(
            self.window,
            padding=25
        )

        frame.pack(
            fill="both",
            expand=True
        )

        ttk.Label(
            frame,
            text=f"Outage #{outage_id}",
            font=("Arial", 16, "bold")
        ).pack(pady=10)

        ttk.Label(
            frame,
            text=f"Current Status: {current_status}"
        ).pack(pady=5)

        ttk.Label(
            frame,
            text="New Status:"
        ).pack(anchor="w")

        self.status_combo = ttk.Combobox(
            frame,
            values=[
                "Reported",
                "In Progress",
                "Resolved"
            ],
            state="readonly"
        )

        self.status_combo.pack(
            fill="x",
            pady=5
        )

        self.status_combo.set(current_status)

        ttk.Button(
            frame,
            text="Update Status",
            command=self.submit
        ).pack(pady=15)

    def submit(self):

        new_status = self.status_combo.get()

        if not new_status:
            return

        db = connect_db()
        cursor = db.cursor()

        cursor.execute(
            """
            SELECT status
            FROM outages
            WHERE outage_id = ?
            """,
            (self.outage_id,)
        )

        result = cursor.fetchone()

        if result is None:

            db.close()

            messagebox.showerror(
                "Error",
                "Outage not found."
            )

            return

        old_status = result[0]

        if old_status == new_status:

            db.close()

            messagebox.showinfo(
                "No Change",
                "The outage already has this status."
            )

            return

        update_time = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        cursor.execute(
            """
            UPDATE outages
            SET status = ?
            WHERE outage_id = ?
            """,
            (
                new_status,
                self.outage_id
            )
        )

        cursor.execute(
            """
            INSERT INTO status_updates (
                outage_id,
                old_status,
                new_status,
                update_time,
                updated_by
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                self.outage_id,
                old_status,
                new_status,
                update_time,
                self.user_id
            )
        )

        db.commit()
        db.close()

        messagebox.showinfo(
            "Success",
            "Outage status updated successfully."
        )

        self.refresh_callback()
        self.window.destroy()


# ============================================================
# REPORT OUTAGE WINDOW
# ============================================================

class ReportOutageWindow:

    def __init__(
        self,
        parent,
        user,
        refresh_callback
    ):

        self.user = user
        self.refresh_callback = refresh_callback

        self.window = tk.Toplevel(parent)

        self.window.title(
            "GridCare-Lite - Report Outage"
        )

        self.window.geometry("520x550")

        frame = ttk.Frame(
            self.window,
            padding=25
        )

        frame.pack(
            fill="both",
            expand=True
        )

        ttk.Label(
            frame,
            text="Report New Outage",
            font=("Arial", 18, "bold")
        ).pack(pady=10)

        ttk.Label(
            frame,
            text="Substation:"
        ).pack(anchor="w")

        self.substation_combo = ttk.Combobox(
            frame,
            state="readonly",
            width=45
        )

        self.substation_combo.pack(
            fill="x",
            pady=5
        )

        self.substation_data = []

        self.load_substations()

        ttk.Label(
            frame,
            text="Location:"
        ).pack(anchor="w")

        self.location_entry = ttk.Entry(frame)

        self.location_entry.pack(
            fill="x",
            pady=5
        )

        ttk.Label(
            frame,
            text="Description:"
        ).pack(anchor="w")

        self.description_entry = tk.Text(
            frame,
            height=5
        )

        self.description_entry.pack(
            fill="x",
            pady=5
        )

        ttk.Label(
            frame,
            text="Severity:"
        ).pack(anchor="w")

        self.priority_combo = ttk.Combobox(
            frame,
            values=[
                "Low",
                "Medium",
                "High",
                "Critical"
            ],
            state="readonly"
        )

        self.priority_combo.set("Medium")

        self.priority_combo.pack(
            fill="x",
            pady=5
        )

        ttk.Button(
            frame,
            text="Report Outage",
            command=self.submit
        ).pack(pady=20)

    def load_substations(self):

        db = connect_db()
        cursor = db.cursor()

        cursor.execute(
            """
            SELECT
                substation_id,
                substation_code,
                name,
                location
            FROM substations
            ORDER BY substation_id
            """
        )

        self.substation_data = cursor.fetchall()

        db.close()

        values = []

        for substation in self.substation_data:

            values.append(
                f"{substation[1]} - "
                f"{substation[2]} - "
                f"{substation[3]}"
            )

        self.substation_combo["values"] = values

        if values:
            self.substation_combo.current(0)

    def submit(self):

        selected_index = self.substation_combo.current()

        if selected_index == -1:

            messagebox.showerror(
                "Error",
                "Please select a substation."
            )

            return

        location = self.location_entry.get().strip()

        description = (
            self.description_entry
            .get("1.0", "end")
            .strip()
        )

        priority = self.priority_combo.get()

        if not location or not description:

            messagebox.showerror(
                "Error",
                "Please complete all required fields."
            )

            return

        substation_id = self.substation_data[
            selected_index
        ][0]

        date_reported = datetime.now().strftime(
            "%Y-%m-%d"
        )

        db = connect_db()
        cursor = db.cursor()

        cursor.execute(
            """
            INSERT INTO outages (
                substation_id,
                location,
                description,
                reported_by,
                date_reported,
                priority
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                substation_id,
                location,
                description,
                self.user[0],
                date_reported,
                priority
            )
        )

        db.commit()

        outage_id = cursor.lastrowid

        db.close()

        messagebox.showinfo(
            "Success",
            f"Outage #{outage_id} reported successfully."
        )

        self.refresh_callback()
        self.window.destroy()


# ============================================================
# WORK ORDER WINDOW
# ============================================================

class WorkOrderWindow:

    def __init__(self, parent, user):

        self.user = user

        self.window = tk.Toplevel(parent)

        self.window.title(
            "GridCare-Lite - Work Orders"
        )

        self.window.geometry("1100x600")

        ttk.Label(
            self.window,
            text="Work Order Management",
            font=("Arial", 18, "bold")
        ).pack(pady=15)

        columns = (
            "id",
            "outage",
            "technician",
            "date",
            "scheduled",
            "status",
            "description"
        )

        self.tree = ttk.Treeview(
            self.window,
            columns=columns,
            show="headings"
        )

        headings = {
            "id": "Work Order",
            "outage": "Outage",
            "technician": "Technician",
            "date": "Created",
            "scheduled": "Scheduled Date",
            "status": "Status",
            "description": "Description"
        }

        for column in columns:

            self.tree.heading(
                column,
                text=headings[column]
            )

            self.tree.column(
                column,
                width=125
            )

        self.tree.column(
            "description",
            width=250
        )

        self.tree.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=10
        )

        buttons = ttk.Frame(self.window)

        buttons.pack(pady=10)

        ttk.Button(
            buttons,
            text="Create / Assign Work Order",
            command=self.create_work_order
        ).grid(
            row=0,
            column=0,
            padx=5
        )

        ttk.Button(
            buttons,
            text="Update Status",
            command=self.update_status
        ).grid(
            row=0,
            column=1,
            padx=5
        )

        ttk.Button(
            buttons,
            text="Record Maintenance",
            command=self.record_maintenance
        ).grid(
            row=0,
            column=2,
            padx=5
        )

        ttk.Button(
            buttons,
            text="Refresh",
            command=self.load_work_orders
        ).grid(
            row=0,
            column=3,
            padx=5
        )

        self.load_work_orders()

    def load_work_orders(self):

        for item in self.tree.get_children():
            self.tree.delete(item)

        db = connect_db()
        cursor = db.cursor()

        cursor.execute(
            """
            SELECT
                w.work_order_id,
                w.outage_id,
                COALESCE(t.name, 'Unassigned'),
                w.date_created,
                COALESCE(w.scheduled_date, ''),
                w.status,
                w.description
            FROM work_orders w
            LEFT JOIN technicians t
                ON w.technician_id = t.technician_id
            ORDER BY w.work_order_id
            """
        )

        work_orders = cursor.fetchall()

        db.close()

        for work_order in work_orders:

            self.tree.insert(
                "",
                "end",
                values=work_order
            )

    def create_work_order(self):

        CreateWorkOrderWindow(
            self.window,
            self.load_work_orders
        )

    def update_status(self):

        selected = self.tree.selection()

        if not selected:

            messagebox.showerror(
                "Error",
                "Please select a work order first."
            )

            return

        values = self.tree.item(
            selected[0],
            "values"
        )

        WorkOrderStatusWindow(
            self.window,
            values[0],
            values[5],
            self.load_work_orders
        )

    def record_maintenance(self):

        selected = self.tree.selection()

        if not selected:

            messagebox.showerror(
                "Error",
                "Please select a work order first."
            )

            return

        values = self.tree.item(
            selected[0],
            "values"
        )

        MaintenanceEntryWindow(
            self.window,
            values[0],
            self.load_work_orders
        )


# ============================================================
# CREATE WORK ORDER WINDOW
# ============================================================

class CreateWorkOrderWindow:

    def __init__(self, parent, refresh_callback):

        self.refresh_callback = refresh_callback

        self.window = tk.Toplevel(parent)

        self.window.title(
            "Create Work Order"
        )

        self.window.geometry("520x550")

        frame = ttk.Frame(
            self.window,
            padding=25
        )

        frame.pack(
            fill="both",
            expand=True
        )

        ttk.Label(
            frame,
            text="Create Work Order",
            font=("Arial", 18, "bold")
        ).pack(pady=10)

        ttk.Label(
            frame,
            text="Outage:"
        ).pack(anchor="w")

        self.outage_combo = ttk.Combobox(
            frame,
            state="readonly",
            width=45
        )

        self.outage_combo.pack(
            fill="x",
            pady=5
        )

        self.outage_data = []

        self.load_outages()

        ttk.Label(
            frame,
            text="Technician:"
        ).pack(anchor="w")

        self.technician_combo = ttk.Combobox(
            frame,
            state="readonly",
            width=45
        )

        self.technician_combo.pack(
            fill="x",
            pady=5
        )

        self.technician_data = []

        self.load_technicians()

        ttk.Label(
            frame,
            text="Scheduled Date (YYYY-MM-DD):"
        ).pack(anchor="w")

        self.scheduled_entry = ttk.Entry(frame)

        self.scheduled_entry.pack(
            fill="x",
            pady=5
        )

        self.scheduled_entry.insert(
            0,
            datetime.now().strftime("%Y-%m-%d")
        )

        ttk.Label(
            frame,
            text="Work Description:"
        ).pack(anchor="w")

        self.description_entry = tk.Text(
            frame,
            height=6
        )

        self.description_entry.pack(
            fill="x",
            pady=5
        )

        ttk.Button(
            frame,
            text="Create Work Order",
            command=self.submit
        ).pack(pady=20)

    def load_outages(self):

        db = connect_db()
        cursor = db.cursor()

        cursor.execute(
            """
            SELECT
                outage_id,
                location,
                status
            FROM outages
            WHERE status != 'Resolved'
            ORDER BY outage_id
            """
        )

        self.outage_data = cursor.fetchall()

        db.close()

        values = []

        for outage in self.outage_data:

            values.append(
                f"Outage #{outage[0]} - "
                f"{outage[1]} - "
                f"{outage[2]}"
            )

        self.outage_combo["values"] = values

        if values:
            self.outage_combo.current(0)

    def load_technicians(self):

        db = connect_db()
        cursor = db.cursor()

        cursor.execute(
            """
            SELECT
                technician_id,
                name,
                specialization,
                availability
            FROM technicians
            WHERE availability = 'Available'
            ORDER BY technician_id
            """
        )

        self.technician_data = cursor.fetchall()

        db.close()

        values = []

        for technician in self.technician_data:

            values.append(
                f"{technician[0]} - "
                f"{technician[1]} - "
                f"{technician[2]}"
            )

        self.technician_combo["values"] = values

        if values:
            self.technician_combo.current(0)

    def submit(self):

        outage_index = self.outage_combo.current()
        technician_index = self.technician_combo.current()

        if outage_index == -1:

            messagebox.showerror(
                "Error",
                "Please select an outage."
            )

            return

        if technician_index == -1:

            messagebox.showerror(
                "Error",
                "Please select a technician."
            )

            return

        scheduled_date = (
            self.scheduled_entry
            .get()
            .strip()
        )

        try:

            datetime.strptime(
                scheduled_date,
                "%Y-%m-%d"
            )

        except ValueError:

            messagebox.showerror(
                "Error",
                "Scheduled date must use YYYY-MM-DD."
            )

            return

        description = (
            self.description_entry
            .get("1.0", "end")
            .strip()
        )

        if not description:

            messagebox.showerror(
                "Error",
                "Please enter a work description."
            )

            return

        outage_id = self.outage_data[
            outage_index
        ][0]

        technician_id = self.technician_data[
            technician_index
        ][0]

        date_created = datetime.now().strftime(
            "%Y-%m-%d"
        )

        db = connect_db()
        cursor = db.cursor()

        cursor.execute(
            """
            INSERT INTO work_orders (
                outage_id,
                technician_id,
                date_created,
                scheduled_date,
                status,
                description
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                outage_id,
                technician_id,
                date_created,
                scheduled_date,
                "Scheduled",
                description
            )
        )

        db.commit()

        work_order_id = cursor.lastrowid

        db.close()

        messagebox.showinfo(
            "Success",
            f"Work Order #{work_order_id} created successfully."
        )

        self.refresh_callback()
        self.window.destroy()


# ============================================================
# WORK ORDER STATUS WINDOW
# ============================================================

class WorkOrderStatusWindow:

    def __init__(
        self,
        parent,
        work_order_id,
        current_status,
        refresh_callback
    ):

        self.work_order_id = work_order_id
        self.refresh_callback = refresh_callback

        self.window = tk.Toplevel(parent)

        self.window.title(
            "Update Work Order Status"
        )

        self.window.geometry("400x250")

        frame = ttk.Frame(
            self.window,
            padding=25
        )

        frame.pack(
            fill="both",
            expand=True
        )

        ttk.Label(
            frame,
            text=f"Work Order #{work_order_id}",
            font=("Arial", 16, "bold")
        ).pack(pady=10)

        ttk.Label(
            frame,
            text=f"Current Status: {current_status}"
        ).pack(pady=5)

        self.status_combo = ttk.Combobox(
            frame,
            values=[
                "Pending",
                "Scheduled",
                "In Progress",
                "Completed"
            ],
            state="readonly"
        )

        self.status_combo.pack(
            fill="x",
            pady=5
        )

        self.status_combo.set(
            current_status
        )

        ttk.Button(
            frame,
            text="Update Status",
            command=self.submit
        ).pack(pady=15)

    def submit(self):

        new_status = self.status_combo.get()

        if not new_status:
            return

        db = connect_db()
        cursor = db.cursor()

        cursor.execute(
            """
            UPDATE work_orders
            SET status = ?
            WHERE work_order_id = ?
            """,
            (
                new_status,
                self.work_order_id
            )
        )

        if cursor.rowcount == 0:

            db.close()

            messagebox.showerror(
                "Error",
                "Work order not found."
            )

            return

        db.commit()
        db.close()

        messagebox.showinfo(
            "Success",
            "Work order status updated successfully."
        )

        self.refresh_callback()
        self.window.destroy()


# ============================================================
# TECHNICIAN WINDOW
# ============================================================

class TechnicianWindow:

    def __init__(self, parent):

        self.window = tk.Toplevel(parent)

        self.window.title(
            "GridCare-Lite - Technicians"
        )

        self.window.geometry("850x550")

        ttk.Label(
            self.window,
            text="Technician Management",
            font=("Arial", 18, "bold")
        ).pack(pady=15)

        columns = (
            "id",
            "name",
            "phone",
            "specialization",
            "availability"
        )

        self.tree = ttk.Treeview(
            self.window,
            columns=columns,
            show="headings"
        )

        headings = {
            "id": "ID",
            "name": "Name",
            "phone": "Phone",
            "specialization": "Specialization",
            "availability": "Availability"
        }

        for column in columns:

            self.tree.heading(
                column,
                text=headings[column]
            )

            self.tree.column(
                column,
                width=150
            )

        self.tree.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=10
        )

        buttons = ttk.Frame(
            self.window
        )

        buttons.pack(pady=10)

        ttk.Button(
            buttons,
            text="Add Technician",
            command=self.add_technician
        ).grid(
            row=0,
            column=0,
            padx=5
        )

        ttk.Button(
            buttons,
            text="Refresh",
            command=self.load_technicians
        ).grid(
            row=0,
            column=1,
            padx=5
        )

        self.load_technicians()

    def load_technicians(self):

        for item in self.tree.get_children():
            self.tree.delete(item)

        db = connect_db()
        cursor = db.cursor()

        cursor.execute(
            """
            SELECT
                technician_id,
                name,
                phone,
                specialization,
                availability
            FROM technicians
            ORDER BY technician_id
            """
        )

        technicians = cursor.fetchall()

        db.close()

        for technician in technicians:

            self.tree.insert(
                "",
                "end",
                values=technician
            )

    def add_technician(self):

        AddTechnicianWindow(
            self.window,
            self.load_technicians
        )


# ============================================================
# ADD TECHNICIAN WINDOW
# ============================================================

class AddTechnicianWindow:

    def __init__(self, parent, refresh_callback):

        self.refresh_callback = refresh_callback

        self.window = tk.Toplevel(parent)

        self.window.title(
            "Add Technician"
        )

        self.window.geometry("450x450")

        frame = ttk.Frame(
            self.window,
            padding=25
        )

        frame.pack(
            fill="both",
            expand=True
        )

        ttk.Label(
            frame,
            text="Add Technician",
            font=("Arial", 18, "bold")
        ).pack(pady=10)

        ttk.Label(
            frame,
            text="Name:"
        ).pack(anchor="w")

        self.name_entry = ttk.Entry(frame)

        self.name_entry.pack(
            fill="x",
            pady=5
        )

        ttk.Label(
            frame,
            text="Phone:"
        ).pack(anchor="w")

        self.phone_entry = ttk.Entry(frame)

        self.phone_entry.pack(
            fill="x",
            pady=5
        )

        ttk.Label(
            frame,
            text="Specialization:"
        ).pack(anchor="w")

        self.specialization_entry = ttk.Entry(frame)

        self.specialization_entry.pack(
            fill="x",
            pady=5
        )

        ttk.Label(
            frame,
            text="Availability:"
        ).pack(anchor="w")

        self.availability_combo = ttk.Combobox(
            frame,
            values=[
                "Available",
                "Busy",
                "Unavailable"
            ],
            state="readonly"
        )

        self.availability_combo.set(
            "Available"
        )

        self.availability_combo.pack(
            fill="x",
            pady=5
        )

        ttk.Button(
            frame,
            text="Add Technician",
            command=self.submit
        ).pack(pady=20)

    def submit(self):

        name = self.name_entry.get().strip()
        phone = self.phone_entry.get().strip()
        specialization = (
            self.specialization_entry
            .get()
            .strip()
        )

        availability = (
            self.availability_combo.get()
        )

        if not name or not phone or not specialization:

            messagebox.showerror(
                "Error",
                "Please complete all fields."
            )

            return

        db = connect_db()
        cursor = db.cursor()

        cursor.execute(
            """
            INSERT INTO technicians (
                name,
                phone,
                specialization,
                availability
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                name,
                phone,
                specialization,
                availability
            )
        )

        db.commit()

        technician_id = cursor.lastrowid

        db.close()

        messagebox.showinfo(
            "Success",
            f"Technician #{technician_id} added successfully."
        )

        self.refresh_callback()
        self.window.destroy()


# ============================================================
# TECHNICIAN WORK ORDER WINDOW
# ============================================================

class TechnicianWorkOrderWindow:

    def __init__(self, parent, user):

        self.user = user

        self.window = tk.Toplevel(parent)

        self.window.title(
            "My Work Orders"
        )

        self.window.geometry("950x550")

        ttk.Label(
            self.window,
            text="My Assigned Work Orders",
            font=("Arial", 18, "bold")
        ).pack(pady=15)

        columns = (
            "id",
            "outage",
            "scheduled",
            "status",
            "description"
        )

        self.tree = ttk.Treeview(
            self.window,
            columns=columns,
            show="headings"
        )

        headings = {
            "id": "Work Order",
            "outage": "Outage",
            "scheduled": "Scheduled Date",
            "status": "Status",
            "description": "Description"
        }

        for column in columns:

            self.tree.heading(
                column,
                text=headings[column]
            )

            self.tree.column(
                column,
                width=150
            )

        self.tree.column(
            "description",
            width=300
        )

        self.tree.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=10
        )

        buttons = ttk.Frame(self.window)

        buttons.pack(pady=10)

        ttk.Button(
            buttons,
            text="Mark Complete",
            command=self.mark_complete
        ).grid(
            row=0,
            column=0,
            padx=5
        )

        ttk.Button(
            buttons,
            text="Refresh",
            command=self.load_orders
        ).grid(
            row=0,
            column=1,
            padx=5
        )

        self.load_orders()

    def find_technician_id(self):

        db = connect_db()
        cursor = db.cursor()

        cursor.execute(
            """
            SELECT technician_id
            FROM technicians
            WHERE user_id = ?
            """,
            (self.user[0],)
        )

        result = cursor.fetchone()

        db.close()

        if result:
            return result[0]

        return None

    def load_orders(self):

        for item in self.tree.get_children():
            self.tree.delete(item)

        technician_id = self.find_technician_id()

        if technician_id is None:

            ttk.Label(
                self.window,
                text="This account has not yet been linked to a technician record."
            ).pack()

            return

        db = connect_db()
        cursor = db.cursor()

        cursor.execute(
            """
            SELECT
                work_order_id,
                outage_id,
                scheduled_date,
                status,
                description
            FROM work_orders
            WHERE technician_id = ?
            ORDER BY work_order_id
            """,
            (technician_id,)
        )

        orders = cursor.fetchall()

        db.close()

        for order in orders:

            self.tree.insert(
                "",
                "end",
                values=order
            )

    def mark_complete(self):

        selected = self.tree.selection()

        if not selected:

            messagebox.showerror(
                "Error",
                "Please select a work order."
            )

            return

        values = self.tree.item(
            selected[0],
            "values"
        )

        work_order_id = values[0]

        db = connect_db()
        cursor = db.cursor()

        cursor.execute(
            """
            UPDATE work_orders
            SET status = 'Completed'
            WHERE work_order_id = ?
            """,
            (work_order_id,)
        )

        db.commit()
        db.close()

        messagebox.showinfo(
            "Success",
            "Work order marked as completed."
        )

        self.load_orders()


# ============================================================
# MAINTENANCE WINDOW
# ============================================================

class MaintenanceWindow:

    def __init__(self, parent):

        self.window = tk.Toplevel(parent)

        self.window.title(
            "GridCare-Lite - Maintenance"
        )

        self.window.geometry("1100x500")

        ttk.Label(
            self.window,
            text="Maintenance Records",
            font=("Arial", 18, "bold")
        ).pack(pady=15)

        columns = (
            "id",
            "work_order",
            "technician",
            "start",
            "end",
            "action",
            "notes"
        )

        self.tree = ttk.Treeview(
            self.window,
            columns=columns,
            show="headings"
        )

        headings = {
            "id": "ID",
            "work_order": "Work Order",
            "technician": "Technician",
            "start": "Start Time",
            "end": "End Time",
            "action": "Action Taken",
            "notes": "Notes"
        }

        for column in columns:

            self.tree.heading(
                column,
                text=headings[column]
            )

            self.tree.column(
                column,
                width=120
            )

        self.tree.column(
            "action",
            width=250
        )

        self.tree.column(
            "notes",
            width=250
        )

        self.tree.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=10
        )

        ttk.Button(
            self.window,
            text="Refresh",
            command=self.load_records
        ).pack(pady=10)

        self.load_records()

    def load_records(self):

        for item in self.tree.get_children():
            self.tree.delete(item)

        db = connect_db()
        cursor = db.cursor()

        cursor.execute(
            """
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
            """
        )

        records = cursor.fetchall()

        db.close()

        for record in records:

            self.tree.insert(
                "",
                "end",
                values=record
            )


# ============================================================
# MAINTENANCE ENTRY WINDOW
# ============================================================

class MaintenanceEntryWindow:

    def __init__(
        self,
        parent,
        work_order_id,
        refresh_callback
    ):

        self.work_order_id = work_order_id
        self.refresh_callback = refresh_callback

        self.window = tk.Toplevel(parent)

        self.window.title(
            "Record Maintenance"
        )

        self.window.geometry("500x550")

        frame = ttk.Frame(
            self.window,
            padding=25
        )

        frame.pack(
            fill="both",
            expand=True
        )

        ttk.Label(
            frame,
            text=f"Maintenance - Work Order #{work_order_id}",
            font=("Arial", 16, "bold")
        ).pack(pady=10)

        ttk.Label(
            frame,
            text="Technician:"
        ).pack(anchor="w")

        self.technician_combo = ttk.Combobox(
            frame,
            state="readonly",
            width=45
        )

        self.technician_combo.pack(
            fill="x",
            pady=5
        )

        self.technician_data = []

        self.load_technicians()

        ttk.Label(
            frame,
            text="Start Time:"
        ).pack(anchor="w")

        self.start_entry = ttk.Entry(frame)

        self.start_entry.pack(
            fill="x",
            pady=5
        )

        self.start_entry.insert(
            0,
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

        ttk.Label(
            frame,
            text="End Time:"
        ).pack(anchor="w")

        self.end_entry = ttk.Entry(frame)

        self.end_entry.pack(
            fill="x",
            pady=5
        )

        ttk.Label(
            frame,
            text="Action Taken:"
        ).pack(anchor="w")

        self.action_entry = tk.Text(
            frame,
            height=4
        )

        self.action_entry.pack(
            fill="x",
            pady=5
        )

        ttk.Label(
            frame,
            text="Notes:"
        ).pack(anchor="w")

        self.notes_entry = tk.Text(
            frame,
            height=4
        )

        self.notes_entry.pack(
            fill="x",
            pady=5
        )

        ttk.Button(
            frame,
            text="Save Maintenance Record",
            command=self.submit
        ).pack(pady=15)

    def load_technicians(self):

        db = connect_db()
        cursor = db.cursor()

        cursor.execute(
            """
            SELECT
                technician_id,
                name,
                specialization
            FROM technicians
            ORDER BY technician_id
            """
        )

        self.technician_data = cursor.fetchall()

        db.close()

        values = []

        for technician in self.technician_data:

            values.append(
                f"{technician[0]} - "
                f"{technician[1]} - "
                f"{technician[2]}"
            )

        self.technician_combo["values"] = values

        if values:
            self.technician_combo.current(0)

    def submit(self):

        technician_index = self.technician_combo.current()

        if technician_index == -1:

            messagebox.showerror(
                "Error",
                "Please select a technician."
            )

            return

        start_time = self.start_entry.get().strip()
        end_time = self.end_entry.get().strip()

        action_taken = (
            self.action_entry
            .get("1.0", "end")
            .strip()
        )

        notes = (
            self.notes_entry
            .get("1.0", "end")
            .strip()
        )

        if not start_time or not action_taken:

            messagebox.showerror(
                "Error",
                "Please enter the start time and action taken."
            )

            return

        technician_id = self.technician_data[
            technician_index
        ][0]

        db = connect_db()
        cursor = db.cursor()

        cursor.execute(
            """
            INSERT INTO maintenance (
                work_order_id,
                technician_id,
                start_time,
                end_time,
                action_taken,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                self.work_order_id,
                technician_id,
                start_time,
                end_time,
                action_taken,
                notes
            )
        )

        db.commit()

        maintenance_id = cursor.lastrowid

        db.close()

        messagebox.showinfo(
            "Success",
            f"Maintenance record #{maintenance_id} saved successfully."
        )

        self.refresh_callback()
        self.window.destroy()


# ============================================================
# CUSTOMER COMPLAINT WINDOW
# ============================================================

class ComplaintWindow:

    def __init__(self, parent, user):

        self.user = user

        self.window = tk.Toplevel(parent)

        self.window.title(
            "Customer Complaints"
        )

        self.window.geometry("1050x550")

        ttk.Label(
            self.window,
            text="Customer Complaint Management",
            font=("Arial", 18, "bold")
        ).pack(pady=15)

        columns = (
            "id",
            "customer",
            "contact",
            "complaint",
            "outage",
            "date",
            "status"
        )

        self.tree = ttk.Treeview(
            self.window,
            columns=columns,
            show="headings"
        )

        headings = {
            "id": "ID",
            "customer": "Customer",
            "contact": "Contact",
            "complaint": "Complaint",
            "outage": "Outage",
            "date": "Date",
            "status": "Status"
        }

        for column in columns:

            self.tree.heading(
                column,
                text=headings[column]
            )

            self.tree.column(
                column,
                width=130
            )

        self.tree.column(
            "complaint",
            width=300
        )

        self.tree.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=10
        )

        buttons = ttk.Frame(self.window)

        buttons.pack(pady=10)

        if user[2] in (
            "admin",
            "customer_service"
        ):

            ttk.Button(
                buttons,
                text="Log Complaint",
                command=self.open_form
            ).grid(
                row=0,
                column=0,
                padx=5
            )

        ttk.Button(
            buttons,
            text="Refresh",
            command=self.load_complaints
        ).grid(
            row=0,
            column=1,
            padx=5
        )

        self.load_complaints()

    def load_complaints(self):

        for item in self.tree.get_children():
            self.tree.delete(item)

        db = connect_db()
        cursor = db.cursor()

        cursor.execute(
            """
            SELECT
                complaint_id,
                customer_name,
                customer_contact,
                complaint_text,
                COALESCE(outage_id, ''),
                date_reported,
                status
            FROM complaints
            ORDER BY complaint_id DESC
            """
        )

        complaints = cursor.fetchall()

        db.close()

        for complaint in complaints:

            self.tree.insert(
                "",
                "end",
                values=complaint
            )

    def open_form(self):

        ComplaintEntryWindow(
            self.window,
            self.user,
            self.load_complaints
        )


# ============================================================
# COMPLAINT ENTRY WINDOW
# ============================================================

class ComplaintEntryWindow:

    def __init__(
        self,
        parent,
        user,
        refresh_callback
    ):

        self.user = user
        self.refresh_callback = refresh_callback

        self.window = tk.Toplevel(parent)

        self.window.title(
            "Log Customer Complaint"
        )

        self.window.geometry("500x500")

        frame = ttk.Frame(
            self.window,
            padding=25
        )

        frame.pack(
            fill="both",
            expand=True
        )

        ttk.Label(
            frame,
            text="Customer Complaint",
            font=("Arial", 18, "bold")
        ).pack(pady=10)

        ttk.Label(
            frame,
            text="Customer Name:"
        ).pack(anchor="w")

        self.name_entry = ttk.Entry(frame)

        self.name_entry.pack(
            fill="x",
            pady=5
        )

        ttk.Label(
            frame,
            text="Customer Contact:"
        ).pack(anchor="w")

        self.contact_entry = ttk.Entry(frame)

        self.contact_entry.pack(
            fill="x",
            pady=5
        )

        ttk.Label(
            frame,
            text="Related Outage (optional):"
        ).pack(anchor="w")

        self.outage_combo = ttk.Combobox(
            frame,
            state="readonly"
        )

        self.outage_combo.pack(
            fill="x",
            pady=5
        )

        self.outage_data = []

        self.load_outages()

        ttk.Label(
            frame,
            text="Complaint:"
        ).pack(anchor="w")

        self.complaint_entry = tk.Text(
            frame,
            height=7
        )

        self.complaint_entry.pack(
            fill="x",
            pady=5
        )

        ttk.Button(
            frame,
            text="Save Complaint",
            command=self.submit
        ).pack(pady=15)

    def load_outages(self):

        db = connect_db()
        cursor = db.cursor()

        cursor.execute(
            """
            SELECT
                outage_id,
                location,
                status
            FROM outages
            ORDER BY outage_id DESC
            """
        )

        self.outage_data = cursor.fetchall()

        db.close()

        values = ["None"]

        for outage in self.outage_data:

            values.append(
                f"Outage #{outage[0]} - "
                f"{outage[1]} - "
                f"{outage[2]}"
            )

        self.outage_combo["values"] = values
        self.outage_combo.current(0)

    def submit(self):

        name = self.name_entry.get().strip()
        contact = self.contact_entry.get().strip()

        complaint = (
            self.complaint_entry
            .get("1.0", "end")
            .strip()
        )

        if not name or not complaint:

            messagebox.showerror(
                "Error",
                "Please enter the customer name and complaint."
            )

            return

        outage_id = None

        if self.outage_combo.current() > 0:

            outage_id = self.outage_data[
                self.outage_combo.current() - 1
            ][0]

        date_reported = datetime.now().strftime(
            "%Y-%m-%d"
        )

        db = connect_db()
        cursor = db.cursor()

        cursor.execute(
            """
            INSERT INTO complaints (
                customer_name,
                customer_contact,
                complaint_text,
                outage_id,
                date_reported,
                status,
                recorded_by
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                contact,
                complaint,
                outage_id,
                date_reported,
                "Open",
                self.user[0]
            )
        )

        db.commit()

        complaint_id = cursor.lastrowid

        db.close()

        messagebox.showinfo(
            "Success",
            f"Complaint #{complaint_id} recorded successfully."
        )

        self.refresh_callback()
        self.window.destroy()


# ============================================================
# USER MANAGEMENT
# ============================================================

class UserManagementWindow:

    def __init__(self, parent):

        self.window = tk.Toplevel(parent)

        self.window.title(
            "User Management"
        )

        self.window.geometry("800x500")

        ttk.Label(
            self.window,
            text="User Management",
            font=("Arial", 18, "bold")
        ).pack(pady=15)

        columns = (
            "id",
            "name",
            "username",
            "role"
        )

        self.tree = ttk.Treeview(
            self.window,
            columns=columns,
            show="headings"
        )

        headings = {
            "id": "User ID",
            "name": "Name",
            "username": "Username",
            "role": "Role"
        }

        for column in columns:

            self.tree.heading(
                column,
                text=headings[column]
            )

            self.tree.column(
                column,
                width=180
            )

        self.tree.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=10
        )

        buttons = ttk.Frame(self.window)

        buttons.pack(pady=10)

        ttk.Button(
            buttons,
            text="Create User",
            command=self.create_user
        ).grid(
            row=0,
            column=0,
            padx=5
        )

        ttk.Button(
            buttons,
            text="Refresh",
            command=self.load_users
        ).grid(
            row=0,
            column=1,
            padx=5
        )

        self.load_users()

    def load_users(self):

        for item in self.tree.get_children():
            self.tree.delete(item)

        db = connect_db()
        cursor = db.cursor()

        cursor.execute(
            """
            SELECT
                user_id,
                name,
                username,
                role
            FROM users
            ORDER BY user_id
            """
        )

        users = cursor.fetchall()

        db.close()

        for user in users:

            self.tree.insert(
                "",
                "end",
                values=user
            )

    def create_user(self):

        CreateUserWindow(
            self.window,
            self.load_users
        )


# ============================================================
# CREATE USER WINDOW
# ============================================================

class CreateUserWindow:

    def __init__(self, parent, refresh_callback):

        self.refresh_callback = refresh_callback

        self.window = tk.Toplevel(parent)

        self.window.title(
            "Create System User"
        )

        self.window.geometry("450x450")

        frame = ttk.Frame(
            self.window,
            padding=25
        )

        frame.pack(
            fill="both",
            expand=True
        )

        ttk.Label(
            frame,
            text="Create System User",
            font=("Arial", 18, "bold")
        ).pack(pady=10)

        ttk.Label(
            frame,
            text="Name:"
        ).pack(anchor="w")

        self.name_entry = ttk.Entry(frame)

        self.name_entry.pack(
            fill="x",
            pady=5
        )

        ttk.Label(
            frame,
            text="Username:"
        ).pack(anchor="w")

        self.username_entry = ttk.Entry(frame)

        self.username_entry.pack(
            fill="x",
            pady=5
        )

        ttk.Label(
            frame,
            text="Password:"
        ).pack(anchor="w")

        self.password_entry = ttk.Entry(
            frame,
            show="*"
        )

        self.password_entry.pack(
            fill="x",
            pady=5
        )

        ttk.Label(
            frame,
            text="Role:"
        ).pack(anchor="w")

        self.role_combo = ttk.Combobox(
            frame,
            values=[
                "admin",
                "engineer",
                "technician",
                "customer_service"
            ],
            state="readonly"
        )

        self.role_combo.set("engineer")

        self.role_combo.pack(
            fill="x",
            pady=5
        )

        ttk.Button(
            frame,
            text="Create User",
            command=self.submit
        ).pack(pady=20)

    def submit(self):

        name = self.name_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        role = self.role_combo.get()

        if not name or not username or not password or not role:

            messagebox.showerror(
                "Error",
                "Please complete all fields."
            )

            return

        db = connect_db()
        cursor = db.cursor()

        cursor.execute(
            """
            SELECT user_id
            FROM users
            WHERE username = ?
            """,
            (username,)
        )

        if cursor.fetchone():

            db.close()

            messagebox.showerror(
                "Error",
                "Username already exists."
            )

            return

        cursor.execute(
            """
            INSERT INTO users (
                name,
                role,
                username,
                password,
                password_hash
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                name,
                role,
                username,
                password,
                hash_password(password)
            )
        )

        user_id = cursor.lastrowid

        # If creating a technician account, also create
        # a technician record linked to the user.
        if role == "technician":

            cursor.execute(
                """
                INSERT INTO technicians (
                    name,
                    availability,
                    user_id
                )
                VALUES (?, ?, ?)
                """,
                (
                    name,
                    "Available",
                    user_id
                )
            )

        db.commit()
        db.close()

        messagebox.showinfo(
            "Success",
            "User created successfully."
        )

        self.refresh_callback()
        self.window.destroy()


# ============================================================
# REPORTS WINDOW
# ============================================================

class ReportsWindow:

    def __init__(self, parent):

        self.window = tk.Toplevel(parent)

        self.window.title(
            "GridCare-Lite - Reports"
        )

        self.window.geometry("850x600")

        ttk.Label(
            self.window,
            text="GridCare-Lite Reports",
            font=("Arial", 20, "bold")
        ).pack(pady=15)

        self.text = tk.Text(
            self.window,
            height=25,
            width=95
        )

        self.text.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )

        ttk.Button(
            self.window,
            text="Refresh Report",
            command=self.generate_report
        ).pack(pady=10)

        self.generate_report()

    def generate_report(self):

        self.text.delete(
            "1.0",
            "end"
        )

        db = connect_db()
        cursor = db.cursor()

        # ----------------------------------------------------
        # Overall outage counts
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                COUNT(*)
            FROM outages
            """
        )

        total = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT
                COUNT(*)
            FROM outages
            WHERE status != 'Resolved'
            """
        )

        open_count = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT
                COUNT(*)
            FROM outages
            WHERE status = 'Resolved'
            """
        )

        resolved_count = cursor.fetchone()[0]

        # ----------------------------------------------------
        # Outages by region/location
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                COALESCE(s.location, 'Unknown'),
                COUNT(*)
            FROM outages o
            LEFT JOIN substations s
                ON o.substation_id = s.substation_id
            GROUP BY s.location
            ORDER BY COUNT(*) DESC
            """
        )

        regions = cursor.fetchall()

        # ----------------------------------------------------
        # Work orders
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                status,
                COUNT(*)
            FROM work_orders
            GROUP BY status
            """
        )

        work_orders = cursor.fetchall()

        # ----------------------------------------------------
        # Average resolution time
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT outage_id
            FROM outages
            WHERE status = 'Resolved'
            """
        )

        resolved_ids = [
            row[0]
            for row in cursor.fetchall()
        ]

        resolution_times = []

        for outage_id in resolved_ids:

            cursor.execute(
                """
                SELECT
                    o.date_reported,
                    MAX(s.update_time)
                FROM outages o
                JOIN status_updates s
                    ON o.outage_id = s.outage_id
                WHERE o.outage_id = ?
                AND s.new_status = 'Resolved'
                """,
                (outage_id,)
            )

            result = cursor.fetchone()

            if result and result[0] and result[1]:

                try:

                    start = datetime.strptime(
                        result[0],
                        "%Y-%m-%d"
                    )

                    end = datetime.strptime(
                        result[1],
                        "%Y-%m-%d %H:%M:%S"
                    )

                    resolution_times.append(
                        (
                            end - start
                        ).total_seconds() / 86400
                    )

                except ValueError:
                    pass

        db.close()

        if resolution_times:

            average = (
                sum(resolution_times)
                / len(resolution_times)
            )

            average_text = (
                f"{average:.2f} days"
            )

        else:

            average_text = (
                "No resolved outages available."
            )

        report = ""

        report += "GRIDCARE-LITE BASIC REPORT\n"
        report += "=" * 60
        report += "\n\n"

        report += "OUTAGE SUMMARY\n"
        report += "-" * 40
        report += f"\nTotal Outages: {total}"
        report += f"\nOpen Outages: {open_count}"
        report += f"\nResolved Outages: {resolved_count}"
        report += (
            f"\nAverage Resolution Time: "
            f"{average_text}"
        )

        report += "\n\nOUTAGES BY REGION\n"
        report += "-" * 40

        if regions:

            for region, count in regions:

                report += (
                    f"\n{region}: {count} outage(s)"
                )

        else:

            report += "\nNo regional outage data."

        report += "\n\nWORK ORDERS BY STATUS\n"
        report += "-" * 40

        if work_orders:

            for status, count in work_orders:

                report += (
                    f"\n{status}: {count}"
                )

        else:

            report += "\nNo work orders."

        self.text.insert(
            "1.0",
            report
        )


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    # Make sure the existing database is compatible
    # before opening the GUI.
    setup_database()

    root = tk.Tk()

    LoginWindow(root)

    root.mainloop()


if __name__ == "__main__":
    main()