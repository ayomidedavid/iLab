from app import db
from flask_login import UserMixin
import uuid

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # Admin, Technician, Lecturer, Student, View-Only
    # ...additional fields...

class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(128), nullable=False)
    qr_code = db.Column(db.String(256))  # Path or data for QR code
    status = db.Column(db.String(20), default='available')
    # ...additional fields...

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    device_id = db.Column(db.Integer, db.ForeignKey('device.id'))
    timestamp = db.Column(db.DateTime, nullable=False)
    # ...additional fields...

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(128))
    timestamp = db.Column(db.DateTime, nullable=False)
    # ...additional fields...
