from flask import Blueprint, render_template, jsonify, request ,session 
from config import app,db
from models import Users_Info,Users_Events_Map,Private_Events,Public_Events,event_schema,Events
from flask_dance.contrib.google import google
from contextlib import redirect_stdout
from datetime import datetime, timedelta



other_routes = Blueprint('other_routes', __name__)

events_data = {
    "registered": [],
    "private": [],
    "hosted": []
}

def populate_my_events():

    # Fetch private events for the user
    private_events = db.session.query(Private_Events).join(
        Users_Events_Map,
        Users_Events_Map.event_id == Private_Events.event_id
    ).filter(
        Users_Events_Map.event_type == 'Private', 
        Users_Events_Map.user_id == Private_Events.users_id,  
    ).all()
    print(private_events)
    
    # Append private events to events_data if not already present
    for event in private_events:
        event_data = {
            "id": event.event_id,  
            "summary": event.summary,  
            "date": event.start_datetime.strftime("%Y-%m-%d"),  
            "location": event.location,
            "popularity": 1  
        }
        
        # Check if the event_id already exists in the private list
        if not any(existing_event["id"] == event.event_id for existing_event in events_data["private"]):
            events_data["private"].append(event_data)

    # Fetch hosted public events for the user
    hosted_events = db.session.query(Public_Events).join(
        Users_Events_Map,
        Users_Events_Map.event_id == Public_Events.event_id
    ).filter(
        Users_Events_Map.event_type == 'Public', 
        Users_Events_Map.user_id == Public_Events.user_id  
    ).all()

    # Append hosted events to events_data if not already present
    for event in hosted_events:
        event_data = {
            "id": event.event_id,  
            "summary": event.summary,  
            "date": event.start_datetime.strftime("%Y-%m-%d"),  
            "location": event.location,
            "popularity": event.popularity  
        }
        
        # Check if the event_id already exists in the hosted list
        if not any(existing_event["id"] == event.event_id for existing_event in events_data["hosted"]):
            events_data["hosted"].append(event_data)

    # Fetch registered public events (those the user is not hosting)
    registered_events = db.session.query(Public_Events).join(
        Users_Events_Map,
        Users_Events_Map.event_id == Public_Events.event_id
    ).filter(
        Users_Events_Map.event_type == 'Public', 
        Users_Events_Map.user_id != Public_Events.user_id   
    ).all()

    # Append registered events to events_data if not already present
    for event in registered_events:
        event_data = {
            "id": event.event_id,  
            "summary": event.summary,  
            "date": event.start_datetime.strftime("%Y-%m-%d"),  
            "location": event.location,
            "popularity": event.popularity  
        }
        
        # Check if the event_id already exists in the registered list
        if not any(existing_event["id"] == event.event_id for existing_event in events_data["registered"]):
            events_data["registered"].append(event_data)

    # Set session flag to False to mark that data is populated
    session["populate"] = False

def add_user_to_users_Info():
    temp=Users_Info.query.filter_by(email_id=session["email"]).all()
    print("inside add 1")
    if not temp:
        print("inside add 2")

        new_student=Users_Info(
            email_id=session["email"],
            refresh_token=session["google_token"]["refresh_token"]
        )
        db.session.add(new_student)
        db.session.commit()

    user_id=Users_Info.query.filter_by(email_id=session["email"]).first()
    session["user_id"]=user_id.user_id

@other_routes.route('/gauthorized')
def gauthorized():
    
    response=google.get("https://www.googleapis.com/oauth2/v2/userinfo")
    if response.status_code==200:
        response=response.json()
        session["email"]=response["email"]
        session["name"]=response["name"]
    else: 
        return f"Error on access the user info code :{response.status_code}"

    token=google.token
    session['google_token']=token

    if google.token['expires_in']<=0:
       google.refresh_token(token['refresh_token'])
       with open('log_output.txt','w') as cout:
           with redirect_stdout(cout):
               print(f"Changing the token with refresh token for user : {session['email']}")
           
    add_user_to_users_Info()

    categories = Public_Events.query.with_entities(Public_Events.category).distinct().all()
    populate_my_events()
    category_list = [category[0] for category in categories]

    return render_template('index.html', categories=category_list)

@other_routes.route('/api/events')
def get_events():
    events_by_category = {}
    
    categories = db.session.query(Public_Events.category).distinct().all()
    
    for category in categories:
        category_name = category[0]
        events = Public_Events.query.filter_by(category=category_name).all()
        events_by_category[category_name] = [event_schema.dump(event) for event in events]

    return jsonify(events_by_category)

@other_routes.route('/add_to_favorites', methods=['POST'])
def add_to_favorites():
    event_name = request.json.get('event_name')
    return jsonify({"message": f"'{event_name}' added to favorites!"})


@other_routes.route('/api/my-events/<string:event_type>', methods=['GET'])
def get_my_events(event_type):

    if event_type in events_data:
        return jsonify(events_data[event_type])
    else:
        return jsonify({"error": "Event type not found"}), 404

@other_routes.route('/api/my-events/add_event/<int:event_id>/<string:event_type>', methods=['POST'])
def add_event(event_id,event_type):
    try:
        # Check if the event exists using the event_id from the URL parameter
        event = Public_Events.query.get(event_id)
        if not event:
            return jsonify({"success": False, "message": "Event not found."}), 404

        # For example, you would get this from the session or authentication context
        existing_event = Users_Events_Map.query.filter_by(user_id=session["user_id"], event_id=event_id).first()

        if existing_event:
            return jsonify({"success": False, "message": "Event already added."}), 409

        new_event=Events(
            summary=event.summary,
            location=event.location,
            description=event.description,
            start_time=event.start_datetime,
            end_time=event.end_datetime,
            attendees=session["email"],
            timezone=event.timezone,
            reminder_minutes=event.reminder_minutes
        )

        valid=new_event.add_to_google_calendar()
        # Add the event to UserEvent table
        if valid == "yes":
            user_event =Users_Events_Map(
                user_id=session["user_id"],
                event_id=event_id,
                c_event_id=session["creation_response"]["id"],
                event_type=event_type
                )
            db.session.add(user_event)
            db.session.commit()
        # Respond with success
            return jsonify({"success": True, "message": "Event successfully added to your list!"}), 200
        else :
            return jsonify({"success": False, "message": "Failed To add in Google Calendar"}), 200

    except Exception as e:
        db.session.rollback()  # Ensure the session is rolled back in case of error
        print(f"Error: {e}")
        return jsonify({"success": False, "message": "An error occurred. Please try again."}), 500
