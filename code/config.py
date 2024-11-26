from flask import Flask
import os
import uuid , pytz
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from datetime import datetime, timedelta
from flask_apscheduler import APScheduler
import subprocess

app = Flask(__name__)
CORS(app)

database_dir = os.path.join(os.path.dirname(__file__), 'database')
if not os.path.exists(database_dir):
    os.makedirs(database_dir)

db_path = os.path.join(database_dir, 'event_management.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SECURE'] = False
app.config['GOOGLE_OAUTH_CLIENT_ID'] =
app.config['GOOGLE_OAUTH_CLIENT_SECRET'] =

db = SQLAlchemy(app)
ma = Marshmallow(app)

class Schedule:
    SCHEDULER_API_ENABLED = True

app.config.from_object(Schedule)

scheduler = APScheduler()
scheduler.init_app(app)

def run_scrape():
    subprocess.run(["python3", "scrape.py"], check=True)

def run_webmail_scrape():
    subprocess.run(["python3", "webmail_scrape.py"], check=True)

scheduler.add_job(id='scrape_job', func=run_scrape, trigger='interval', minutes=100)
scheduler.add_job(id='webmail_scrape_job', func=run_webmail_scrape, trigger='interval', minutes=100)
