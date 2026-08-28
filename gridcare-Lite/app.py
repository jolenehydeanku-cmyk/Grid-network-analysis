import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import hashlib


DATABASE_NAME = "gridcare.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def connect_db():
    db = sqlite3.connect(DATABASE_NAME)
    db.execute("PRAGMA foreign_keys = ON")
    return db


# ============================================================
# PASSWORD FUNCTIONS
# ============================================================

def hash_password(password):
    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


def check_password(stored_password, entered_password):
    """
    Supports both:
    1. Old plain-text passwords already in the database
    2. New hashed passwords
    """

    hashed = hash_password(entered_password)

    if stored_password == hashed:
        return True

    # Support old accounts created before this version
    if stored_password == entered_password:
        return True

    return False


# ============================================================
# DATABASE PREPARATION
# ============================================================

def prepare_database():

    db = connect_db()
    cursor = db.cursor()

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
    # Add user_id to technicians if it does not exist
    # --------------------------------------------------------

    cursor.execute(
        "PRAGMA table_info(technicians)"
    )

    technician_columns = [
        row[1]
        for row in cursor.fetchall()
    ]

    if "user_id" not in technician_columns:

        cursor.execute(
            """
            ALTER TABLE technicians
            ADD COLUMN user_id INTEGER
            """
        )

    # --------------------------------------------------------
    # Convert old roles to the new four-role system
    # --------------------------------------------------------

    cursor.execute(
        """
        UPDATE users
        SET role = 'Administrator'
        WHERE role = 'Manager'
        """
    )

    cursor.execute(
        """
        UPDATE users
        SET role = 'Customer Service'
        WHERE role = 'Customer'
        """
    )

    db.commit()
    db.close()


# ============================================================
# LOGIN WINDOW
# ============================================================

class LoginWindow:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "GridCare-Lite - Login"
        )

        self.root.geometry(
            "450x400"
        )

        self.root.resizable(
            False,
            False
        )

        frame = ttk.Frame(
            self.root,
            padding=30
        )

        frame.pack(
            expand=True
        )

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

        self.root.bind(
            "<Return>",
            lambda event: self.login()
        )

    def open_register(self):

        RegisterWindow(
            self.root
        )

    def login(self):

        username = (
            self.username_entry
            .get()
            .strip()
        )

        password = (
            self.password_entry
            .get()
            .strip()
        )

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
        username = user[3]
        stored_password = user[4]

        if not check_password(
            stored_password,
            password
        ):

            db.close()

            messagebox.showerror(
                "Login Failed",
                "Incorrect username or password."
            )

            return

        # Upgrade old plain-text password
        if stored_password == password:

            cursor.execute(
                """
                UPDATE users
                SET password = ?
                WHERE user_id = ?
                """,
                (
                    hash_password(password),
                    user_id
                )
            )

            db.commit()

        db.close()

        # ----------------------------------------------------
        # Check role
        # ----------------------------------------------------

        valid_roles = [
            "Administrator",
            "Engineer",
            "Technician",
            "Customer Service"
        ]

        if role not in valid_roles:

            messagebox.showerror(
                "Login Failed",
                "This account has an invalid role."
            )

            return

        for widget in self.root.winfo_children():
            widget.destroy()

        Dashboard(
            self.root,
            (
                user_id,
                name,
                role,
                username
            )
        )


# ============================================================
# REGISTER WINDOW
# ============================================================

class RegisterWindow:

    def __init__(self, parent):

        self.window = tk.Toplevel(
            parent
        )

        self.window.title(
            "GridCare-Lite - Create Account"
        )

        self.window.geometry(
            "500x500"
        )

        self.window.resizable(
            False,
            False
        )

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
            text="Account Type:"
        ).grid(
            row=4,
            column=0,
            sticky="w",
            pady=8
        )

        self.role_combo = ttk.Combobox(
            frame,
            values=[
                "Engineer",
                "Technician",
                "Customer Service"
            ],
            state="readonly",
            width=28
        )

        self.role_combo.grid(
            row=4,
            column=1,
            pady=8
        )

        self.role_combo.set(
            "Engineer"
        )

        ttk.Label(
            frame,
            text=(
                "Administrator accounts cannot be created "
                "through public registration."
            ),
            wraplength=400
        ).grid(
            row=5,
            column=0,
            columnspan=2,
            pady=15
        )

        ttk.Button(
            frame,
            text="Register",
            command=self.register
        ).grid(
            row=6,
            column=0,
            columnspan=2,
            pady=20
        )

    def register(self):

        name = (
            self.name_entry
            .get()
            .strip()
        )

        username = (
            self.username_entry
            .get()
            .strip()
        )

        password = (
            self.password_entry
            .get()
            .strip()
        )

        role = self.role_combo.get()

        if not name or not username or not password:

            messagebox.showerror(
                "Registration Failed",
                "Please complete all fields."
            )

            return

        if role not in [
            "Engineer",
            "Technician",
            "Customer Service"
        ]:

            messagebox.showerror(
                "Registration Failed",
                "Please select a valid account type."
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

        password_hash = hash_password(
            password
        )

        cursor.execute(
            """
            INSERT INTO users (
                name,
                role,
                username,
                password
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                name,
                role,
                username,
                password_hash
            )
        )

        user_id = cursor.lastrowid

        # ----------------------------------------------------
        # If registering a technician, also create technician
        # record and connect it to the user account.
        # ----------------------------------------------------

        if role == "Technician":

            cursor.execute(
                """
                INSERT INTO technicians (
                    name,
                    specialization,
                    availability,
                    user_id
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    name,
                    "General Electrical",
                    "Available",
                    user_id
                )
            )

        db.commit()
        db.close()

        messagebox.showinfo(
            "Registration Successful",
            (
                f"{role} account created successfully.\n\n"
                "You can now log in."
            )
        )

        self.window.destroy()


# ============================================================
# MAIN DASHBOARD
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
            f"GridCare-Lite - {self.role} Dashboard"
        )

        self.root.geometry(
            "950x700"
        )

        self.build_dashboard()

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
            text=f"Welcome, {self.name} ({self.role})"
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
            text=f"{self.role} Dashboard",
            font=("Arial", 18, "bold")
        ).pack(
            pady=15
        )

        buttons_frame = ttk.Frame(
            content
        )

        buttons_frame.pack(
            pady=10
        )

        # ----------------------------------------------------
        # ADMINISTRATOR
        # ----------------------------------------------------

        if self.role == "Administrator":

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
                "Customer Complaints",
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

        # ----------------------------------------------------
        # ENGINEER
        # ----------------------------------------------------

        elif self.role == "Engineer":

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
                "Logout",
                self.logout,
                1,
                1
            )

        # ----------------------------------------------------
        # TECHNICIAN
        # ----------------------------------------------------

        elif self.role == "Technician":

            self.add_button(
                buttons_frame,
                "My Work Orders",
                self.open_my_work_orders,
                0,
                0
            )

            self.add_button(
                buttons_frame,
                "Update / Complete Assigned Work",
                self.open_my_work_orders,
                0,
                1
            )

            self.add_button(
                buttons_frame,
                "Logout",
                self.logout,
                1,
                0
            )

        # ----------------------------------------------------
        # CUSTOMER SERVICE
        # ----------------------------------------------------

        elif self.role == "Customer Service":

            self.add_button(
                buttons_frame,
                "View Outages",
                self.open_outages,
                0,
                0
            )

            self.add_button(
                buttons_frame,
                "Customer Complaints",
                self.open_complaints,
                0,
                1
            )

            self.add_button(
                buttons_frame,
                "Logout",
                self.logout,
                1,
                0
            )

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
            width=28,
            command=command
        ).grid(
            row=row,
            column=column,
            padx=10,
            pady=10
        )

    # --------------------------------------------------------
    # DASHBOARD FUNCTIONS
    # --------------------------------------------------------

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
            "SELECT COUNT(*) FROM status_updates"
        )

        total_updates = cursor.fetchone()[0]

        db.close()

        summary = [
            f"Total Outages: {total_outages}",
            f"Open Outages: {open_outages}",
            f"Work Orders: {total_work_orders}",
            f"Technicians: {total_technicians}",
            f"Maintenance Records: {total_maintenance}",
            f"Status Updates: {total_updates}"
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

    # --------------------------------------------------------
    # WINDOWS
    # --------------------------------------------------------

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

    def open_my_work_orders(self):

        MyWorkOrderWindow(
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

    def open_users(self):

        UserManagementWindow(
            self.root,
            self.user
        )

    def open_reports(self):

        ReportsWindow(
            self.root
        )

    def logout(self):

        answer = messagebox.askyesno(
            "Logout",
            "Are you sure you want to logout?"
        )

        if answer:

            for widget in self.root.winfo_children():
                widget.destroy()

            LoginWindow(
                self.root
            )


# ============================================================
# OUTAGE WINDOW
# ============================================================

class OutageWindow:

    def __init__(self, parent, user):

        self.user = user

        self.window = tk.Toplevel(
            parent
        )

        self.window.title(
            "GridCare-Lite - Outages"
        )

        self.window.geometry(
            "1100x550"
        )

        ttk.Label(
            self.window,
            text="Outage Management",
            font=("Arial", 18, "bold")
        ).pack(
            pady=15
        )

        columns = (
            "id",
            "substation",
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
            "location": "Location",
            "description": "Description",
            "reported_by": "Reported By",
            "date": "Date",
            "priority": "Priority",
            "status": "Status"
        }

        for column in columns:

            self.tree.heading(
                column,
                text=headings[column]
            )

            self.tree.column(
                column,
                width=110
            )

        self.tree.column(
            "description",
            width=260
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

        buttons.pack(
            pady=10
        )

        if self.user[2] in [
            "Administrator",
            "Engineer"
        ]:

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
                o.location,
                o.description,
                u.name,
                o.date_reported,
                o.priority,
                o.status
            FROM outages o
            LEFT JOIN users u
                ON o.reported_by = u.user_id
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
        current_status = values[7]

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

        self.window = tk.Toplevel(
            parent
        )

        self.window.title(
            "Update Outage Status"
        )

        self.window.geometry(
            "400x250"
        )

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
        ).pack(
            pady=10
        )

        ttk.Label(
            frame,
            text=f"Current Status: {current_status}"
        ).pack(
            pady=5
        )

        ttk.Label(
            frame,
            text="New Status:"
        ).pack(
            anchor="w"
        )

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

        self.status_combo.set(
            current_status
        )

        ttk.Button(
            frame,
            text="Update Status",
            command=self.submit
        ).pack(
            pady=15
        )

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

        update_time = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
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

        self.window = tk.Toplevel(
            parent
        )

        self.window.title(
            "GridCare-Lite - Report Outage"
        )

        self.window.geometry(
            "500x500"
        )

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
        ).pack(
            pady=10
        )

        ttk.Label(
            frame,
            text="Substation:"
        ).pack(
            anchor="w"
        )

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
        ).pack(
            anchor="w"
        )

        self.location_entry = ttk.Entry(
            frame
        )

        self.location_entry.pack(
            fill="x",
            pady=5
        )

        ttk.Label(
            frame,
            text="Description:"
        ).pack(
            anchor="w"
        )

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
        ).pack(
            anchor="w"
        )

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

        self.priority_combo.set(
            "Medium"
        )

        self.priority_combo.pack(
            fill="x",
            pady=5
        )

        ttk.Button(
            frame,
            text="Report Outage",
            command=self.submit
        ).pack(
            pady=20
        )

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

            text = (
                f"{substation[1]} - "
                f"{substation[2]} - "
                f"{substation[3]}"
            )

            values.append(text)

        self.substation_combo["values"] = values

        if values:
            self.substation_combo.current(0)

    def submit(self):

        selected_index = (
            self.substation_combo.current()
        )

        if selected_index == -1:

            messagebox.showerror(
                "Error",
                "Please select a substation."
            )

            return

        location = (
            self.location_entry
            .get()
            .strip()
        )

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
            "%Y-%m-%d %H:%M:%S"
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
# WORK ORDER WINDOW - ADMINISTRATOR
# ============================================================

class WorkOrderWindow:

    def __init__(self, parent, user):

        self.user = user

        self.window = tk.Toplevel(
            parent
        )

        self.window.title(
            "GridCare-Lite - Work Orders"
        )

        self.window.geometry(
            "1000x600"
        )

        ttk.Label(
            self.window,
            text="Work Order Management",
            font=("Arial", 18, "bold")
        ).pack(
            pady=15
        )

        columns = (
            "id",
            "outage",
            "technician",
            "date",
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
            "date": "Date",
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
                width=130
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

        buttons = ttk.Frame(
            self.window
        )

        buttons.pack(
            pady=10
        )

        ttk.Button(
            buttons,
            text="Create Work Order",
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

        work_order_id = values[0]
        current_status = values[4]

        WorkOrderStatusWindow(
            self.window,
            work_order_id,
            current_status,
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

        work_order_id = values[0]

        MaintenanceEntryWindow(
            self.window,
            work_order_id,
            self.load_work_orders
        )


# ============================================================
# MY WORK ORDERS - TECHNICIAN
# ============================================================

class MyWorkOrderWindow:

    def __init__(self, parent, user):

        self.user = user

        self.window = tk.Toplevel(
            parent
        )

        self.window.title(
            "GridCare-Lite - My Work Orders"
        )

        self.window.geometry(
            "1000x550"
        )

        ttk.Label(
            self.window,
            text="My Assigned Work Orders",
            font=("Arial", 18, "bold")
        ).pack(
            pady=15
        )

        columns = (
            "id",
            "outage",
            "date",
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
            "date": "Date",
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
            width=350
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

        buttons.pack(
            pady=10
        )

        ttk.Button(
            buttons,
            text="Update / Complete Work",
            command=self.update_work
        ).grid(
            row=0,
            column=0,
            padx=5
        )

        ttk.Button(
            buttons,
            text="Refresh",
            command=self.load_work_orders
        ).grid(
            row=0,
            column=1,
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
            SELECT technician_id
            FROM technicians
            WHERE user_id = ?
            """,
            (self.user[0],)
        )

        technician = cursor.fetchone()

        if technician is None:

            db.close()

            messagebox.showwarning(
                "No Technician Record",
                "No technician record is linked to this account."
            )

            return

        technician_id = technician[0]

        cursor.execute(
            """
            SELECT
                work_order_id,
                outage_id,
                date_created,
                status,
                description
            FROM work_orders
            WHERE technician_id = ?
            ORDER BY work_order_id
            """,
            (technician_id,)
        )

        work_orders = cursor.fetchall()

        db.close()

        for work_order in work_orders:

            self.tree.insert(
                "",
                "end",
                values=work_order
            )

    def update_work(self):

        selected = self.tree.selection()

        if not selected:

            messagebox.showerror(
                "Error",
                "Please select one of your work orders."
            )

            return

        values = self.tree.item(
            selected[0],
            "values"
        )

        work_order_id = values[0]
        current_status = values[3]

        TechnicianWorkWindow(
            self.window,
            self.user,
            work_order_id,
            current_status,
            self.load_work_orders
        )


# ============================================================
# TECHNICIAN WORK UPDATE
# ============================================================

class TechnicianWorkWindow:

    def __init__(
        self,
        parent,
        user,
        work_order_id,
        current_status,
        refresh_callback
    ):

        self.user = user
        self.work_order_id = work_order_id
        self.refresh_callback = refresh_callback

        self.window = tk.Toplevel(
            parent
        )

        self.window.title(
            "Update Assigned Work"
        )

        self.window.geometry(
            "450x300"
        )

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
        ).pack(
            pady=10
        )

        ttk.Label(
            frame,
            text="Status:"
        ).pack(
            anchor="w"
        )

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

        self.status_combo.set(
            current_status
        )

        self.status_combo.pack(
            fill="x",
            pady=8
        )

        ttk.Label(
            frame,
            text="Work Notes:"
        ).pack(
            anchor="w"
        )

        self.notes_entry = tk.Text(
            frame,
            height=5
        )

        self.notes_entry.pack(
            fill="x",
            pady=8
        )

        ttk.Button(
            frame,
            text="Save Update",
            command=self.submit
        ).pack(
            pady=10
        )

    def submit(self):

        new_status = self.status_combo.get()

        if not new_status:
            return

        db = connect_db()
        cursor = db.cursor()

        # Verify that the work order belongs to this technician
        cursor.execute(
            """
            SELECT w.work_order_id
            FROM work_orders w
            JOIN technicians t
                ON w.technician_id = t.technician_id
            WHERE w.work_order_id = ?
            AND t.user_id = ?
            """,
            (
                self.work_order_id,
                self.user[0]
            )
        )

        if cursor.fetchone() is None:

            db.close()

            messagebox.showerror(
                "Access Denied",
                "You are not assigned to this work order."
            )

            return

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

        db.commit()
        db.close()

        messagebox.showinfo(
            "Success",
            "Your work order has been updated successfully."
        )

        self.refresh_callback()

        self.window.destroy()


# ============================================================
# CREATE WORK ORDER WINDOW
# ============================================================

class CreateWorkOrderWindow:

    def __init__(
        self,
        parent,
        refresh_callback
    ):

        self.refresh_callback = refresh_callback

        self.window = tk.Toplevel(
            parent
        )

        self.window.title(
            "Create Work Order"
        )

        self.window.geometry(
            "500x500"
        )

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
        ).pack(
            pady=10
        )

        ttk.Label(
            frame,
            text="Outage:"
        ).pack(
            anchor="w"
        )

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
        ).pack(
            anchor="w"
        )

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
            text="Work Description:"
        ).pack(
            anchor="w"
        )

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
        ).pack(
            pady=20
        )

    def load_outages(self):

        db = connect_db()
        cursor = db.cursor()

        cursor.execute(
            """
            SELECT
                outage_id,
                location,
                description,
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
                f"{outage[3]}"
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

        outage_index = (
            self.outage_combo.current()
        )

        technician_index = (
            self.technician_combo.current()
        )

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
                status,
                description
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                outage_id,
                technician_id,
                date_created,
                "Pending",
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

        self.window = tk.Toplevel(
            parent
        )

        self.window.title(
            "Update Work Order Status"
        )

        self.window.geometry(
            "400x250"
        )

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
        ).pack(
            pady=10
        )

        ttk.Label(
            frame,
            text=f"Current Status: {current_status}"
        ).pack(
            pady=5
        )

        ttk.Label(
            frame,
            text="New Status:"
        ).pack(
            anchor="w"
        )

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
        ).pack(
            pady=15
        )

    def submit(self):

        new_status = self.status_combo.get()

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

        self.window = tk.Toplevel(
            parent
        )

        self.window.title(
            "GridCare-Lite - Technicians"
        )

        self.window.geometry(
            "850x500"
        )

        ttk.Label(
            self.window,
            text="Technician Management",
            font=("Arial", 18, "bold")
        ).pack(
            pady=15
        )

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

        buttons.pack(
            pady=10
        )

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

    def __init__(
        self,
        parent,
        refresh_callback
    ):

        self.refresh_callback = refresh_callback

        self.window = tk.Toplevel(
            parent
        )

        self.window.title(
            "Add Technician"
        )

        self.window.geometry(
            "450x450"
        )

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
        ).pack(
            pady=10
        )

        ttk.Label(
            frame,
            text="Name:"
        ).pack(
            anchor="w"
        )

        self.name_entry = ttk.Entry(
            frame
        )

        self.name_entry.pack(
            fill="x",
            pady=5
        )

        ttk.Label(
            frame,
            text="Phone:"
        ).pack(
            anchor="w"
        )

        self.phone_entry = ttk.Entry(
            frame
        )

        self.phone_entry.pack(
            fill="x",
            pady=5
        )

        ttk.Label(
            frame,
            text="Specialization:"
        ).pack(
            anchor="w"
        )

        self.specialization_entry = ttk.Entry(
            frame
        )

        self.specialization_entry.pack(
            fill="x",
            pady=5
        )

        ttk.Label(
            frame,
            text="Availability:"
        ).pack(
            anchor="w"
        )

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
        ).pack(
            pady=20
        )

    def submit(self):

        name = (
            self.name_entry
            .get()
            .strip()
        )

        phone = (
            self.phone_entry
            .get()
            .strip()
        )

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
# MAINTENANCE WINDOW
# ============================================================

class MaintenanceWindow:

    def __init__(self, parent):

        self.window = tk.Toplevel(
            parent
        )

        self.window.title(
            "GridCare-Lite - Maintenance"
        )

        self.window.geometry(
            "1100x500"
        )

        ttk.Label(
            self.window,
            text="Maintenance Records",
            font=("Arial", 18, "bold")
        ).pack(
            pady=15
        )

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
        ).pack(
            pady=10
        )

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

        self.window = tk.Toplevel(
            parent
        )

        self.window.title(
            "Record Maintenance"
        )

        self.window.geometry(
            "500x550"
        )

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
        ).pack(
            pady=10
        )

        ttk.Label(
            frame,
            text="Technician:"
        ).pack(
            anchor="w"
        )

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
        ).pack(
            anchor="w"
        )

        self.start_entry = ttk.Entry(
            frame
        )

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
        ).pack(
            anchor="w"
        )

        self.end_entry = ttk.Entry(
            frame
        )

        self.end_entry.pack(
            fill="x",
            pady=5
        )

        ttk.Label(
            frame,
            text="Action Taken:"
        ).pack(
            anchor="w"
        )

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
        ).pack(
            anchor="w"
        )

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
        ).pack(
            pady=15
        )

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

        technician_index = (
            self.technician_combo.current()
        )

        if technician_index == -1:

            messagebox.showerror(
                "Error",
                "Please select a technician."
            )

            return

        start_time = (
            self.start_entry
            .get()
            .strip()
        )

        end_time = (
            self.end_entry
            .get()
            .strip()
        )

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
            (
                f"Maintenance record #{maintenance_id} "
                "saved successfully."
            )
        )

        self.refresh_callback()

        self.window.destroy()


# ============================================================
# CUSTOMER COMPLAINT WINDOW
# ============================================================

class ComplaintWindow:

    def __init__(self, parent, user):

        self.user = user

        self.window = tk.Toplevel(
            parent
        )

        self.window.title(
            "GridCare-Lite - Customer Complaints"
        )

        self.window.geometry(
            "1050x600"
        )

        ttk.Label(
            self.window,
            text="Customer Complaints",
            font=("Arial", 18, "bold")
        ).pack(
            pady=15
        )

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

        buttons = ttk.Frame(
            self.window
        )

        buttons.pack(
            pady=10
        )

        ttk.Button(
            buttons,
            text="Log Complaint",
            command=self.log_complaint
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
                outage_id,
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

    def log_complaint(self):

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

        self.window = tk.Toplevel(
            parent
        )

        self.window.title(
            "Log Customer Complaint"
        )

        self.window.geometry(
            "500x550"
        )

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
            text="Log Customer Complaint",
            font=("Arial", 18, "bold")
        ).pack(
            pady=10
        )

        ttk.Label(
            frame,
            text="Customer Name:"
        ).pack(
            anchor="w"
        )

        self.customer_entry = ttk.Entry(
            frame
        )

        self.customer_entry.pack(
            fill="x",
            pady=5
        )

        ttk.Label(
            frame,
            text="Customer Contact:"
        ).pack(
            anchor="w"
        )

        self.contact_entry = ttk.Entry(
            frame
        )

        self.contact_entry.pack(
            fill="x",
            pady=5
        )

        ttk.Label(
            frame,
            text="Related Outage:"
        ).pack(
            anchor="w"
        )

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
        ).pack(
            anchor="w"
        )

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
        ).pack(
            pady=15
        )

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
            ORDER BY outage_id
            """
        )

        self.outage_data = cursor.fetchall()

        db.close()

        values = [
            "No linked outage"
        ]

        for outage in self.outage_data:

            values.append(
                f"Outage #{outage[0]} - "
                f"{outage[1]} - "
                f"{outage[2]}"
            )

        self.outage_combo["values"] = values

        self.outage_combo.current(0)

    def submit(self):

        customer_name = (
            self.customer_entry
            .get()
            .strip()
        )

        contact = (
            self.contact_entry
            .get()
            .strip()
        )

        complaint = (
            self.complaint_entry
            .get("1.0", "end")
            .strip()
        )

        if not customer_name or not complaint:

            messagebox.showerror(
                "Error",
                "Please enter the customer name and complaint."
            )

            return

        selected = self.outage_combo.current()

        outage_id = None

        if selected > 0:

            outage_id = self.outage_data[
                selected - 1
            ][0]

        date_reported = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
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
                customer_name,
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

    def __init__(self, parent, user):

        self.user = user

        self.window = tk.Toplevel(
            parent
        )

        self.window.title(
            "GridCare-Lite - User Management"
        )

        self.window.geometry(
            "850x500"
        )

        ttk.Label(
            self.window,
            text="User Management",
            font=("Arial", 18, "bold")
        ).pack(
            pady=15
        )

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

        buttons = ttk.Frame(
            self.window
        )

        buttons.pack(
            pady=10
        )

        ttk.Button(
            buttons,
            text="Create Staff Account",
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

        AdminCreateUserWindow(
            self.window,
            self.load_users
        )


# ============================================================
# ADMIN CREATE USER WINDOW
# ============================================================

class AdminCreateUserWindow:

    def __init__(
        self,
        parent,
        refresh_callback
    ):

        self.refresh_callback = refresh_callback

        self.window = tk.Toplevel(
            parent
        )

        self.window.title(
            "Create Staff Account"
        )

        self.window.geometry(
            "500x500"
        )

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
            text="Create Staff Account",
            font=("Arial", 18, "bold")
        ).pack(
            pady=10
        )

        ttk.Label(
            frame,
            text="Name:"
        ).pack(
            anchor="w"
        )

        self.name_entry = ttk.Entry(
            frame
        )

        self.name_entry.pack(
            fill="x",
            pady=5
        )

        ttk.Label(
            frame,
            text="Username:"
        ).pack(
            anchor="w"
        )

        self.username_entry = ttk.Entry(
            frame
        )

        self.username_entry.pack(
            fill="x",
            pady=5
        )

        ttk.Label(
            frame,
            text="Password:"
        ).pack(
            anchor="w"
        )

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
        ).pack(
            anchor="w"
        )

        self.role_combo = ttk.Combobox(
            frame,
            values=[
                "Engineer",
                "Technician",
                "Customer Service"
            ],
            state="readonly"
        )

        self.role_combo.set(
            "Engineer"
        )

        self.role_combo.pack(
            fill="x",
            pady=5
        )

        ttk.Button(
            frame,
            text="Create Account",
            command=self.submit
        ).pack(
            pady=20
        )

    def submit(self):

        name = (
            self.name_entry
            .get()
            .strip()
        )

        username = (
            self.username_entry
            .get()
            .strip()
        )

        password = (
            self.password_entry
            .get()
            .strip()
        )

        role = self.role_combo.get()

        if not name or not username or not password:

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

        if cursor.fetchone() is not None:

            db.close()

            messagebox.showerror(
                "Error",
                "That username is already in use."
            )

            return

        cursor.execute(
            """
            INSERT INTO users (
                name,
                role,
                username,
                password
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                name,
                role,
                username,
                hash_password(password)
            )
        )

        user_id = cursor.lastrowid

        if role == "Technician":

            cursor.execute(
                """
                INSERT INTO technicians (
                    name,
                    specialization,
                    availability,
                    user_id
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    name,
                    "General Electrical",
                    "Available",
                    user_id
                )
            )

        db.commit()
        db.close()

        messagebox.showinfo(
            "Success",
            f"{role} account created successfully."
        )

        self.refresh_callback()

        self.window.destroy()


# ============================================================
# REPORTS WINDOW
# ============================================================

class ReportsWindow:

    def __init__(self, parent):

        self.window = tk.Toplevel(
            parent
        )

        self.window.title(
            "GridCare-Lite - Reports"
        )

        self.window.geometry(
            "700x600"
        )

        ttk.Label(
            self.window,
            text="GridCare-Lite Reports",
            font=("Arial", 18, "bold")
        ).pack(
            pady=15
        )

        frame = ttk.Frame(
            self.window,
            padding=20
        )

        frame.pack(
            fill="both",
            expand=True
        )

        self.report_text = tk.Text(
            frame,
            height=25,
            width=80
        )

        self.report_text.pack(
            fill="both",
            expand=True
        )

        ttk.Button(
            self.window,
            text="Refresh Report",
            command=self.load_report
        ).pack(
            pady=10
        )

        self.load_report()

    def load_report(self):

        db = connect_db()
        cursor = db.cursor()

        # Total and open outages
        cursor.execute(
            "SELECT COUNT(*) FROM outages"
        )

        total = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM outages
            WHERE status != 'Resolved'
            """
        )

        open_outages = cursor.fetchone()[0]

        # Average resolution time
        cursor.execute(
            """
            SELECT
                AVG(
                    julianday(s.update_time)
                    - julianday(o.date_reported)
                )
            FROM outages o
            JOIN status_updates s
                ON o.outage_id = s.outage_id
            WHERE s.new_status = 'Resolved'
            """
        )

        average_days = cursor.fetchone()[0]

        if average_days is None:
            average_text = "No resolved outages yet."
        else:
            average_hours = average_days * 24
            average_text = (
                f"{average_hours:.2f} hours"
            )

        # Outages by location/region
        cursor.execute(
            """
            SELECT
                location,
                COUNT(*)
            FROM outages
            GROUP BY location
            ORDER BY COUNT(*) DESC
            """
        )

        regions = cursor.fetchall()

        db.close()

        self.report_text.delete(
            "1.0",
            "end"
        )

        self.report_text.insert(
            "end",
            "GRIDCARE-LITE BASIC REPORT\n"
        )

        self.report_text.insert(
            "end",
            "============================\n\n"
        )

        self.report_text.insert(
            "end",
            f"Total Outages: {total}\n"
        )

        self.report_text.insert(
            "end",
            f"Open Outages: {open_outages}\n"
        )

        self.report_text.insert(
            "end",
            f"Average Resolution Time: {average_text}\n\n"
        )

        self.report_text.insert(
            "end",
            "OUTAGES BY REGION / LOCATION\n"
        )

        self.report_text.insert(
            "end",
            "----------------------------\n"
        )

        if not regions:

            self.report_text.insert(
                "end",
                "No outage data available.\n"
            )

        else:

            for region, count in regions:

                self.report_text.insert(
                    "end",
                    f"{region}: {count} outage(s)\n"
                )


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    prepare_database()

    root = tk.Tk()

    LoginWindow(
        root
    )

    root.mainloop()


if __name__ == "__main__":
    main()