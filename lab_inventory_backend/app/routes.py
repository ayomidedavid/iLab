
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
    return render_template('studentdashboard.html', current_user=session)


@app.route('/admindashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('signin'))
    return render_template('admindashboard.html', current_user=session)


@app.route('/techniciandashboard')
def technician_dashboard():
    if 'user_id' not in session or session.get('role') != 'technician':
        return redirect(url_for('signin'))
    return render_template('techniciandashboard.html', current_user=session)


@app.route('/lecturerdashboard')
def lecturer_dashboard():
    if 'user_id' not in session or session.get('role') != 'lecturer':
        return redirect(url_for('signin'))
    return render_template('lecturerdashboard.html', current_user=session)


@app.route('/viewonlydashboard')
def viewonly_dashboard():
    if 'user_id' not in session or session.get('role') != 'view-only':
        return redirect(url_for('signin'))
    return render_template('viewonlydashboard.html', current_user=session)

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
