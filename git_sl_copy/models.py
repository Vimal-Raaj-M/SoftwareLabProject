from config import db
from contextlib import redirect_stdout
import uuid , pytz, json
from datetime import datetime, timedelta
from flask_marshmallow import Marshmallow
from flask_dance.contrib.google import google
from flask import session

ma = Marshmallow()

class Users_Info(db.Model):
    __tablename__='user_info'
    user_id=db.Column(db.String(40),primary_key=True,unique=True)
    email_id=db.Column(db.String(40),unique=True,nullable=False)
    refresh_token=db.Column(db.String(200),nullable=False)

    def __init__(self, email_id, refresh_token):
        self.user_id = str(uuid.uuid4())  
        self.email_id = email_id            
        self.refresh_token = refresh_token 

    events=db.relationship('Users_Events_Map',backref='user',lazy=True)


class Users_Events_Map(db.Model):
    __tablename__='user_event_map'
    user_id=db.Column(db.String(40),db.ForeignKey('user_info.user_id'),nullable=False)
    event_id=db.Column(db.String(30),nullable=False)
    c_event_id=db.Column(db.String(40),nullable=False)
    event_type=db.Column(db.String(10),nullable=False)
    __table_args__=(db.PrimaryKeyConstraint(user_id,event_id),)

class Public_Events(db.Model):
    __tablename__='public_events'
    user_id=db.Column(db.String(40),nullable=False)
    event_id=db.Column(db.String(40), primary_key=True)
    summary=db.Column(db.String(100), nullable=False)
    location=db.Column(db.String(100))
    description=db.Column(db.String(255))
    start_datetime=db.Column(db.DateTime, nullable=False)
    end_datetime=db.Column(db.DateTime, nullable=False)
    timezone=db.Column(db.String(50), default='Asia/Kolkata')  
    attendees=db.Column(db.JSON)
    use_default_reminders=db.Column(db.Boolean, default=False)
    reminder_minutes=db.Column(db.Integer, default=10)
    category=db.Column(db.String(20),nullable=False)
    popularity=db.Column(db.Integer,nullable=False)

    def __init__(self, user_id,summary, location, description, start_time=None, end_time=None, attendees=None, timezone="Asia/Kolkata", reminder_minutes=10, category='miscellaneous',popularity=0,event_id=None):
        self.event_id= event_id or str(uuid.uuid4())
        self.user_id = user_id
        self.summary=summary
        self.location=location
        self.description=description
        self.start_datetime=start_time or (datetime.now(pytz.timezone('Asia/Kolkata')) + timedelta(hours=1))  # Timezone-aware datetime
        self.end_datetime=end_time or (self.start_datetime + timedelta(hours=2))
        self.timezone=timezone
        self.attendees=attendees or [{'email': 'test@example.com'}]
        self.use_default_reminders = False
        self.reminder_minutes = reminder_minutes
        self.category=category
        self.popularity=popularity

    __table_args__=(db.PrimaryKeyConstraint(event_id),)

class Private_Events(db.Model):
    __tablename__='private_events'
    user_id=db.Column(db.String(40),nullable=False)
    event_id=db.Column(db.String(40), primary_key=True)
    summary=db.Column(db.String(100), nullable=False)
    location=db.Column(db.String(100))
    description=db.Column(db.String(255))
    start_datetime=db.Column(db.DateTime, nullable=False)
    end_datetime=db.Column(db.DateTime, nullable=False)
    timezone=db.Column(db.String(50), default='Asia/Kolkata')  
    attendees=db.Column(db.JSON)
    use_default_reminders=db.Column(db.Boolean, default=False)
    reminder_minutes=db.Column(db.Integer, default=10)
    category=db.Column(db.String(20),nullable=False)

    def __init__(self,user_id, summary, location, description, start_time=None, end_time=None, attendees=None, timezone="Asia/Kolkata",reminder_minutes=10,category='miscellaneous'):
        self.user_id=user_id
        self.event_id=str(uuid.uuid4())
        self.summary=summary
        self.location=location
        self.description=description
        self.start_datetime=start_time or (datetime.now(pytz.timezone('Asia/Kolkata')) + timedelta(hours=1))  # Timezone-aware datetime
        self.end_datetime=end_time or (self.start_datetime + timedelta(hours=2))
        self.timezone=timezone
        self.attendees=attendees or [{'email': 'test@example.com'}]
        self.use_default_reminders = False
        self.reminder_minutes = reminder_minutes
        self.category=category

    __table_args__=(db.PrimaryKeyConstraint(event_id),)


# class Event(db.Model):
#     event_id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), nullable=False)
#     organizer = db.Column(db.String(100), nullable=False)
#     date = db.Column(db.Date, nullable=True)
#     start_time = db.Column(db.Time, nullable=False)
#     end_time = db.Column(db.Time, nullable=True)
#     venue = db.Column(db.String(100), nullable=False)
#     links = db.Column(db.String(100), nullable=True)
#     description = db.Column(db.Text, nullable=False)
#     contact_details = db.Column(db.String(120), nullable=True)
#     popularity = db.Column(db.Integer, default=0)
#     participants = db.Column(db.Integer, default=0)
#     category = db.Column(db.String(50), nullable=False)

class EventSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Public_Events
        
event_schema = EventSchema()

class Events:
    def __init__(self, summary, location, description, start_time=None, end_time=None, attendees=None, timezone='Asia/Kolkata', reminder_minutes=10):
        self.summary = summary
        self.location = location
        self.description = description
        self.start_datetime=start_time or (datetime.now(pytz.timezone('Asia/Kolkata')) + timedelta(hours=1))  # Timezone-aware datetime
        self.end_datetime=end_time or (self.start_datetime + timedelta(hours=2))
        self.timezone = timezone
        self.attendees = attendees or [{'email': 'test@example.com'}]
        self.reminder_minutes = reminder_minutes

    def to_google_event(self):
        event_data = {
            'summary': self.summary,
            'location': self.location,
            'description': self.description,
            'start': {
                'dateTime': self.start_datetime.isoformat(),
                'timeZone': self.timezone,
            },
            'end': {
                'dateTime': self.end_datetime.isoformat(),
                'timeZone': self.timezone,
            },
            'attendees': self.attendees,
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': self.reminder_minutes},
                ],
            },
        }
        return event_data

    def add_to_google_calendar(self):
        if not google.authorized:
            return "Google authentication required."
        event_data = self.to_google_event()
        response = google.post(
            'https://www.googleapis.com/calendar/v3/calendars/primary/events',
            json=event_data
        )
        with open('event_creation.txt','w') as cout:
            with redirect_stdout(cout):
                print(json.dumps(response.json(), indent=4))
        if response.status_code == 200:
            session["creation_response"]=dict(response.json())
            return "yes"
        else:
            return "no"
