-- Lab Inventory & Management System Database Initialization

CREATE DATABASE IF NOT EXISTS lab_inventory_system;
USE lab_inventory_system;

-- Users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    uuid CHAR(36) NOT NULL UNIQUE,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'technician', 'lecturer', 'student', 'view-only') NOT NULL,
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Assets table
CREATE TABLE assets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    uuid CHAR(36) NOT NULL UNIQUE,
    asset_id VARCHAR(50) NOT NULL UNIQUE,
    device_name VARCHAR(100),
    manufacturer VARCHAR(100),
    model VARCHAR(100),
    serial_number VARCHAR(100),
    os VARCHAR(50),
    cpu VARCHAR(50),
    ram VARCHAR(50),
    storage VARCHAR(50),
    location VARCHAR(100),
    purchase_date DATE,
    warranty_expiry DATE,
    status ENUM('working', 'needs_repair', 'decommissioned') DEFAULT 'working',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Class sessions table
CREATE TABLE class_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_name VARCHAR(100),
    session_date DATETIME,
    lab_location VARCHAR(100),
    lecturer_id INT,
    FOREIGN KEY (lecturer_id) REFERENCES users(id)
);

-- Device assignments table
CREATE TABLE device_assignments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT,
    student_id INT,
    asset_id INT,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES class_sessions(id),
    FOREIGN KEY (student_id) REFERENCES users(id),
    FOREIGN KEY (asset_id) REFERENCES assets(id)
);

-- Attendance table
CREATE TABLE attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT,
    student_id INT,
    asset_id INT,
    timestamp DATETIME,
    FOREIGN KEY (session_id) REFERENCES class_sessions(id),
    FOREIGN KEY (student_id) REFERENCES users(id),
    FOREIGN KEY (asset_id) REFERENCES assets(id)
);

-- Maintenance logs table
CREATE TABLE maintenance_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    asset_id INT,
    technician_id INT,
    event_type VARCHAR(50),
    description TEXT,
    event_date DATETIME,
    FOREIGN KEY (asset_id) REFERENCES assets(id),
    FOREIGN KEY (technician_id) REFERENCES users(id)
);

-- Audit log table
CREATE TABLE audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(255),
    details TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)