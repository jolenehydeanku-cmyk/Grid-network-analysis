import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime


DATABASE_NAME = "gridcare.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def connect_db():
    return sqlite3.connect(DATABASE_NAME)


# ============================================================
# LOGIN WINDOW
# ============================================================

class LoginWindow:

    def __init__(self, root):

        self.root = root

        self.root.title("GridCare-Lite - Login")
        self.root.geometry("450x400")
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

        self.root.bind(
            "<Return>",
            lambda event: self.login()
        )

    def open_register(self):

        RegisterWindow(
            self.root
        )

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
                username
            FROM users
            WHERE username = ?
            AND password = ?
            """,
            (
                username,
                password
            )
        )

        user = cursor.fetchone()

        db.close()

        if user is None:

            messagebox.showerror(
                "Login Failed",
                "Incorrect username or password."
            )

            return

        for widget in self.root.winfo_children():
            widget.destroy()

        Dashboard(
            self.root,
            user
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

        self.window.geometry("450x400")
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
            text="Account Type:"
        ).grid(
            row=4,
            column=0,
            sticky="w",
            pady=8
        )

        ttk.Label(
            frame,
            text="Customer"
        ).grid(
            row=4,
            column=1,
            sticky="w",
            pady=8
        )

        ttk.Button(
            frame,
            text="Register",
            command=self.register
        ).grid(
            row=5,
            column=0,
            columnspan=2,
            pady=20
        )

    def register(self):

        name = self.name_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not name or not username or not password:

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

        existing_user = cursor.fetchone()

        if existing_user is not None:

            db.close()

            messagebox.showerror(
                "Registration Failed",
                "That username is already in use. Please choose another username."
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
                "Customer",
                username,
                password
            )
        )

        db.commit()
        db.close()

        messagebox.showinfo(
            "Registration Successful",
            "Your account has been created successfully. You can now log in."
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
        self.role = self.normalize_role(user[2])
        self.username = user[3]

        self.root.title(
            f"GridCare-Lite - Dashboard ({self.name})"
        )

        self.root.geometry("900x650")

        self.build_dashboard()

    # --------------------------------------------------------
    # NORMALIZE EXISTING AND NEW ROLE NAMES
    # --------------------------------------------------------

    def normalize_role(self, role):

        role = role.strip().lower()

        role_mapping = {
            "manager": "Administrator",
            "admin": "Administrator",
            "administrator": "Administrator",

            "engineer": "Engineer",

            "technician": "Technician",

            "customer_service": "Customer Service",
            "customer service": "Customer Service",

            "customer": "Customer"
        }

        return role_mapping.get(
            role,
            role.title()
        )

    # --------------------------------------------------------
    # DASHBOARD
    # --------------------------------------------------------

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

        # ====================================================
        # ADMINISTRATOR
        # ====================================================

        if self.role == "Administrator":

            ttk.Button(
                buttons_frame,
                text="View Outages",
                width=25,
                command=self.open_outages
            ).grid(
                row=0,
                column=0,
                padx=10,
                pady=10
            )

            ttk.Button(
                buttons_frame,
                text="Report New Outage",
                width=25,
                command=self.report_outage
            ).grid(
                row=0,
                column=1,
                padx=10,
                pady=10
            )

            ttk.Button(
                buttons_frame,
                text="Work Orders",
                width=25,
                command=self.open_work_orders
            ).grid(
                row=1,
                column=0,
                padx=10,
                pady=10
            )

            ttk.Button(
                buttons_frame,
                text="Technicians",
                width=25,
                command=self.open_technicians
            ).grid(
                row=1,
                column=1,
                padx=10,
                pady=10
            )

            ttk.Button(
                buttons_frame,
                text="Maintenance",
                width=25,
                command=self.open_maintenance
            ).grid(
                row=2,
                column=0,
                padx=10,
                pady=10
            )

            ttk.Button(
                buttons_frame,
                text="Refresh Dashboard",
                width=25,
                command=self.refresh_dashboard
            ).grid(
                row=2,
                column=1,
                padx=10,
                pady=10
            )

        # ====================================================
        # ENGINEER
        # ====================================================

        elif self.role == "Engineer":

            ttk.Button(
                buttons_frame,
                text="View Outages",
                width=25,
                command=self.open_outages
            ).grid(
                row=0,
                column=0,
                padx=10,
                pady=10
            )

            ttk.Button(
                buttons_frame,
                text="Report New Outage",
                width=25,
                command=self.report_outage
            ).grid(
                row=0,
                column=1,
                padx=10,
                pady=10
            )

            ttk.Button(
                buttons_frame,
                text="Refresh Dashboard",
                width=25,
                command=self.refresh_dashboard
            ).grid(
                row=1,
                column=0,
                padx=10,
                pady=10
            )

        # ====================================================
        # TECHNICIAN
        # ====================================================

        elif self.role == "Technician":

            ttk.Button(
                buttons_frame,
                text="My Work Orders",
                width=25,
                command=self.open_work_orders
            ).grid(
                row=0,
                column=0,
                padx=10,
                pady=10
            )

            ttk.Button(
                buttons_frame,
                text="Maintenance",
                width=25,
                command=self.open_maintenance
            ).grid(
                row=0,
                column=1,
                padx=10,
                pady=10
            )

            ttk.Button(
                buttons_frame,
                text="Refresh Dashboard",
                width=25,
                command=self.refresh_dashboard
            ).grid(
                row=1,
                column=0,
                padx=10,
                pady=10
            )

        # ====================================================
        # CUSTOMER SERVICE
        # ====================================================

        elif self.role == "Customer Service":

            ttk.Button(
                buttons_frame,
                text="View Outages",
                width=25,
                command=self.open_outages
            ).grid(
                row=0,
                column=0,
                padx=10,
                pady=10
            )

            ttk.Button(
                buttons_frame,
                text="Refresh Dashboard",
                width=25,
                command=self.refresh_dashboard
            ).grid(
                row=0,
                column=1,
                padx=10,
                pady=10
            )

        # ====================================================
        # EXISTING CUSTOMER ROLE
        # ====================================================

        elif self.role == "Customer":

            ttk.Button(
                buttons_frame,
                text="View Outages",
                width=25,
                command=self.open_outages
            ).grid(
                row=0,
                column=0,
                padx=10,
                pady=10
            )

            ttk.Button(
                buttons_frame,
                text="Refresh Dashboard",
                width=25,
                command=self.refresh_dashboard
            ).grid(
                row=0,
                column=1,
                padx=10,
                pady=10
            )

        # ====================================================
        # UNKNOWN ROLE
        # ====================================================

        else:

            ttk.Label(
                buttons_frame,
                text="Your account does not have a recognized role.",
                foreground="red"
            ).pack(
                pady=20
            )

        # ====================================================
        # LOGOUT
        # ====================================================

        ttk.Button(
            buttons_frame,
            text="Logout",
            width=25,
            command=self.logout
        ).grid(
            row=10,
            column=0,
            columnspan=2,
            pady=20
        )

        # ====================================================
        # SYSTEM SUMMARY
        # ====================================================

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

    # --------------------------------------------------------
    # LOAD DASHBOARD SUMMARY
    # --------------------------------------------------------

    def load_summary(self):

        for widget in self.summary_frame.winfo_children():
            widget.destroy()

        db = connect_db()
        cursor = db.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM outages
            """
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
            """
            SELECT COUNT(*)
            FROM work_orders
            """
        )

        total_work_orders = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM technicians
            """
        )

        total_technicians = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM maintenance
            """
        )

        total_maintenance = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM status_updates
            """
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

    # --------------------------------------------------------
    # REFRESH
    # --------------------------------------------------------

    def refresh_dashboard(self):

        self.load_summary()

        messagebox.showinfo(
            "Dashboard Refreshed",
            "Dashboard information has been refreshed."
        )

    # --------------------------------------------------------
    # OPEN OUTAGES
    # --------------------------------------------------------

    def open_outages(self):

        OutageWindow(
            self.root,
            self.user
        )

    # --------------------------------------------------------
    # REPORT OUTAGE
    # --------------------------------------------------------

    def report_outage(self):

        ReportOutageWindow(
            self.root,
            self.user,
            self.load_summary
        )

    # --------------------------------------------------------
    # WORK ORDERS
    # --------------------------------------------------------

    def open_work_orders(self):

        WorkOrderWindow(
            self.root,
            self.user
        )

    # --------------------------------------------------------
    # TECHNICIANS
    # --------------------------------------------------------

    def open_technicians(self):

        TechnicianWindow(
            self.root
        )

    # --------------------------------------------------------
    # MAINTENANCE
    # --------------------------------------------------------

    def open_maintenance(self):

        MaintenanceWindow(
            self.root
        )

    # --------------------------------------------------------
    # LOGOUT
    # --------------------------------------------------------

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

        self.window = tk.Toplevel(parent)

        self.window.title(
            "GridCare-Lite - Outages"
        )

        self.window.geometry("1100x550")

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

            messagebox.showinfo(
                "No Change",
                "The outage already has this status."
            )

            db.close()

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

        self.window = tk.Toplevel(parent)

        self.window.title(
            "GridCare-Lite - Report Outage"
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
            text="Priority:"
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

        self.window.geometry("1000x600")

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
                work_order_id,
                outage_id,
                technician_id,
                date_created,
                status,
                description
            FROM work_orders
            ORDER BY work_order_id
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
# CREATE WORK ORDER WINDOW
# ============================================================

class CreateWorkOrderWindow:

    def __init__(self, parent, refresh_callback):

        self.refresh_callback = refresh_callback

        self.window = tk.Toplevel(parent)

        self.window.title(
            "Create Work Order"
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

            text = (
                f"Outage #{outage[0]} - "
                f"{outage[1]} - "
                f"{outage[3]}"
            )

            values.append(text)

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

            text = (
                f"{technician[0]} - "
                f"{technician[1]} - "
                f"{technician[2]}"
            )

            values.append(text)

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

        self.window = tk.Toplevel(parent)

        self.window.title(
            "GridCare-Lite - Technicians"
        )

        self.window.geometry("800x500")

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
                width=140
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
        ).pack(
            pady=10
        )

        ttk.Label(
            frame,
            text="Name:"
        ).pack(
            anchor="w"
        )

        self.name_entry = ttk.Entry(frame)

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

        self.phone_entry = ttk.Entry(frame)

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

        self.specialization_entry = ttk.Entry(frame)

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

        name = self.name_entry.get().strip()
        phone = self.phone_entry.get().strip()

        specialization = (
            self.specialization_entry
            .get()
            .strip()
        )

        availability = self.availability_combo.get()

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

        self.window = tk.Toplevel(parent)

        self.window.title(
            "GridCare-Lite - Maintenance"
        )

        self.window.geometry("1100x500")

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

            text = (
                f"{technician[0]} - "
                f"{technician[1]} - "
                f"{technician[2]}"
            )

            values.append(text)

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
# MAIN PROGRAM
# ============================================================

def main():

    root = tk.Tk()

    LoginWindow(
        root
    )

    root.mainloop()


if __name__ == "__main__":
    main()