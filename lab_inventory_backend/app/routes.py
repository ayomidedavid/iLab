from app import app, db, login_manager
from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, Device, Attendance, ActivityLog

@app.route('/')
def index():
    return "Lab Inventory & Management System API is running."

# Add more routes for login, user management, device management, attendance, etc.
