from flask import Flask, render_template, request, redirect, session, url_for, flash
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Change this to a strong secret key for production
DATABASE = "instance/app.db"


def init_db():
    # Ensure instance folder exists
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Create tables if not exist
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            fullname TEXT,
            contact TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS parking_lots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prime_location_name TEXT NOT NULL,
            price REAL NOT NULL,
            address TEXT,
            pin_code TEXT,
            max_spots INTEGER NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS parking_spots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lot_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'A',
            FOREIGN KEY (lot_id) REFERENCES parking_lots(id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spot_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            vehicle_number TEXT,
            parked_at TEXT,
            left_at TEXT,
            cost REAL,
            status TEXT NOT NULL DEFAULT 'booked',
            FOREIGN KEY (spot_id) REFERENCES parking_spots(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Insert default admin user if not exists
    c.execute("SELECT id FROM users WHERE username=?", ('admin',))
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, role, fullname) VALUES (?, ?, ?, ?)",
                  ('admin', 'admin123', 'admin', 'Super Admin'))

    conn.commit()
    conn.close()


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif session.get('role') == 'user':
            return redirect(url_for('user_dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?", (username, password)
        ).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['role'] = user['role']
            flash("Logged in successfully!", "success")
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash("Invalid username or password.", "danger")
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        fullname = request.form.get('fullname', '').strip()
        contact = request.form.get('contact', '').strip()

        if not (username and password):
            flash("Username and password are required!", "danger")
            return render_template('register.html')

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (username, password, role, fullname, contact) VALUES (?, ?, 'user', ?, ?)",
                (username, password, fullname, contact)
            )
            conn.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Username already taken.", "danger")
        finally:
            conn.close()
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('login'))


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        flash("Please login first.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db()
    if request.method == 'POST':
        fullname = request.form.get('fullname', '').strip()
        contact = request.form.get('contact', '').strip()
        password = request.form.get('password', '').strip()
        if password:
            conn.execute("UPDATE users SET fullname=?, contact=?, password=? WHERE id=?",
                         (fullname, contact, password, user_id))
        else:
            conn.execute("UPDATE users SET fullname=?, contact=? WHERE id=?",
                         (fullname, contact, user_id))
        conn.commit()
        flash("Profile updated successfully.", "success")

    user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return render_template('profile.html', user=user)


@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('login'))

    conn = get_db()
    lots = conn.execute("SELECT * FROM parking_lots").fetchall()
    users = conn.execute("SELECT * FROM users WHERE role='user'").fetchall()
    conn.close()
    return render_template('admin_dashboard.html', lots=lots, users=users)


@app.route('/admin/add_lot', methods=['GET', 'POST'])
def add_lot():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        prime_location_name = request.form.get('prime_location_name', '').strip()
        price = request.form.get('price')
        address = request.form.get('address', '').strip()
        pin_code = request.form.get('pin_code', '').strip()
        max_spots = request.form.get('max_spots')

        if not prime_location_name or not price or not max_spots:
            flash("Please provide all required fields.", "danger")
            return render_template('add_lot.html')

        try:
            price = float(price)
            max_spots = int(max_spots)
        except ValueError:
            flash("Price must be a number and max spots must be an integer.", "danger")
            return render_template('add_lot.html')

        conn = get_db()
        c = conn.cursor()
        c.execute("""INSERT INTO parking_lots (prime_location_name, price, address, pin_code, max_spots)
                     VALUES (?, ?, ?, ?, ?)""",
                  (prime_location_name, price, address, pin_code, max_spots))
        lot_id = c.lastrowid

        for _ in range(max_spots):
            c.execute("INSERT INTO parking_spots (lot_id, status) VALUES (?, 'A')", (lot_id,))
        conn.commit()
        conn.close()
        flash("Parking lot added successfully.", "success")
        return redirect(url_for('admin_dashboard'))
    return render_template('add_lot.html')


@app.route('/admin/delete_lot/<int:lot_id>', methods=['POST'])
def delete_lot(lot_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('login'))

    conn = get_db()
    occupied_spot = conn.execute("SELECT * FROM parking_spots WHERE lot_id=? AND status='O'", (lot_id,)).fetchone()
    if occupied_spot:
        flash("Cannot delete lot: some spots are occupied.", "danger")
        conn.close()
        return redirect(url_for('admin_dashboard'))

    conn.execute("DELETE FROM parking_spots WHERE lot_id=?", (lot_id,))
    conn.execute("DELETE FROM parking_lots WHERE id=?", (lot_id,))
    conn.commit()
    conn.close()
    flash("Parking lot deleted.", "info")
    return redirect(url_for('admin_dashboard'))


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '').strip()
    conn = get_db()
    if query:
        results = conn.execute("SELECT * FROM parking_lots WHERE prime_location_name LIKE ?", (f'%{query}%',)).fetchall()
    else:
        results = conn.execute("SELECT * FROM parking_lots").fetchall()
    conn.close()
    return render_template('search_results.html', query=query, results=results)


@app.route('/user/dashboard')
def user_dashboard():
    if 'user_id' not in session or session.get('role') != 'user':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('login'))

    conn = get_db()
    lots = conn.execute("SELECT * FROM parking_lots").fetchall()
    reservations = conn.execute("""
        SELECT r.*, l.prime_location_name, s.id AS spot_number
        FROM reservations r
        JOIN parking_spots s ON r.spot_id = s.id
        JOIN parking_lots l ON s.lot_id = l.id
        WHERE r.user_id = ?
        ORDER BY r.parked_at DESC
    """, (session['user_id'],)).fetchall()
    conn.close()
    return render_template('user_dashboard.html', lots=lots, reservations=reservations)


@app.route('/user/reserve/<int:lot_id>', methods=['GET', 'POST'])
def reserve(lot_id):
    if 'user_id' not in session or session.get('role') != 'user':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        vehicle_number = request.form.get('vehicle_number', '').strip().upper()
        if not vehicle_number:
            flash("Vehicle number is required.", "danger")
            return render_template('reserve_spot.html', lot_id=lot_id)

        conn = get_db()
        spot = conn.execute("SELECT * FROM parking_spots WHERE lot_id=? AND status='A' LIMIT 1", (lot_id,)).fetchone()
        if not spot:
            flash("No available parking spots in this lot.", "warning")
            conn.close()
            return redirect(url_for('user_dashboard'))

        conn.execute("UPDATE parking_spots SET status='O' WHERE id=?", (spot['id'],))
        lot = conn.execute("SELECT price FROM parking_lots WHERE id=?", (lot_id,)).fetchone()
        now = datetime.now().isoformat(sep=' ', timespec='seconds')
        conn.execute("""INSERT INTO reservations (spot_id, user_id, vehicle_number, parked_at, status, cost)
                        VALUES (?, ?, ?, ?, 'booked', ?)""",
                     (spot['id'], session['user_id'], vehicle_number, now, lot['price'] if lot else 0))
        conn.commit()
        conn.close()
        flash("Spot successfully reserved!", "success")
        return redirect(url_for('user_dashboard'))

    # GET request show vehicle number input form
    return render_template('reserve_spot.html', lot_id=lot_id)


@app.route('/user/start_parking/<int:reservation_id>', methods=['POST'])
def start_parking(reservation_id):
    if 'user_id' not in session or session.get('role') != 'user':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('login'))

    now = datetime.now().isoformat(sep=' ', timespec='seconds')
    conn = get_db()
    res = conn.execute(
        "SELECT * FROM reservations WHERE id=? AND user_id=? AND status='booked'",
        (reservation_id, session['user_id'])
    ).fetchone()
    if not res:
        flash("Invalid reservation or already started.", "danger")
        conn.close()
        return redirect(url_for('user_dashboard'))

    conn.execute("UPDATE reservations SET status='parked', parked_at=? WHERE id=?", (now, reservation_id))
    conn.commit()
    conn.close()
    flash("Parking started.", "success")
    return redirect(url_for('user_dashboard'))


@app.route('/user/release/<int:reservation_id>', methods=['POST'])
def release(reservation_id):
    if 'user_id' not in session or session.get('role') != 'user':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('login'))

    now = datetime.now().isoformat(sep=' ', timespec='seconds')
    conn = get_db()
    res = conn.execute(
        "SELECT * FROM reservations WHERE id=? AND user_id=? AND status IN ('booked', 'parked')",
        (reservation_id, session['user_id'])
    ).fetchone()

    if not res:
        flash("Invalid reservation or already released.", "danger")
        conn.close()
        return redirect(url_for('user_dashboard'))

    # Calculate duration hours
    parked_at = res['parked_at']
    if parked_at:
        parked_time = datetime.fromisoformat(parked_at)
        duration_hours = (datetime.now() - parked_time).total_seconds() / 3600
        duration_hours = max(1, duration_hours)
    else:
        duration_hours = 1  # fallback duration

    lot = conn.execute("""
        SELECT l.price FROM parking_lots l
        JOIN parking_spots s ON s.lot_id = l.id
        WHERE s.id = ?
    """, (res['spot_id'],)).fetchone()
    price_per_hour = lot['price'] if lot else 0
    total_cost = round(price_per_hour * duration_hours, 2)

    conn.execute("UPDATE parking_spots SET status='A' WHERE id=?", (res['spot_id'],))
    conn.execute(
        "UPDATE reservations SET left_at=?, cost=?, status='released' WHERE id=?",
        (now, total_cost, reservation_id)
    )
    conn.commit()
    conn.close()

    flash(f"Spot released. Total cost: ₹{total_cost}", "success")
    return redirect(url_for('user_dashboard'))


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
