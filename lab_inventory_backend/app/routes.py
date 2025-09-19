from flask import send_file
from app import app
from flask import render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.db import get_db_connection



@app.route('/technician/assets')
def technician_assets():
    if 'user_id' not in session or session.get('role') != 'technician':
        return redirect(url_for('signin'))
    conn = get_db_connection()
    systems = []
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM assets ORDER BY asset_id ASC')
            systems = cursor.fetchall()
    finally:
        conn.close()
    return render_template('technician_assets.html', systems=systems, current_user=session)
from flask import send_file

@app.route('/admin/users')
def users():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('signin'))
    conn = get_db_connection()
    users = []
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM users ORDER BY role ASC')
            users = cursor.fetchall()
    finally:
        conn.close()
    return render_template('users.html', users=users, current_user=session)



@app.route('/admin/inventory')
def inventory():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('signin'))
    conn = get_db_connection()
    systems = []
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM assets ORDER BY asset_id ASC')
            systems = cursor.fetchall()
    finally:
        conn.close()
    return render_template('inventory.html', systems=systems, current_user=session)



#  View all active assets in a table (admin only)
@app.route('/admin/assets/active')
def view_active_assets():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('signin'))
    conn = get_db_connection()
    assets = []
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM assets WHERE status='working' ORDER BY asset_id ASC")
            assets = cursor.fetchall()
    finally:
        conn.close()
    return render_template('assets_table.html', assets=assets, current_user=session, systems=[], recent_activity=[], maintenance_list=[], notifications=[], audit_logs=[])
# Serve QR code image for asset


# View all assets in a table
@app.route('/admin/assets')
def view_assets():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('signin'))
    conn = get_db_connection()
    assets = []
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM assets ORDER BY asset_id ASC')
            assets = cursor.fetchall()
    finally:
        conn.close()
    return render_template('assets_table.html', assets=assets, current_user=session, systems=[], recent_activity=[], maintenance_list=[], notifications=[], audit_logs=[])

# Edit asset
@app.route('/admin/assets/edit/<asset_id>', methods=['GET', 'POST'])
def edit_asset(asset_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('signin'))
    conn = get_db_connection()
    asset = None
    try:
        with conn.cursor() as cursor:
            if request.method == 'POST':
                fields = ['device_name', 'manufacturer', 'model', 'serial_number', 'os', 'cpu', 'ram', 'storage', 'location', 'status', 'mouse', 'keyboard', 'power_pack']
                values = [request.form.get(f) for f in fields]
                update_sql = """
                    UPDATE assets SET device_name=%s, manufacturer=%s, model=%s, serial_number=%s, os=%s, cpu=%s, ram=%s, storage=%s, location=%s, status=%s, mouse=%s, keyboard=%s, power_pack=%s WHERE asset_id=%s
                """
                cursor.execute(update_sql, (*values, asset_id))
                conn.commit()
                flash('Asset updated successfully.')
                return redirect(url_for('view_assets'))
            cursor.execute('SELECT * FROM assets WHERE asset_id=%s', (asset_id,))
            asset = cursor.fetchone()
    finally:
        conn.close()
    return render_template('add_asset.html', asset=asset, edit_mode=True)

# Delete asset
@app.route('/admin/assets/delete/<asset_id>', methods=['POST'])
def delete_asset(asset_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('signin'))
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('DELETE FROM assets WHERE asset_id=%s', (asset_id,))
            conn.commit()
            flash('Asset deleted successfully.')
    finally:
        conn.close()
    return redirect(url_for('view_assets'))

@app.route('/asset_qr/<asset_id>')
def asset_qr(asset_id):
    import os
    qr_dir = os.path.join(os.path.dirname(__file__), 'qrcodes')
    qr_path = os.path.join(qr_dir, f'{asset_id}.png')
    if os.path.exists(qr_path):
        return send_file(qr_path, mimetype='image/png')
    else:
        flash('QR code not found for this asset.')
        return redirect(url_for('asset_info', asset_id=asset_id))


# Technician: Asset access redirect (QR/manual)
@app.route('/asset_info_redirect')
def asset_info_redirect():
    asset_id = request.args.get('asset_id')
    if asset_id:
        return redirect(url_for('asset_info', asset_id=asset_id))
    else:
        flash('Please enter or scan a valid Asset ID.')
        return redirect(url_for('technician_dashboard'))


# Decommission asset route
@app.route('/decommission_asset/<asset_id>', methods=['POST'])
def decommission_asset(asset_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE assets SET status=%s WHERE asset_id=%s", ('decommissioned', asset_id))
            conn.commit()
            flash('Asset decommissioned successfully.')
    except Exception:
        flash('Failed to decommission asset.')
    finally:
        conn.close()
    return redirect(url_for('asset_info', asset_id=asset_id))



# Technician: Add new asset
@app.route('/add_asset', methods=['GET', 'POST'])
def add_asset():
    if 'user_id' not in session or session.get('role') not in ['technician', 'admin']:
        flash('Only technicians and admins can add new assets.')
        return redirect(url_for('signin'))
    if request.method == 'POST':
        fields = ['device_name', 'manufacturer', 'model', 'serial_number', 'os', 'cpu', 'ram', 'storage', 'location', 'status', 'mouse', 'keyboard', 'power_pack']
        values = []
        # Get main fields
        allowed_status = ['GOOD', 'FAULTY', 'DECOMMISSIONED']
        for f in fields:
            val = request.form.get(f)
            # Handle custom 'Other' values for dropdowns
            if f == 'model' and val == 'Other':
                val = request.form.get('model_other') or 'Other'
            if f == 'cpu' and val == 'Other':
                val = request.form.get('cpu_other') or 'Other'
            if f == 'ram' and val == 'Other':
                val = request.form.get('ram_other') or 'Other'
            if f == 'location' and val == 'Other':
                val = request.form.get('location_other') or 'Other'
            if f == 'storage' and val == 'Other':
                val = request.form.get('storage_other') or 'Other'
            if f == 'status':
                if val not in allowed_status:
                    val = 'GOOD'  # fallback to default
            values.append(val)
        # Auto-generate asset_id and uuid
        import uuid, os, qrcode
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT COUNT(*) AS cnt FROM assets')
                count = cursor.fetchone()['cnt'] + 1
                asset_id = f"ASSET{count:04d}"
                asset_uuid = str(uuid.uuid4())
                insert_sql = """
                    INSERT INTO assets (asset_id, device_name, manufacturer, model, serial_number, os, cpu, ram, storage, location, status, mouse, keyboard, power_pack, uuid)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_sql, (asset_id, *values, asset_uuid))
                conn.commit()
                # Generate QR code for the new asset
                qr_dir = os.path.join(os.path.dirname(__file__), 'qrcodes')
                os.makedirs(qr_dir, exist_ok=True)
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(asset_id)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                qr_path = os.path.join(qr_dir, f'{asset_id}.png')
                img.save(qr_path)
                flash('New asset added successfully! QR code generated.')
                return redirect(url_for('asset_info', asset_id=asset_id))
        except Exception:
            flash('Failed to add new asset.')
        finally:
            conn.close()
    return render_template('add_asset.html')


# Lecturer: Start new session
@app.route('/lecturer/session/start', methods=['POST'])
def lecturer_start_session():
    if 'user_id' not in session or session.get('role') != 'lecturer':
        flash('Only lecturers can start sessions.')
        return redirect(url_for('signin'))
    name = request.form.get('name')
    date = request.form.get('date')
    time = request.form.get('time')
    lecturer_id = session.get('user_id')
    if not name or not date or not time:
        flash('Please provide all session details.')
        return redirect(url_for('lecturer_dashboard'))
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO sessions (name, date, time, lecturer_id, status)
                VALUES (%s, %s, %s, %s, %s)
            """, (name, date, time, lecturer_id, 'active'))
            conn.commit()
        flash('Session started successfully!')
    except Exception as e:
        flash('Error starting session: ' + str(e))
    finally:
        conn.close()
    return redirect(url_for('lecturer_dashboard'))

@app.route('/asset/<asset_id>', methods=['GET', 'POST'])
def asset_info(asset_id):
    from app.db import get_db_connection
    conn = get_db_connection()
    if request.method == 'POST' and session.get('role') == 'technician':
        # Update asset info
        fields = ['device_name', 'manufacturer', 'model', 'serial_number', 'os', 'cpu', 'ram', 'storage', 'location', 'status']
        values = [request.form.get(f) for f in fields]
        update_sql = """
            UPDATE assets SET device_name=%s, manufacturer=%s, model=%s, serial_number=%s, os=%s, cpu=%s, ram=%s, storage=%s, location=%s, status=%s
            WHERE asset_id=%s
        """
        try:
            with conn.cursor() as cursor:
                cursor.execute(update_sql, (*values, asset_id))
                conn.commit()
                flash('Asset information updated successfully.')
        except Exception:
            flash('Failed to update asset information.')
    # Fetch asset info
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM assets WHERE asset_id = %s', (asset_id,))
            asset = cursor.fetchone()
    finally:
        conn.close()
    return render_template('asset_info.html', asset=asset)

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
    systems_tables = ['assets']
    activity_tables = ['activity_logs', 'activity', 'logs']
    maintenance_tables = ['maintenance', 'maintenance_queue', 'repairs']
    notifications_tables = ['notifications', 'alerts']
    audit_tables = ['audit_logs', 'audits']
    users_table = 'users'

    # User role counts
    student_count = lecturer_count = technician_count = admin_count = viewer_count = 0

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
                        # Also fetch all assets for the systems list
                        cursor.execute(f"SELECT id, uuid, asset_id, device_name, manufacturer, model, serial_number, os, cpu, ram, storage, location, purchase_date, warranty_expiry, picture_path, status, mouse, keyboard, power_pack, created_at FROM `{t}` ORDER BY id ASC LIMIT 100")
                        systems = cursor.fetchall() or []
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
                    cursor.execute(f"SELECT id, uuid, asset_id, device_name, manufacturer, model, serial_number, os, cpu, ram, storage, location, purchase_date, warranty_expiry, picture_path, status, mouse, keyboard, power_pack, created_at FROM `{systems_table_found}` ORDER BY id ASC LIMIT 100")
                    systems = cursor.fetchall() or []
                except Exception:
                    systems = []

            # Users and role counts
            try:
                cursor.execute(f"SELECT username, role, status FROM `{users_table}` ORDER BY id DESC LIMIT 100")
                users = cursor.fetchall() or []
                # Count users by role
                cursor.execute(f"SELECT role, COUNT(*) AS cnt FROM `{users_table}` GROUP BY role")
                for r in cursor.fetchall():
                    role = (r.get('role') or '').lower()
                    cnt = r.get('cnt', 0)
                    if role == 'student':
                        student_count = cnt
                    elif role == 'lecturer':
                        lecturer_count = cnt
                    elif role == 'technician':
                        technician_count = cnt
                    elif role == 'admin':
                        admin_count = cnt
                    elif role == 'viewer':
                        viewer_count = cnt
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
                           usage_series=usage_series,
                           student_count=student_count, lecturer_count=lecturer_count,
                           technician_count=technician_count, admin_count=admin_count,
                           viewer_count=viewer_count)

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
