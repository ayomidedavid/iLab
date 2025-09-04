from app import app, db, login_manager
from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, Device, Attendance, ActivityLog
from werkzeug.security import generate_password_hash, check_password_hash

@app.route('/')
def index():
    return "Lab Inventory & Management System API is running."

# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        email = request.form.get('email')
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('signup'))
        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            role=role,
            email=email
        )
        db.session.add(user)
        db.session.commit()
        flash('Signup successful! Please sign in.')
        return redirect(url_for('signin'))
    return render_template('signup.html')

# Signin route
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Login successful!')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
            return redirect(url_for('signin'))
    return render_template('signin.html')
