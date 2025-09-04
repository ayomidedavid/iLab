import os

# Flask secret key
SECRET_KEY = os.environ.get('SECRET_KEY', 'your_secret_key')

# PyMySQL connection settings
MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
MYSQL_DB = os.environ.get('MYSQL_DB', 'lab_inventory_system')
