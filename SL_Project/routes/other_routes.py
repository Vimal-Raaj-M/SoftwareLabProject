from flask import Blueprint, render_template, jsonify, request
from models import Event, event_schema
from config import db
import json

other_routes = Blueprint('other_routes', __name__)

@other_routes.route('/')
def index():
    categories = db.session.query(Event.category).distinct().all()
    category_list = [category[0] for category in categories]

    return render_template('index.html', categories=category_list)

@other_routes.route('/api/events')
def get_events():
    events_by_category = {}
    
    categories = db.session.query(Event.category).distinct().all()
    
    for category in categories:
        category_name = category[0]
        events = Event.query.filter_by(category=category_name).all()
        events_by_category[category_name] = [event_schema.dump(event) for event in events]

    return jsonify(events_by_category)

@other_routes.route('/add_to_favorites', methods=['POST'])
def add_to_favorites():
    event_name = request.json.get('event_name')
    return jsonify({"message": f"'{event_name}' added to favorites!"})

events_data = {
    "registered": [
        {"id": 1, "name": "Art Workshop", "date": "2024-11-15", "location": "City Art Gallery", "popularity":1},
        {"id": 2, "name": "Tech Meetup", "date": "2024-11-20", "location": "Tech Park", "popularity":1},
    ],
    "private": [
        {"id": 3, "name": "Birthday Celebration", "date": "2024-12-01", "location": "John's Place", "popularity":1},
        {"id": 4, "name": "Private Yoga Session", "date": "2024-12-05", "location": "Local Yoga Center", "popularity":1},
    ],
    "hosted": [
        {"id": 5, "name": "Startup Pitch Night", "date": "2024-12-10", "location": "Innovation Hub"},
        {"id": 6, "name": "Book Reading Event", "date": "2024-12-15", "location": "Community Library"},
    ]
}

@other_routes.route('/api/my-events/<string:event_type>', methods=['GET'])
def get_my_events(event_type):
    if event_type in events_data:
        return jsonify(events_data[event_type])
    else:
        return jsonify({"error": "Event type not found"}), 404