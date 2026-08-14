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
        self.root.geometry("450x350")
        self.root.resizable(False, False)

        frame = ttk.Frame(self.root, padding=30)
        frame.pack(expand=True)

        title = ttk.Label(
            frame,
            text="GRIDCARE-LITE",
            font=("Arial", 22, "bold")
        )
        title.grid(row=0, column=0, columnspan=2, pady=10)

        subtitle = ttk.Label(
            frame,
            text="Outage and Maintenance Management System"
        )
        subtitle.grid(row=1, column=0, columnspan=2, pady=10)

        ttk.Label(
            frame,
            text="Username:"
        ).grid(row=2, column=0, sticky="w", pady=8)

        self.username_entry = ttk.Entry(
            frame,
            width=30
        )
        self.username_entry.grid(row=2, column=1, pady=8)

        ttk.Label(
            frame,
            text="Password:"
        ).grid(row=3, column=0, sticky="w", pady=8)

        self.password_entry = ttk.Entry(
            frame,
            width=30,
            show="*"
        )
        self.password_entry.grid(row=3, column=1, pady=8)

        login_button = ttk.Button(
            frame,
            text="Log In",
            command=self.login
        )
        login_button.grid(
            row=4,
            column=0,
            columnspan=2,
            pady=20
        )

        self.root.bind(
            "<Return>",
            lambda event: self.login()
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

        cursor.execute("""
            SELECT user_id, name, role, username
            FROM users
            WHERE username = ? AND password = ?
        """, (username, password))

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
            f"GridCare-Lite - Dashboard ({self.name})"
        )

        self.root.geometry("900x600")

        self.build_dashboard()

    def build_dashboard(self):

        header = ttk.Frame(
            self.root,
            padding=20
        )
        header.pack(fill="x")

        ttk.Label(
            header,
            text="GRIDCARE-LITE",
            font=("Arial", 22, "bold")
        ).pack(side="left")

        ttk.Label(
            header,
            text=f"Welcome, {self.name} ({self.role})"
        ).pack(side="right")

        content = ttk.Frame(
            self.root,
            padding=20
        )
        content.pack(fill="both", expand=True)

        ttk.Label(
            content,
            text="Operations Dashboard",
            font=("Arial", 18, "bold")
        ).pack(pady=15)

        buttons_frame = ttk.Frame(content)
        buttons_frame.pack(pady=20)

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
            text="Refresh Dashboard",
            width=25,
            command=self.refresh_dashboard
        ).grid(
            row=2,
            column=0,
            padx=10,
            pady=10
        )

        ttk.Button(
            buttons_frame,
            text="Logout",
            width=25,
            command=self.logout
        ).grid(
            row=2,
            column=1,
            padx=10,
            pady=10
        )

        self.summary_frame = ttk.LabelFrame(
            content,
            text="System Summary",
            padding=20
        )
        self.summary_frame.pack(
            fill="x",
            pady=20
        )

        self.load_summary()

    def load_summary(self):

        for widget in self.summary_frame.winfo_children():
            widget.destroy()

        db = connect_db()
        cursor = db.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM outages
        """)

        total_outages = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM outages
            WHERE status != 'Resolved'
        """)

        open_outages = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM work_orders
        """)

        total_work_orders = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM technicians
        """)

        total_technicians = cursor.fetchone()[0]

        db.close()

        ttk.Label(
            self.summary_frame,
            text=f"Total Outages: {total_outages}"
        ).pack(anchor="w", pady=3)

        ttk.Label(
            self.summary_frame,
            text=f"Open Outages: {open_outages}"
        ).pack(anchor="w", pady=3)

        ttk.Label(
            self.summary_frame,
            text=f"Work Orders: {total_work_orders}"
        ).pack(anchor="w", pady=3)

        ttk.Label(
            self.summary_frame,
            text=f"Technicians: {total_technicians}"
        ).pack(anchor="w", pady=3)

    def refresh_dashboard(self):
        self.load_summary()

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
        self.window.title("GridCare-Lite - Outages")
        self.window.geometry("950x500")

        ttk.Label(
            self.window,
            text="Outage Dashboard",
            font=("Arial", 18, "bold")
        ).pack(pady=15)

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
            command=self.load_outages
        ).pack(pady=10)

        self.load_outages()

    def load_outages(self):

        for item in self.tree.get_children():
            self.tree.delete(item)

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

        for outage in outages:

            self.tree.insert(
                "",
                "end",
                values=outage
            )


# ============================================================
# REPORT OUTAGE WINDOW
# ============================================================

class ReportOutageWindow:

    def __init__(self, parent, user, refresh_callback):

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
        frame.pack(fill="both", expand=True)

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
            text="Priority:"
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

        cursor.execute("""
            SELECT
                substation_id,
                substation_code,
                name,
                location
            FROM substations
        """)

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
            self.user[0],
            date_reported,
            priority
        ))

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

        self.window.geometry("950x600")

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

        buttons.pack(pady=10)

        ttk.Button(
            buttons,
            text="Create Work Order",
            command=self.create_work_order
        ).grid(
            row=0,
            column=0,
            padx=10
        )

        ttk.Button(
            buttons,
            text="Refresh",
            command=self.load_work_orders
        ).grid(
            row=0,
            column=1,
            padx=10
        )

        self.load_work_orders()

    def load_work_orders(self):

        for item in self.tree.get_children():
            self.tree.delete(item)

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

        cursor.execute("""
            SELECT
                outage_id,
                location,
                description,
                status
            FROM outages
            WHERE status != 'Resolved'
        """)

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

        cursor.execute("""
            SELECT
                technician_id,
                name,
                specialization,
                availability
            FROM technicians
            WHERE availability = 'Available'
        """)

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

        messagebox.showinfo(
            "Success",
            f"Work Order #{work_order_id} created successfully."
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

        self.window.geometry("750x450")

        ttk.Label(
            self.window,
            text="Technicians",
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
                width=140
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
            command=self.load_technicians
        ).pack(pady=10)

        self.load_technicians()

    def load_technicians(self):

        for item in self.tree.get_children():
            self.tree.delete(item)

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

        for technician in technicians:

            self.tree.insert(
                "",
                "end",
                values=technician
            )


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    root = tk.Tk()

    LoginWindow(root)

    root.mainloop()


if __name__ == "__main__":
    main()