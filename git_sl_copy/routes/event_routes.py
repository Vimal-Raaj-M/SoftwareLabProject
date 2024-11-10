from flask import Blueprint, render_template, jsonify, request, redirect, url_for,session
from config import db
from models import Users_Info,Users_Events_Map,Private_Events,Public_Events,event_schema,Events
from datetime import datetime, timezone
from dateutil import parser
event_routes = Blueprint('event_routes', __name__)

def get_categories():
    categories = db.session.query(Public_Events.category).distinct().all()
    category_list = [category[0] for category in categories]

    return category_list


@event_routes.route("/create_event", methods=["POST", "GET"])
def create_event():
    if request.method == "POST":
        data = request.form
        # start_time_obj = datetime.strptime(data.get("start_datetime"), '%Y-%m-%dT%H:%M')
        # start_time_utc = start_time_obj.replace(tzinfo=timezone.utc)
        # start_time_iso_utc = start_time_utc.isoformat()
        # end_time_obj = datetime.strptime(data.get("end_datetime"), '%Y-%m-%dT%H:%M')
        # end_time_utc = end_time_obj.replace(tzinfo=timezone.utc)
        # end_time_iso_utc = end_time_utc.isoformat()
        start_time=parser.parse(data.get("start_datetime"))
        end_time=parser.parse(data.get("end_datetime"))
        new_event=Events(
            # user_id=session["user_id"],
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
                    # session["event_id"]=new_event.event_id
                    new_map=Users_Events_Map(
                    user_id=session["user_id"],
                    event_id=new_event_public.event_id,
                    c_event_id=session["creation_response"]["id"],
                    event_type=data.get("type")
                    )
                    db.session.add(new_map)
                    db.session.commit()
                    session["populate"]=True
                    return render_template("popup_redirect.html", message="Event successfully added to your list!", redirect_url=url_for("other_routes.gauthorized"))     
                else :
                    return render_template("popup_redirect.html", message="Failed to add to Google Calendar", redirect_url=url_for("other_routes.gauthorized"))
            else:
                new_event_private = Private_Events(
                    user_id=session["user_id"],
                    summary=data.get("name"),
                    location=data.get("venue"),
                    description=data.get("description"),
                    start_time=start_time,
                    end_time=end_time,
                    # popularity=int(data.get("popularity", 1)),
                    category=data.get("category")
                )
                valid=new_event.add_to_google_calendar()
                if valid =="yes":
                    db.session.add(new_event_private)
                    db.session.commit()
                    # session["event_id"]=new_event.event_id
                    new_map=Users_Events_Map(
                    user_id=session["user_id"],
                    event_id=new_event_private.event_id,
                    c_event_id=session["creation_response"]["id"],
                    event_type=data.get("type")
                    )
                    db.session.add(new_map)
                    db.session.commit()
                    session["populate"]=True
                    return render_template("popup_redirect.html", message="Event successfully added to your list!", redirect_url=url_for("other_routes.gauthorized"))

                else:
                    return render_template("popup_redirect.html", message="Failed to add to Google Calendar", redirect_url=url_for("other_routes.gauthorized"))
        except Exception as e:
            return jsonify({"message": str(e)}), 500
    return render_template("manager_event_form.html", categories= get_categories())


@event_routes.route("/update_event/<int:event_id>", methods=["GET", "POST"])
def update_event(event_id):
    event = Public_Events.query.get(event_id)
    if not event:
        return jsonify({"message": "Event not found"}), 404

    if request.method == "POST":
        data = request.form
        try:
            event.name = data.get("name", event.name)
            event.organizer = data.get("organizer", event.organizer)
            event.date = datetime.strptime(data.get("date", event.date.strftime('%Y-%m-%d')), '%Y-%m-%d').date()
            event.start_time = datetime.strptime(data.get("start_time", event.start_time.strftime('%H:%M')), '%H:%M').time()
            event.end_time = datetime.strptime(data.get("end_time", event.end_time.strftime('%H:%M')), '%H:%M').time()
            event.description = data.get("description", event.description)
            event.venue = data.get("venue", event.venue)
            event.links = data.get("links", event.links)
            event.contact_details = data.get("contact_details", event.contact_details)
            event.popularity = int(data.get("popularity", event.popularity))
            event.participants = int(data.get("participants", event.participants))
            event.category = data.get("category", event.category)

            if event.start_time >= event.end_time:
                return jsonify({"message": "Start time must be before end time"}), 400
            session["populate"]=True
            db.session.commit()
        except Exception as e:
            return jsonify({"message": str(e)}), 500

        return redirect(url_for("other_routes.gauthorized"))

    return render_template("manager_event_form.html", event=event, categories= get_categories())


@event_routes.route("/delete_event/<int:event_id>", methods=["GET"])
def delete_event(event_id):
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"message": "Event not found"}), 404

    db.session.delete(event)
    db.session.commit()
    return redirect(url_for("other_routes.gauthorized"))