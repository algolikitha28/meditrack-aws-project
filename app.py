from flask import Flask, render_template, request, redirect, jsonify
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

def get_db():
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DB"),
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/')
def dashboard():

    conn = get_db()

    with conn.cursor() as cur:

        cur.execute("SELECT COUNT(*) total FROM equipment")
        total = cur.fetchone()['total']

        cur.execute("""
        SELECT status, COUNT(*) count
        FROM equipment
        GROUP BY status
        """)
        status_counts = cur.fetchall()

        cur.execute("""
        SELECT e.equipment_name,
               m.next_due_date
        FROM maintenance_logs m
        JOIN equipment e
        ON e.equipment_id = m.equipment_id
        WHERE m.next_due_date < CURDATE()
        """)
        overdue = cur.fetchall()

    conn.close()

    return render_template(
        'dashboard.html',
        total=total,
        status_counts=status_counts,
        overdue=overdue
    )

@app.route('/add_equipment', methods=['GET','POST'])
def add_equipment():

    if request.method == 'POST':

        conn = get_db()

        with conn.cursor() as cur:

            cur.execute("""
            INSERT INTO equipment
            (
            equipment_name,
            serial_number,
            department,
            purchase_date,
            status
            )
            VALUES (%s,%s,%s,%s,%s)
            """,
            (
                request.form['equipment_name'],
                request.form['serial_number'],
                request.form['department'],
                request.form['purchase_date'],
                request.form['status']
            ))

            conn.commit()

        conn.close()

        return redirect('/equipment')

    return render_template('add_equipment.html')

@app.route('/equipment')
def equipment():

    conn = get_db()

    with conn.cursor() as cur:

        cur.execute("SELECT * FROM equipment")
        equipment = cur.fetchall()

    conn.close()

    return render_template(
        'equipment_list.html',
        equipment=equipment
    )

@app.route('/maintenance/<int:id>', methods=['GET','POST'])
def maintenance(id):

    if request.method == 'POST':

        conn = get_db()

        with conn.cursor() as cur:

            cur.execute("""
            INSERT INTO maintenance_logs
            (
            equipment_id,
            maintenance_date,
            technician_name,
            issue_reported,
            resolution_notes,
            next_due_date
            )
            VALUES (%s,%s,%s,%s,%s,%s)
            """,
            (
                id,
                request.form['maintenance_date'],
                request.form['technician_name'],
                request.form['issue_reported'],
                request.form['resolution_notes'],
                request.form['next_due_date']
            ))

            conn.commit()

        conn.close()

        return redirect('/equipment')

    return render_template(
        'add_maintenance.html',
        equipment_id=id
    )

@app.route('/history/<int:id>')
def history(id):

    conn = get_db()

    with conn.cursor() as cur:

        cur.execute("""
        SELECT *
        FROM maintenance_logs
        WHERE equipment_id=%s
        """,(id,))

        logs = cur.fetchall()

    conn.close()

    return render_template(
        'maintenance_history.html',
        logs=logs
    )

@app.route('/update_status/<int:id>', methods=['POST'])
def update_status(id):

    status = request.form['status']

    conn = get_db()

    with conn.cursor() as cur:

        cur.execute("""
        UPDATE equipment
        SET status=%s
        WHERE equipment_id=%s
        """,(status,id))

        conn.commit()

    conn.close()

    return redirect('/equipment')

@app.route('/api/overdue')
def overdue_api():

    conn = get_db()

    with conn.cursor() as cur:

        cur.execute("""
        SELECT *
        FROM maintenance_logs
        WHERE next_due_date < CURDATE()
        """)

        data = cur.fetchall()

    conn.close()

    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)