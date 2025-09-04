from flask import Flask
import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

from app import routes
