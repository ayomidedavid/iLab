from app import app
from flask import render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.db import get_db_connection

# Signout route
@app.route('/signout')
def signout():
    session.clear()
    flash('You have been signed out.')
    return redirect(url_for('signin'))


@app.route('/studentdashboard')
def student_dashboard():
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('signin'))
    user_id = session.get('user_id')
    assigned_system = None
    notifications = []
    recent_activity = []
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Find assigned system for student
            try:
                cursor.execute("SELECT uuid, hostname, location, status FROM devices WHERE assigned_to=%s LIMIT 1", (session.get('username'),))
                assigned_system = cursor.fetchone()
                if not assigned_system:
                    cursor.execute("SELECT uuid, hostname, location, status FROM systems WHERE assigned_to=%s LIMIT 1", (session.get('username'),))
                    assigned_system = cursor.fetchone()
            except Exception:
                assigned_system = None

            # Notifications
            try:
                cursor.execute("SELECT message, timestamp AS time FROM notifications WHERE user_id=%s ORDER BY timestamp DESC LIMIT 5", (user_id,))
                notifications = cursor.fetchall() or []
            except Exception:
                notifications = []

            # Recent activity
            try:
                cursor.execute("SELECT action AS message, timestamp AS time FROM activity_logs WHERE user_id=%s ORDER BY timestamp DESC LIMIT 5", (user_id,))
                recent_activity = cursor.fetchall() or []
            except Exception:
                recent_activity = []
    finally:
        conn.close()
    return render_template('studentdashboard.html', current_user=session, assigned_system=assigned_system, notifications=notifications, recent_activity=recent_activity)


@app.route('/admindashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('signin'))
    # Prepare defaults
    total_systems = 0
    active_count = faulty_count = maintenance_count = 0
    systems = []
    users = []
    recent_activity = []
    maintenance_list = []
    notifications = []
    audit_logs = []
    current_sessions = 0

    # Helper lists to try common table names
    systems_tables = ['devices', 'systems', 'assets', 'desktops']
    activity_tables = ['activity_logs', 'activity', 'logs']
    maintenance_tables = ['maintenance', 'maintenance_queue', 'repairs']
    notifications_tables = ['notifications', 'alerts']
    audit_tables = ['audit_logs', 'audits']
    users_table = 'users'

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Find systems table and counts
            systems_table_found = None
            for t in systems_tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) AS cnt FROM `{t}`")
                    row = cursor.fetchone()
                    if row and row.get('cnt') is not None:
                        total_systems = row['cnt']
                        systems_table_found = t
                        break
                except Exception:
                    continue

            # If a systems table was found, get status breakdown and a sample list
            if systems_table_found:
                try:
                    cursor.execute(f"SELECT status, COUNT(*) AS cnt FROM `{systems_table_found}` GROUP BY status")
                    for r in cursor.fetchall():
                        st = (r.get('status') or '').lower()
                        cnt = r.get('cnt', 0)
                        if st in ('active', 'working', 'running'):
                            active_count += cnt
                        elif st in ('faulty', 'broken'):
                            faulty_count += cnt
                        elif st in ('maintenance', 'repair'):
                            maintenance_count += cnt
                        else:
                            pass
                except Exception:
                    pass

                try:
                    cursor.execute(f"SELECT uuid, hostname, location, status, assigned_to FROM `{systems_table_found}` ORDER BY id DESC LIMIT 100")
                    systems = cursor.fetchall() or []
                except Exception:
                    systems = []

            # Users
            try:
                cursor.execute(f"SELECT username, role, status FROM `{users_table}` ORDER BY id DESC LIMIT 100")
                users = cursor.fetchall() or []
            except Exception:
                users = []

            # Recent activity
            activity_table_found = None
            for t in activity_tables:
                try:
                    cursor.execute(f"SELECT action AS message, timestamp AS time, user_id FROM `{t}` ORDER BY timestamp DESC LIMIT 25")
                    recent_activity = cursor.fetchall() or []
                    activity_table_found = t
                    break
                except Exception:
                    continue

            # Attempt to enrich recent activity with username if possible
            if recent_activity:
                for act in recent_activity:
                    try:
                        uid = act.get('user_id')
                        if uid:
                            cursor.execute("SELECT username FROM users WHERE id=%s", (uid,))
                            u = cursor.fetchone()
                            act['user'] = u['username'] if u else 'User ' + str(uid)
                        else:
                            act['user'] = 'System'
                    except Exception:
                        act['user'] = 'System'

            # Maintenance list
            maintenance_table_found = None
            for t in maintenance_tables:
                try:
                    cursor.execute(f"SELECT id, hostname, issue_summary, status, technician FROM `{t}` ORDER BY id DESC LIMIT 25")
                    maintenance_list = cursor.fetchall() or []
                    maintenance_table_found = t
                    break
                except Exception:
                    continue

            # Notifications
            for t in notifications_tables:
                try:
                    cursor.execute(f"SELECT message, timestamp AS time FROM `{t}` ORDER BY timestamp DESC LIMIT 10")
                    notifications = cursor.fetchall() or []
                    break
                except Exception:
                    continue

            # Audit logs
            for t in audit_tables:
                try:
                    cursor.execute(f"SELECT timestamp AS time, user_id AS user, action FROM `{t}` ORDER BY timestamp DESC LIMIT 25")
                    audit_logs = cursor.fetchall() or []
                    for a in audit_logs:
                        try:
                            uid = a.get('user')
                            if uid:
                                cursor.execute("SELECT username FROM users WHERE id=%s", (uid,))
                                uu = cursor.fetchone()
                                a['user'] = uu['username'] if uu else str(uid)
                        except Exception:
                            a['user'] = str(a.get('user'))
                    break
                except Exception:
                    continue

            # Current sessions - try sessions table
            try:
                cursor.execute("SELECT COUNT(*) AS cnt FROM sessions")
                r = cursor.fetchone()
                if r and r.get('cnt') is not None:
                    current_sessions = r['cnt']
            except Exception:
                current_sessions = 0

    finally:
        conn.close()

    usage_labels = ['6h', '5h', '4h', '3h', '2h', '1h', 'Now']
    usage_series = [2, 3, 5, 4, 6, 7, active_count or 0]

    return render_template('admindashboard.html', current_user=session,
                           systems=systems, users=users,
                           recent_activity=recent_activity, maintenance_list=maintenance_list,
                           notifications=notifications, audit_logs=audit_logs,
                           active_count=active_count, faulty_count=faulty_count,
                           maintenance_count=maintenance_count, total_systems=total_systems,
                           current_sessions=current_sessions, usage_labels=usage_labels,
                           usage_series=usage_series)

@app.route('/admin/users/approve', methods=['POST'])
def admin_approve_user():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('signin'))
    username = request.form.get('username')
    if not username:
        flash('No username provided for approval')
        return redirect(url_for('admin_dashboard'))
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE users SET status='active' WHERE username=%s AND status='pending'", (username,))
            conn.commit()
            flash(f"User '{username}' approved successfully.")
    except Exception:
        flash('Failed to approve user - database error')
    finally:
        conn.close()
    return redirect(url_for('admin_dashboard'))
    # Prepare defaults
    total_systems = 0
    active_count = faulty_count = maintenance_count = 0
    systems = []
    users = []
    recent_activity = []
    maintenance_list = []
    notifications = []
    audit_logs = []
    current_sessions = 0

    # Helper lists to try common table names
    systems_tables = ['devices', 'systems', 'assets', 'desktops']
    activity_tables = ['activity_logs', 'activity', 'logs']
    maintenance_tables = ['maintenance', 'maintenance_queue', 'repairs']
    notifications_tables = ['notifications', 'alerts']
    audit_tables = ['audit_logs', 'audits']
    users_table = 'users'

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Find systems table and counts
            systems_table_found = None
            for t in systems_tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) AS cnt FROM `{t}`")
                    row = cursor.fetchone()
                    if row and row.get('cnt') is not None:
                        total_systems = row['cnt']
                        systems_table_found = t
                        break
                except Exception:
                    continue

            # If a systems table was found, get status breakdown and a sample list
            if systems_table_found:
                try:
                    cursor.execute(f"SELECT status, COUNT(*) AS cnt FROM `{systems_table_found}` GROUP BY status")
                    for r in cursor.fetchall():
                        st = (r.get('status') or '').lower()
                        cnt = r.get('cnt', 0)
                        if st in ('active', 'working', 'running'):
                            active_count += cnt
                        elif st in ('faulty', 'broken'):
                            faulty_count += cnt
                        elif st in ('maintenance', 'repair'):
                            maintenance_count += cnt
                        else:
                            # other categories ignored for summary
                            pass
                except Exception:
                    pass

                try:
                    cursor.execute(f"SELECT uuid, hostname, location, status, assigned_to FROM `{systems_table_found}` ORDER BY id DESC LIMIT 100")
                    systems = cursor.fetchall() or []
                except Exception:
                    systems = []

            # Users
            try:
                cursor.execute(f"SELECT username, role, status FROM `{users_table}` ORDER BY id DESC LIMIT 100")
                users = cursor.fetchall() or []
            except Exception:
                users = []

            # Recent activity
            activity_table_found = None
            for t in activity_tables:
                try:
                    cursor.execute(f"SELECT action AS message, timestamp AS time, user_id FROM `{t}` ORDER BY timestamp DESC LIMIT 25")
                    recent_activity = cursor.fetchall() or []
                    activity_table_found = t
                    break
                except Exception:
                    continue

            # Attempt to enrich recent activity with username if possible
            if recent_activity:
                for act in recent_activity:
                    try:
                        uid = act.get('user_id')
                        if uid:
                            cursor.execute("SELECT username FROM users WHERE id=%s", (uid,))
                            u = cursor.fetchone()
                            act['user'] = u['username'] if u else 'User ' + str(uid)
                        else:
                            act['user'] = 'System'
                    except Exception:
                        act['user'] = 'System'

            # Maintenance list
            maintenance_table_found = None
            for t in maintenance_tables:
                try:
                    cursor.execute(f"SELECT id, hostname, issue_summary, status, technician FROM `{t}` ORDER BY id DESC LIMIT 25")
                    maintenance_list = cursor.fetchall() or []
                    maintenance_table_found = t
                    break
                except Exception:
                    continue

            # Notifications
            for t in notifications_tables:
                try:
                    cursor.execute(f"SELECT message, timestamp AS time FROM `{t}` ORDER BY timestamp DESC LIMIT 10")
                    notifications = cursor.fetchall() or []
                    break
                except Exception:
                    continue

            # Audit logs
            for t in audit_tables:
                try:
                    cursor.execute(f"SELECT timestamp AS time, user_id AS user, action FROM `{t}` ORDER BY timestamp DESC LIMIT 25")
                    audit_logs = cursor.fetchall() or []
                    # map user ids to names where possible
                    for a in audit_logs:
                        try:
                            uid = a.get('user')
                            if uid:
                                cursor.execute("SELECT username FROM users WHERE id=%s", (uid,))
                                uu = cursor.fetchone()
                                a['user'] = uu['username'] if uu else str(uid)
                        except Exception:
                            a['user'] = str(a.get('user'))
                    break
                except Exception:
                    continue

            # Current sessions - try sessions table
            try:
                cursor.execute("SELECT COUNT(*) AS cnt FROM sessions")
                r = cursor.fetchone()
                if r and r.get('cnt') is not None:
                    current_sessions = r['cnt']
            except Exception:
                current_sessions = 0

    finally:
        conn.close()

    # Usage data placeholders (charts)
    usage_labels = ['6h', '5h', '4h', '3h', '2h', '1h', 'Now']
    usage_series = [2, 3, 5, 4, 6, 7, active_count or 0]

    return render_template('admindashboard.html', current_user=session,
                           systems=systems, users=users,
                           recent_activity=recent_activity, maintenance_list=maintenance_list,
                           notifications=notifications, audit_logs=audit_logs,
                           active_count=active_count, faulty_count=faulty_count,
                           maintenance_count=maintenance_count, total_systems=total_systems,
                           current_sessions=current_sessions, usage_labels=usage_labels,
                           usage_series=usage_series)


# POST: Add new desktop
@app.route('/admin/assets/add', methods=['POST'])
def admin_add_asset():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('signin'))
    uuid_val = request.form.get('uuid')
    hostname = request.form.get('hostname')
    location = request.form.get('location')
    status = request.form.get('status', 'working')

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            try:
                cursor.execute("INSERT INTO devices (uuid, hostname, location, status) VALUES (%s,%s,%s,%s)",
                               (uuid_val, hostname, location, status))
                conn.commit()
                flash('Desktop added successfully')
            except Exception:
                # try alternative table names
                try:
                    cursor.execute("INSERT INTO systems (uuid, hostname, location, status) VALUES (%s,%s,%s,%s)",
                                   (uuid_val, hostname, location, status))
                    conn.commit()
                    flash('Desktop added successfully')
                except Exception:
                    flash('Failed to add desktop - database error')
    finally:
        conn.close()
    return redirect(url_for('admin_dashboard'))


# POST: Create new user
@app.route('/admin/users/add', methods=['POST'])
def admin_add_user():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('signin'))
    username = request.form.get('username')
    email = request.form.get('email')
    role = request.form.get('role', 'Viewer')
    password = request.form.get('password')
    password_hash = generate_password_hash(password) if password else None

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            try:
                cursor.execute("INSERT INTO users (uuid, username, password_hash, role, email, status) VALUES (UUID(), %s, %s, %s, %s, %s)",
                               (username, password_hash, role, email, 'active'))
                conn.commit()
                flash('User created successfully')
            except Exception:
                flash('Failed to create user - database error')
    finally:
        conn.close()
    return redirect(url_for('admin_dashboard'))


# POST: Save basic system settings (branding/logo)
@app.route('/admin/settings', methods=['POST'])
def admin_settings():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('signin'))
    app_name = request.form.get('app_name')
    logo_path = request.form.get('logo_path')
    session_timeout = request.form.get('session_timeout')

    # This is a placeholder: implement persistence (db or config file) as needed
    flash('Settings saved (placeholder). To persist settings, implement storage in DB or config file.')
    return redirect(url_for('admin_dashboard'))


@app.route('/techniciandashboard')
def technician_dashboard():
    if 'user_id' not in session or session.get('role') != 'technician':
        return redirect(url_for('signin'))
    user_id = session.get('user_id')
    notifications = []
    recent_activity = []
    maintenance_list = []
    parts = []
    systems = []
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Maintenance queue
            try:
                cursor.execute("SELECT id, hostname, issue_summary, status FROM maintenance WHERE technician=%s ORDER BY id DESC LIMIT 25", (session.get('username'),))
                maintenance_list = cursor.fetchall() or []
            except Exception:
                maintenance_list = []

            # Notifications
            try:
                cursor.execute("SELECT message, timestamp AS time FROM notifications WHERE user_id=%s ORDER BY timestamp DESC LIMIT 5", (user_id,))
                notifications = cursor.fetchall() or []
            except Exception:
                notifications = []

            # Recent activity
            try:
                cursor.execute("SELECT action AS message, timestamp AS time FROM activity_logs WHERE user_id=%s ORDER BY timestamp DESC LIMIT 10", (user_id,))
                recent_activity = cursor.fetchall() or []
            except Exception:
                recent_activity = []

            # Parts inventory
            try:
                cursor.execute("SELECT id, name, available FROM parts ORDER BY name ASC LIMIT 50")
                parts = cursor.fetchall() or []
            except Exception:
                parts = []

            # Systems list for reporting issues
            try:
                cursor.execute("SELECT id, hostname FROM systems ORDER BY hostname ASC LIMIT 50")
                systems = cursor.fetchall() or []
            except Exception:
                systems = []
    finally:
        conn.close()
    return render_template('techniciandashboard.html', current_user=session, notifications=notifications, recent_activity=recent_activity, maintenance_list=maintenance_list, parts=parts, systems=systems)


@app.route('/lecturerdashboard')
def lecturer_dashboard():
    if 'user_id' not in session or session.get('role') != 'lecturer':
        return redirect(url_for('signin'))
    return render_template('lecturerdashboard.html', current_user=session)


@app.route('/viewonlydashboard')
def viewonly_dashboard():
    if 'user_id' not in session or session.get('role') != 'view-only':
        return redirect(url_for('signin'))
    total_systems = 0
    active_count = faulty_count = maintenance_count = 0
    systems = []
    notifications = []
    maintenance_list = []
    recent_activity = []
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Systems
            try:
                cursor.execute("SELECT uuid, hostname, location, status, assigned_to FROM systems ORDER BY id DESC LIMIT 100")
                systems = cursor.fetchall() or []
            except Exception:
                systems = []

            # Inventory summary
            try:
                cursor.execute("SELECT COUNT(*) AS cnt FROM systems")
                row = cursor.fetchone()
                if row and row.get('cnt') is not None:
                    total_systems = row['cnt']
                cursor.execute("SELECT status, COUNT(*) AS cnt FROM systems GROUP BY status")
                for r in cursor.fetchall():
                    st = (r.get('status') or '').lower()
                    cnt = r.get('cnt', 0)
                    if st in ('active', 'working', 'running'):
                        active_count += cnt
                    elif st in ('faulty', 'broken'):
                        faulty_count += cnt
                    elif st in ('maintenance', 'repair'):
                        maintenance_count += cnt
            except Exception:
                pass

            # Notifications
            try:
                cursor.execute("SELECT message, timestamp AS time FROM notifications ORDER BY timestamp DESC LIMIT 10")
                notifications = cursor.fetchall() or []
            except Exception:
                notifications = []

            # Maintenance queue
            try:
                cursor.execute("SELECT hostname, issue_summary, status, technician FROM maintenance ORDER BY id DESC LIMIT 25")
                maintenance_list = cursor.fetchall() or []
            except Exception:
                maintenance_list = []

            # Recent activity
            try:
                cursor.execute("SELECT action AS message, timestamp AS time, user_id FROM activity_logs ORDER BY timestamp DESC LIMIT 25")
                recent_activity = cursor.fetchall() or []
                for act in recent_activity:
                    try:
                        uid = act.get('user_id')
                        if uid:
                            cursor.execute("SELECT username FROM users WHERE id=%s", (uid,))
                            u = cursor.fetchone()
                            act['user'] = u['username'] if u else 'User ' + str(uid)
                        else:
                            act['user'] = 'System'
                    except Exception:
                        act['user'] = 'System'
            except Exception:
                recent_activity = []
    finally:
        conn.close()
    return render_template('viewonlydashboard.html', current_user=session, systems=systems, total_systems=total_systems, active_count=active_count, faulty_count=faulty_count, maintenance_count=maintenance_count, notifications=notifications, maintenance_list=maintenance_list, recent_activity=recent_activity)

@app.route('/')
def index():
    return render_template('index.html')

# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user_id' in session:
        # Redirect to the user's dashboard if already logged in
        role = session.get('role')
        if role == 'student':
            return redirect(url_for('student_dashboard'))
        elif role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif role == 'technician':
            return redirect(url_for('technician_dashboard'))
        elif role == 'lecturer':
            return redirect(url_for('lecturer_dashboard'))
        elif role == 'view-only':
            return redirect(url_for('viewonly_dashboard'))
        else:
            return redirect(url_for('signin'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        email = request.form.get('email')
        password_hash = generate_password_hash(password)
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
            user = cursor.fetchone()
            if user:
                flash('Username already exists')
                return redirect(url_for('signup'))
            cursor.execute("INSERT INTO users (uuid, username, password_hash, role, email, status) VALUES (UUID(), %s, %s, %s, %s, %s)",
                           (username, password_hash, role, email, 'pending'))
            conn.commit()
        conn.close()
        flash('Signup successful! Your account is pending approval by an admin.')
        return redirect(url_for('signin'))
    return render_template('signup.html')

# Signin route
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
            user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            flash('Login successful!')
            role = user['role']
            if role == 'student':
                return redirect(url_for('student_dashboard'))
            elif role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif role == 'technician':
                return redirect(url_for('technician_dashboard'))
            elif role == 'lecturer':
                return redirect(url_for('lecturer_dashboard'))
            elif role == 'view-only':
                return redirect(url_for('viewonly_dashboard'))
            else:
                return redirect(url_for('signin'))
        else:
            flash('Invalid username or password')
            return redirect(url_for('signin'))
    return render_template('signin.html')

# Dashboard route
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    return render_template('dashboard.html', current_user=session)
