# CarePoint — Hospital Management Website

A simple Flask + MySQL website for the Hospital Management System DBMS mini project.

## Features
- Dashboard with patient, doctor, appointment and bill counts
- Reads live records from the existing MySQL database
- Pages for patients, doctors, appointments, rooms and bills
- Add-patient form that writes directly into MySQL
- Responsive layout for laptop and mobile screens

## Important database note
This project defaults to a database named `hospital_management` because that is the database name used in the current work. If your actual database is named `hospital_db` or something else, update `DB_NAME` in the commands below. The app detects common column-name variants (such as `Name` or `patient_name`) for the patient form.

## 1. Open the project
Unzip the folder and open `HospitalManagementWebsite` in VS Code.

## 2. Start MySQL
Start your MySQL server using the MySQL settings you already configured. Do not start MySQL with `--skip-grant-tables` for normal use.

## 3. Install Python dependencies
Open Terminal in VS Code and run:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 4. Set your database password
In the same Terminal session, set the password you use to log in to MySQL. Do not type your password into the source code or share it in screenshots.

```bash
export DB_USER=root
export DB_PASSWORD='YOUR_MYSQL_PASSWORD'
export DB_NAME=hospital_management
```

Replace `YOUR_MYSQL_PASSWORD` with your actual password. If your database is named `hospital_db`, use `export DB_NAME=hospital_db` instead.

## 5. Run the website

```bash
python3 app.py
```

Open this address in your browser:

http://127.0.0.1:5000

## Troubleshooting
- **Access denied:** check `DB_USER` and `DB_PASSWORD` against the credentials that work in Terminal.
- **Unknown database:** run `SHOW DATABASES;` inside MySQL and set `DB_NAME` to the exact database name.
- **Table not found:** make sure all nine tables are in the selected database.
- **Column not found on dashboard:** the app's recent-appointment card expects `Patient_ID`, `Doctor_ID`, `Appointment_Date`, and a patient/doctor name column. If your table columns differ, adapt the joins in `app.py` to match `DESCRIBE Patient;`, `DESCRIBE Doctor;`, and `DESCRIBE Appointment;`.

## Security
This is a local student demo, not a production medical system. Do not use real patient information. Do not expose this development server publicly. Use a dedicated least-privilege MySQL user for anything beyond local testing.
