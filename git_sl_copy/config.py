from flask import Flask
import os
import uuid , pytz
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

database_dir = os.path.join(os.path.dirname(__file__), 'database')
if not os.path.exists(database_dir):
    os.makedirs(database_dir)

db_path = os.path.join(database_dir, 'event_management.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SECURE'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)

#student table for storing the details