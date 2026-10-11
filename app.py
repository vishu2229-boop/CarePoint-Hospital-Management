import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-for-local-development")

# Configure these environment variables if your MySQL settings differ.
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "hospital_management"),
}

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

def table_columns(cursor, table):
    cursor.execute("""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = %s AND LOWER(TABLE_NAME) = LOWER(%s)
        ORDER BY ORDINAL_POSITION
    """, (DB_CONFIG["database"], table))
    return [row["COLUMN_NAME"] for row in cursor.fetchall()]

def find_column(columns, *candidates):
    by_lower = {c.lower(): c for c in columns}
    for candidate in candidates:
        if candidate.lower() in by_lower:
            return by_lower[candidate.lower()]
    return None

def quote_identifier(identifier):
    # Only identifiers read from INFORMATION_SCHEMA are passed here.
    return "`" + identifier.replace("`", "``") + "`"

def fetch_all(sql, params=()):
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def get_dashboard_stats():
    conn = get_connection()
    try:
        cur = conn.cursor()
        stats = {}
        for table, label in [
            ("Patient", "patients"),
            ("Doctor", "doctors"),
            ("Appointment", "appointments"),
            ("Bill", "bills"),
        ]:
            cur.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = %s AND LOWER(TABLE_NAME) = LOWER(%s)
            """, (DB_CONFIG["database"], table))
            exists = cur.fetchone()[0]
            if exists:
                cur.execute(f"SELECT COUNT(*) FROM {quote_identifier(table)}")
                stats[label] = cur.fetchone()[0]
            else:
                stats[label] = 0
        return stats
    finally:
        cur.close()
        conn.close()

@app.route("/")
def dashboard():
    try:
        stats = get_dashboard_stats()
        recent = fetch_all("""
            SELECT a.*, p.*, d.*
            FROM Appointment a
            LEFT JOIN Patient p ON a.Patient_ID = p.Patient_ID
            LEFT JOIN Doctor d ON a.Doctor_ID = d.Doctor_ID
            ORDER BY a.Appointment_Date DESC
            LIMIT 5
        """)
        # Use clear, stable display fields even if a schema has Name or patient_name.
        appointments = []
        for row in recent:
            appointments.append({
                "id": row.get("Appointment_ID", row.get("appointment_id", "")),
                "patient": row.get("patient_name", row.get("Name", row.get("name", "Patient"))),
                "doctor": row.get("doctor_name", row.get("Name_1", "Doctor")),
                "date": row.get("Appointment_Date", row.get("appointment_date", "")),
                "status": row.get("Status", row.get("status", "Scheduled")),
            })
        return render_template("dashboard.html", stats=stats, appointments=appointments)
    except Error as e:
        return render_template("setup_error.html", error=str(e), config=DB_CONFIG)

@app.route("/patients")
def patients():
    try:
        rows = fetch_all("SELECT * FROM Patient ORDER BY 1 DESC")
        columns = list(rows[0].keys()) if rows else table_columns_from_db("Patient")
        return render_template("table.html", title="Patients", rows=rows, columns=columns,
                               add_url=url_for("add_patient"), empty_text="No patient records yet.")
    except Error as e:
        flash(f"Could not load patients: {e}", "error")
        return redirect(url_for("dashboard"))

def table_columns_from_db(table):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA=%s AND LOWER(TABLE_NAME)=LOWER(%s)
            ORDER BY ORDINAL_POSITION
        """, (DB_CONFIG["database"], table))
        return [r[0] for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()

@app.route("/patients/add", methods=["GET", "POST"])
def add_patient():
    columns = table_columns_from_db("Patient")
    name_col = find_column(columns, "patient_name", "name")
    dob_col = find_column(columns, "dob", "date_of_birth")
    gender_col = find_column(columns, "gender")
    phone_col = find_column(columns, "phone", "phone_number")
    blood_col = find_column(columns, "blood_group", "blood_type")
    address_col = find_column(columns, "address")
    editable = [c for c in [name_col, dob_col, gender_col, phone_col, blood_col, address_col] if c]
    if request.method == "POST":
        values = []
        for col in editable:
            val = request.form.get(col, "").strip() or None
            if col == dob_col and val:
                # HTML date field supplies YYYY-MM-DD.
                datetime.strptime(val, "%Y-%m-%d")
            values.append(val)
        if not name_col or not request.form.get(name_col, "").strip():
            flash("Patient name is required. Check the Patient table schema.", "error")
            return render_template("patient_form.html", columns=editable, labels=labels_for(editable))
        conn = get_connection()
        try:
            cur = conn.cursor()
            placeholders = ", ".join(["%s"] * len(editable))
            col_sql = ", ".join(quote_identifier(c) for c in editable)
            cur.execute(f"INSERT INTO Patient ({col_sql}) VALUES ({placeholders})", values)
            conn.commit()
            flash("Patient added successfully.", "success")
            return redirect(url_for("patients"))
        except Error as e:
            flash(f"Could not add patient: {e}", "error")
        finally:
            cur.close()
            conn.close()
    return render_template("patient_form.html", columns=editable, labels=labels_for(editable))

def labels_for(columns):
    labels = {}
    for c in columns:
        low = c.lower()
        labels[c] = {
            "patient_name": "Patient name", "name": "Patient name",
            "dob": "Date of birth", "date_of_birth": "Date of birth",
            "gender": "Gender", "phone": "Phone", "phone_number": "Phone",
            "blood_group": "Blood group", "blood_type": "Blood group",
            "address": "Address",
        }.get(low, c.replace("_", " ").title())
    return labels

@app.route("/doctors")
def doctors():
    return generic_table("Doctor", "Doctors")

@app.route("/appointments")
def appointments_page():
    return generic_table("Appointment", "Appointments")

@app.route("/rooms")
def rooms():
    return generic_table("Room", "Rooms")

@app.route("/bills")
def bills():
    return generic_table("Bill", "Bills")

def generic_table(table, title):
    try:
        rows = fetch_all(f"SELECT * FROM {quote_identifier(table)} ORDER BY 1 DESC")
        columns = list(rows[0].keys()) if rows else table_columns_from_db(table)
        return render_template("table.html", title=title, rows=rows, columns=columns,
                               add_url=None, empty_text=f"No {title.lower()} records yet.")
    except Error as e:
        flash(f"Could not load {title.lower()}: {e}", "error")
        return redirect(url_for("dashboard"))

@app.route("/health")
def health():
    try:
        conn = get_connection()
        conn.close()
        return {"status": "ok", "database": DB_CONFIG["database"]}
    except Error as e:
        return {"status": "error", "message": str(e)}, 500

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
