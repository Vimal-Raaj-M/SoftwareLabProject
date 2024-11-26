from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for, current_app
from config import app, db
from models import Users_Info, Users_Events_Map, Private_Events, Public_Events, event_schema, Events
from flask_dance.contrib.google import google
from contextlib import redirect_stdout
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from requests_oauthlib import OAuth2Session
from dateutil import parser

other_routes = Blueprint('other_routes', __name__)

events_data = dict()

def populate_my_events():
    global events_data
    events_data = {
        "registered": [],
        "private": [],
        "hosted": []
    }
    
    private_events = db.session.query(Private_Events).join(
        Users_Events_Map,
        Users_Events_Map.event_id == Private_Events.event_id
    ).filter(
        Users_Events_Map.event_type == 'Private', 
        session["user_id"] == Private_Events.user_id,  
    ).all()
    print(private_events)
    
    
    for event in private_events:
        event_data = {
            "event_id": event.event_id,  
            "summary": event.summary,  
            "start_datetime": event.start_datetime.strftime("%Y-%m-%d"),  
            "location": event.location,
            "popularity": 1  
        }
        
        
        if not any(existing_event["event_id"] == event.event_id for existing_event in events_data["private"]):
            events_data["private"].append(event_data)

    
    hosted_events = db.session.query(Public_Events).join(
        Users_Events_Map,
        Users_Events_Map.event_id == Public_Events.event_id
    ).filter(
        Users_Events_Map.event_type == 'Public', 
        session["user_id"] == Public_Events.user_id  
    ).all()
    print(hosted_events)

    
    for event in hosted_events:
        event_data = {
            "event_id": event.event_id,  
            "summary": event.summary,  
            "start_datetime": event.start_datetime.strftime("%Y-%m-%d"),  
            "location": event.location,
            "popularity": event.popularity  
        }
        
        
        if not any(existing_event["event_id"] == event.event_id for existing_event in events_data["hosted"]):
            events_data["hosted"].append(event_data)

    
    registered_events = db.session.query(Public_Events).join(
        Users_Events_Map,
        Users_Events_Map.event_id == Public_Events.event_id
    ).filter(
        Users_Events_Map.event_type == 'Public', 
        Users_Events_Map.user_id == session["user_id"],
        Users_Events_Map.user_id != Public_Events.user_id   
    ).all()

    
    for event in registered_events:
        event_data = {
            "event_id": event.event_id,  
            "summary": event.summary,  
            "start_datetime": event.start_datetime.strftime("%Y-%m-%d"),  
            "location": event.location,
            "popularity": event.popularity  
        }
        
        
        if not any(existing_event["event_id"] == event.event_id for existing_event in events_data["registered"]):
            events_data["registered"].append(event_data)

    
    session["populate"] = False

def add_user_to_users_Info():
    temp=Users_Info.query.filter_by(email_id=session["email"]).all()
    if not temp:
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
        print(response)
        session['profile'] = response
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

    return render_template('index.html', categories=category_list, session_profile = session['profile'])

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

@other_routes.route('/api/my-events/add_event/<string:event_id>/<string:event_type>', methods=['POST'])
def add_event(event_id,event_type):
    try:
        
        event = Public_Events.query.get(event_id)
        if not event:
            return jsonify({"success": False, "message": "Event not found."}), 404

        
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
        
        if valid == "yes":
            user_event =Users_Events_Map(
                user_id=session["user_id"],
                event_id=event_id,
                c_event_id=session["creation_response"]["id"],
                event_type=event_type
                )
            event.popularity = event.popularity + 1
            db.session.add(user_event)
            db.session.commit()
            populate_my_events()
        
            return jsonify({"success": True, "message": "Event successfully added to your list!"}), 200
        else :
            return jsonify({"success": False, "message": "Failed To add in Google Calendar"}), 200

    except Exception as e:
        db.session.rollback()  
        print(f"Error: {e}")
        return jsonify({"success": False, "message": "An error occurred. Please try again."}), 500
    

def get_categories():
    categories = db.session.query(Public_Events.category).distinct().all()
    category_list = [category[0] for category in categories]

    return category_list

def refresh_and_delete_user_event(refresh_token,c_event_id):
    try:
        with current_app.app_context():
            oauth2_session = OAuth2Session(client_id=current_app.config['GOOGLE_OAUTH_CLIENT_ID'],
                                        token={'refresh_token': refresh_token})
            token = oauth2_session.refresh_token(
                'https://accounts.google.com/o/oauth2/token',
                client_id=current_app.config['GOOGLE_OAUTH_CLIENT_ID'],
                client_secret=current_app.config['GOOGLE_OAUTH_CLIENT_SECRET']
            )
        new_access_token = token['access_token']

        credentials = Credentials(
            token=new_access_token,
            refresh_token=token['refresh_token'],
            token_uri='https://oauth2.googleapis.com/token',
            client_id=current_app.config['GOOGLE_OAUTH_CLIENT_ID'],
            client_secret=current_app.config['GOOGLE_OAUTH_CLIENT_SECRET'],
            scopes=['https://www.googleapis.com/auth/calendar']
        )
        service = build('calendar', 'v3', credentials=credentials)
        
        service.events().delete(calendarId='primary', eventId=c_event_id).execute()

        print(f"Event {c_event_id} successfully deleted.")
        return "True"

    except Exception as e:
        print(f"Error deleting event: {e}")
        return "False"

def refresh_and_update_user_event(refresh_token, c_event_id, updated_event_data):
    try:
        with current_app.app_context():
            oauth2_session = OAuth2Session(
                client_id=current_app.config['GOOGLE_OAUTH_CLIENT_ID'],
                token={'refresh_token': refresh_token}
            )
            token = oauth2_session.refresh_token(
                'https://accounts.google.com/o/oauth2/token',
                client_id=current_app.config['GOOGLE_OAUTH_CLIENT_ID'],
                client_secret=current_app.config['GOOGLE_OAUTH_CLIENT_SECRET']
            )
        new_access_token = token['access_token']

        credentials = Credentials(
            token=new_access_token,
            refresh_token=token['refresh_token'],
            token_uri='https://oauth2.googleapis.com/token',
            client_id=current_app.config['GOOGLE_OAUTH_CLIENT_ID'],
            client_secret=current_app.config['GOOGLE_OAUTH_CLIENT_SECRET'],
            scopes=['https://www.googleapis.com/auth/calendar']
        )
        service = build('calendar', 'v3', credentials=credentials)

        updated_event = service.events().update(
            calendarId='primary',
            eventId=c_event_id,
            body=updated_event_data
        ).execute()

        print(f"Event {c_event_id} successfully updated: {updated_event}")
        return "True"

    except Exception as e:
        print(f"Error updating event: {e}")
        return "False"
    

@other_routes.route("/create_event", methods=["POST", "GET"])
def create_event():
    if request.method == "POST":
        data = request.form
        start_time=parser.parse(data.get("start_datetime"))
        end_time=parser.parse(data.get("end_datetime"))
        new_event=Events(
            summary=data.get("name"),
            location=data.get("venue"),
            description=data.get("description"),
            start_time=start_time,
            end_time=end_time
            )
        try:

            if data.get("type") == "Public":
                new_event_public = Public_Events(
                    user_id=session["user_id"],
                    summary=data.get("name"),
                    location=data.get("venue"),
                    description=data.get("description"),
                    start_time=start_time,
                    end_time=end_time,
                    popularity=int(data.get("popularity", 1)),
                    category=data.get("category")
                )
                valid=new_event.add_to_google_calendar()

                if valid =="yes":
                    db.session.add(new_event_public)
                    db.session.commit()
                    new_map=Users_Events_Map(
                    user_id=session["user_id"],
                    event_id=new_event_public.event_id,
                    c_event_id=session["creation_response"]["id"],
                    event_type=data.get("type")
                    )
                    db.session.add(new_map)
                    db.session.commit()
                    session["populate"]=True
                    return f"""
                            <script type="text/javascript">
                                alert("Event successfully added to your list!");
                                window.location.href = "{url_for('other_routes.gauthorized')}";
                            </script>
                            """
                else :
                    return f"""
                            <script type="text/javascript">
                                alert("Failed to add to Google Calendar");
                                window.location.href = "{url_for('other_routes.gauthorized')}";
                            </script>
                            """
            else:
                new_event_private = Private_Events(
                    user_id=session["user_id"],
                    summary=data.get("name"),
                    location=data.get("venue"),
                    description=data.get("description"),
                    start_time=start_time,
                    end_time=end_time,
                    category=data.get("category")
                )
                valid=new_event.add_to_google_calendar()
                if valid =="yes":
                    db.session.add(new_event_private)
                    db.session.commit()
                    new_map=Users_Events_Map(
                    user_id=session["user_id"],
                    event_id=new_event_private.event_id,
                    c_event_id=session["creation_response"]["id"],
                    event_type=data.get("type")
                    )
                    db.session.add(new_map)
                    db.session.commit()
                    session["populate"]=True
                    with current_app.test_client() as client:
                        response = client.post('/populate')
                    print("Status Code:", response.status_code)
                    return f"""
                            <script type="text/javascript">
                                alert("Event successfully added to your list!");
                                window.location.href = "{url_for('other_routes.gauthorized')}";
                            </script>
                            """
                else :
                    return f"""
                            <script type="text/javascript">
                                alert("Failed to add to Google Calendar");
                                window.location.href = "{url_for('other_routes.gauthorized')}";
                            </script>
                            """
        except Exception as e:
            return jsonify({"message": str(e)}), 500
    return render_template("manager_event_form.html", categories= get_categories())


@other_routes.route("/api/my-events/update_event/<string:event_id>/<string:event_type>", methods=["POST", "GET"])
def update_event(event_id, event_type):
    if event_type == "Private":
        event = Private_Events.query.get(event_id)
    if event_type == "Public":
        event = Public_Events.query.get(event_id)
    if not event:
        return jsonify({"message": "Event not found"}), 404

    if request.method == "POST":
        data = request.form
        try:
            event.user_id = data.get("user_id",event.user_id)
            event.event_id = data.get("event_id",event.event_id)
            event.summary = data.get("name", event.summary)
            event.start_datetime = parser.parse(data.get("start_datetime"))
            event.end_datetime = parser.parse(data.get("end_datetime"))
            event.description = data.get("description", event.description)
            event.location = data.get("venue", event.location)
            event.category = data.get("category", event.category)
            original_type = data.get("original_type","")
            type = data.get("type")
            print(event.start_datetime , event.end_datetime)
            if event.start_datetime >= event.end_datetime:
                return jsonify({"message": "Start time must be before end time"}), 400
            if type == original_type:
                print("Same")
                event_update(event,type)
            else:
                event_update(event, type, original_type)
            session["populate"]=True
            db.session.commit()
        except Exception as e:
            return jsonify({"message": str(e)}), 500

        return redirect(url_for("other_routes.gauthorized"))

    event = {
        'user_id' : event.user_id,
        'event_id' : event.event_id,
        'summary': event.summary,
        'start_datetime': event.start_datetime,
        'end_datetime': event.end_datetime,
        'location': event.location,
        'description': event.description,
        'category' : event.category
        }
    
    return render_template("manager_event_form.html", event=event, type=event_type, categories=get_categories())

def event_update(event, event_type, original_type=None):
    print("InSDioadnfion")
    print(event_type)
    if event_type == "Private" and original_type is None:
        delete_event(event.event_id, "Private")
        new_event_private = Private_Events(
            user_id=session["user_id"],
            summary=event.summary,
            location=event.location,
            description=event.description,
            start_time=event.start_datetime,
            end_time=event.end_datetime,
            category=event.category
        )
        new_event=Events(
            summary=event.summary,
            location=event.location,
            description=event.description,
            start_time=event.start_datetime,
            end_time=event.end_datetime
            )
        valid=new_event.add_to_google_calendar()
        if valid =="yes":
            db.session.add(new_event_private)
            db.session.commit()
            new_map=Users_Events_Map(
            user_id=session["user_id"],
            event_id=new_event_private.event_id,
            c_event_id=session["creation_response"]["id"],
            event_type="Private"
            )
            db.session.add(new_map)
            db.session.commit()
            session["populate"]=True
            with current_app.test_client() as client:
                response = client.post('/populate')
            print("Status Code:", response.status_code)
            return f"""
                    <script type="text/javascript">
                        alert("Event successfully added to your list!");
                        window.location.href = "{url_for('other_routes.gauthorized')}";
                    </script>
                    """
        else :
            return f"""
                    <script type="text/javascript">
                        alert("Failed to add to Google Calendar");
                        window.location.href = "{url_for('other_routes.gauthorized')}";
                    </script>
                    """
    if event_type == "Public" and original_type is None:
        event_id = event.event_id
        updated_event = Events(
            summary=event.summary,
            location=event.location,
            end_time=event.end_datetime,
            start_time=event.start_datetime,
            description=event.description,
            attendees=event.attendees
        )
        print(updated_event)
        updated_event = updated_event.to_google_event()
        events = Users_Events_Map.query.filter_by(event_id=event_id).all()
        for ori_event in events:
            user_id = ori_event.user_id
            c_event_id = ori_event.c_event_id
            user_info=Users_Info.query.filter(Users_Info.user_id==user_id).first()
            refresh_token = user_info.refresh_token
            refresh_and_update_user_event(refresh_token,c_event_id, updated_event)
    if original_type is not None:
        event_id = event.event_id
        if event_type == "Public" and original_type == "Private":
            pub_event = Public_Events.query.get(event_id)
            if pub_event:
                return jsonify({"success": False, "message": "Event already in Public."}), 404
            user_event = Users_Events_Map.query.filter_by(event_id=event_id).first()
            if user_event:
                user_event.event_type = event_type
                
                db.session.commit()
            print("Use map created")
            pub_event = Public_Events(
                event_id=event.event_id,
                summary=event.summary,
                location=event.location,
                user_id=event.user_id,
                description=event.description,
                start_time=event.start_datetime,
                end_time=event.end_datetime,
                popularity=1,
                category=event.category
            )
            pri_event = Private_Events.query.get(event_id)
            db.session.add(pub_event)
            db.session.add(user_event)
            db.session.delete(pri_event)
            db.session.commit()
        elif event_type == "Private" and original_type == "Public":
            ori_event = event
            print("pub to private")
            delete_event(event_id=ori_event.event_id, event_type="Public")
            print(ori_event)
            pri_event = Private_Events(
                summary=event.summary,
                location=event.location,
                user_id=event.user_id,
                description=event.description,
                start_time=event.start_datetime,
                end_time=event.end_datetime,
                category=event.category
            )
            goog_event = Events(
                summary=pri_event.summary,
                location=pri_event.location,
                description=pri_event.description,
                start_time=pri_event.start_datetime,
                end_time=pri_event.end_datetime,
                attendees=pri_event.attendees,
            )
            goog_event.add_to_google_calendar()
            print("Private event created")
            user_event = Users_Events_Map(
                user_id=session["user_id"],
                event_id=pri_event.event_id,
                c_event_id=session["creation_response"]["id"],
                event_type=event_type      
            )
            print("User map created")
            db.session.add(pri_event)
            print("pri added")
            db.session.add(user_event)
            print("user added")
            db.session.commit()


 

@other_routes.route("/api/my-events/remove_event/<string:event_id>/<string:event_type>", methods=["GET"])
def delete_event(event_id,event_type):
    p_event=Public_Events.query.get(event_id)
    if event_type == "Private" or p_event.user_id != session["user_id"]:
        event=Users_Events_Map.query.filter(Users_Events_Map.user_id ==session["user_id"],Users_Events_Map.event_id==event_id).first()
        url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event.c_event_id}"
        response=google.delete(url)
        if response.status_code == 204:
            if event_type == "Private":
                event=Private_Events.query.get(event_id)
                if not event:
                    return jsonify({"message": "Event not found in Private Table"}), 404
                db.session.delete(event)
                db.session.commit()

            event=Users_Events_Map.query.filter(Users_Events_Map.user_id==session["user_id"],Users_Events_Map.event_id==event_id).first()
            if not event:
                return jsonify({"message": "Event not found in User map Table "}), 404
            if p_event:
                p_event.popularity -= 1
            db.session.delete(event)
            db.session.commit()
            session["populate"]=True
            populate_my_events()
            return jsonify({"message": "Event deleted successfully"}), 200

        else:
            return jsonify({"error": f"Failed to delete event: {response.json()}", "status": response.status_code}), response.status_code
    
    else :
        user_with_event_id=Users_Events_Map.query.filter(Users_Events_Map.event_id==event_id).all()
        user_c_event_id_rtoken=[]

        for users in user_with_event_id:
            user_info=Users_Info.query.filter(Users_Info.user_id==users.user_id).first()
            if user_info:
                user_c_event_id_rtoken.append({
                    "user_id":user_info.user_id,
                    "event_id":users.event_id,
                    "c_event_id":users.c_event_id,
                    "refresh_token":user_info.refresh_token
                })
        flag = True
        for final_delete in user_c_event_id_rtoken:
            if refresh_and_delete_user_event(final_delete['refresh_token'],final_delete['c_event_id']) == "True":
                if flag:
                    event=Public_Events.query.filter(Public_Events.user_id==final_delete['user_id'],Public_Events.event_id==final_delete['event_id']).first()
                    if not event:
                        return jsonify({"message": "Event not found in Public Table"}), 404
                    db.session.delete(event)
                    db.session.commit()
                    flag = False
                event=Users_Events_Map.query.filter(Users_Events_Map.event_id==final_delete['event_id']).first()
                if not event:
                    return jsonify({"message": "Event not found in User map Table "}), 404
                db.session.delete(event)
                db.session.commit()
                session["populate"]=True
                populate_my_events()
            else :
                return jsonify({"message": "All the users entries not deleted"}), 404
            
        return jsonify({"message": "All the Event deleted successfully"}), 200

