from config import db
from flask_marshmallow import Marshmallow

ma = Marshmallow()

class Event(db.Model):
    event_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    organizer = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=True)
    venue = db.Column(db.String(100), nullable=False)
    links = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=False)
    contact_details = db.Column(db.String(120), nullable=True)
    popularity = db.Column(db.Integer, default=0)
    participants = db.Column(db.Integer, default=0)
    category = db.Column(db.String(50), nullable=False)

class EventSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Event
        
event_schema = EventSchema()