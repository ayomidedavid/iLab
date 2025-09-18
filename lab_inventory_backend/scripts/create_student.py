#!/usr/bin/env python3
"""
create_student.py

Creates a student user in the app database.

Usage: run from your project root with your virtualenv activated:
  python lab_inventory_backend/scripts/create_student.py

The script will prompt for DB credentials (or read from env vars: DB_HOST, DB_USER, DB_PASS, DB_NAME, DB_PORT).
It will generate a strong password by default and print it at the end.
"""
import os
import sys
import getpass
import secrets
import string

try:
    import pymysql
except Exception:
    print("pymysql is required. Install with: pip install pymysql")
    sys.exit(1)

try:
    from werkzeug.security import generate_password_hash
except Exception:
    print("werkzeug is required. Install with: pip install werkzeug")
    sys.exit(1)

DEFAULT_USERNAME = 'student01'
DEFAULT_EMAIL = 'student01@example.com'
DEFAULT_ROLE = 'Student'


def input_default(prompt, default):
    val = input(f"{prompt} [{default}]: ")
    return val.strip() or default


def generate_password(length=14):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*-_"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def main():
    print("Create student account script")

    db_host = os.environ.get('DB_HOST') or input_default('DB host', 'localhost')
    db_user = os.environ.get('DB_USER') or input_default('DB user', 'root')
    db_pass = os.environ.get('DB_PASS') or getpass.getpass('DB password (leave empty for none): ')
    db_name = os.environ.get('DB_NAME') or input_default('DB name', 'ilab')
    db_port = int(os.environ.get('DB_PORT') or input_default('DB port', '3306'))

    username = input_default('Username', DEFAULT_USERNAME)
    email = input_default('Email', DEFAULT_EMAIL)
    role = input_default('Role', DEFAULT_ROLE)

    pw_choice = input_default('Press Enter to generate a secure password, or type a password to use', '')
    if pw_choice:
        password = pw_choice
    else:
        password = generate_password()

    print('\nCreating user:')
    print('  username:', username)
    print('  email:', email)
    print('  role:', role)

    password_hash = generate_password_hash(password)

    conn = None
    try:
        conn = pymysql.connect(host=db_host, user=db_user, password=db_pass, db=db_name, port=db_port,
                               cursorclass=pymysql.cursors.DictCursor)
        with conn.cursor() as cur:
            # Check if username exists
            cur.execute("SELECT id, username FROM users WHERE username=%s", (username,))
            existing = cur.fetchone()
            if existing:
                print('\nA user with that username already exists in the database:')
                print('  id:', existing.get('id'), 'username:', existing.get('username'))
                ans = input_default('Do you want to overwrite this user (yes to overwrite)', 'no')
                if ans.lower() not in ('y', 'yes'):
                    print('Aborting. No changes made.')
                    return
                # Attempt update
                try:
                    cur.execute("UPDATE users SET password_hash=%s, role=%s, email=%s, status=%s WHERE username=%s",
                                (password_hash, role, email, 'active', username))
                    conn.commit()
                    print('\nUpdated existing user with new password and role.')
                except Exception as e:
                    print('Failed to update user:', e)
                    return
            else:
                # Insert new user
                try:
                    cur.execute(
                        "INSERT INTO users (uuid, username, password_hash, role, email, status) VALUES (UUID(), %s, %s, %s, %s, %s)",
                        (username, password_hash, role, email, 'active')
                    )
                    conn.commit()
                    print('\nUser created successfully.')
                except Exception as e:
                    print('Failed to insert user:', e)
                    print('\nIf your users table has a different schema, use the SQL fallback below to adapt.')
                    # Print fallback SQL
                    fallback = f"INSERT INTO users (uuid, username, password_hash, role, email, status) VALUES (UUID(), '{username}', '{password_hash}', '{role}', '{email}', 'active');"
                    print('\nFallback SQL:')
                    print(fallback)
                    return

        print('\nCredentials:')
        print('  username:', username)
        print('  password:', password)
        print('\nStore the password securely. You can now sign in at http://localhost:5000/signin')

    except Exception as e:
        print('Connection failed:', e)
        print('\nIf you prefer, generate the password hash locally by running:')
        print("python -c \"from werkzeug.security import generate_password_hash; print(generate_password_hash('YOUR_PASSWORD'))\"")
        print('\nThen run an INSERT statement into your users table.')
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    main()
