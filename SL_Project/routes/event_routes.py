from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from config import db
from datetime import datetime
from models import Event

event_routes = Blueprint('event_routes', __name__)

def get_categories():
    categories = db.session.query(Event.category).distinct().all()
    category_list = [category[0] for category in categories]

    return category_list

@event_routes.route("/create_event", methods=["POST", "GET"])
def create_event():
    if request.method == "POST":
        data = request.form
        required_fields = ['name', 'organizer', 'date', 'start_time', 'description', 'category', 'venue']
        
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({"message": f"Missing required fields: {', '.join(missing_fields)}"}), 400
        
        try:
            new_event = Event(
                name=data.get("name"),
                organizer=data.get("organizer"),
                date=datetime.strptime(data.get("date"), '%Y-%m-%d').date(),
                start_time=datetime.strptime(data.get("start_time"), '%H:%M').time(),
                end_time=datetime.strptime(data.get("end_time"), '%H:%M').time(),
                description=data.get("description"),
                venue=data.get("venue"),
                links=data.get("links"),
                contact_details=data.get("contact_details"),
                popularity=int(data.get("popularity", 0)),
                participants=int(data.get("participants", 0)),
                category=data.get("category")
            )

            if new_event.start_time >= new_event.end_time:
                return jsonify({"message": "Start time must be before end time"}), 400

            db.session.add(new_event)
            db.session.commit()
        except Exception as e:
            return jsonify({"message": str(e)}), 500

        return redirect(url_for("other_routes.index"))

    return render_template("manager_event_form.html", categories= get_categories())

@event_routes.route("/update_event/<int:event_id>", methods=["GET", "POST"])
def update_event(event_id):
    event = Event.query.get(event_id)
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

            db.session.commit()
        except Exception as e:
            return jsonify({"message": str(e)}), 500

        return redirect(url_for("other_routes.index"))

    return render_template("manager_event_form.html", event=event, categories= get_categories())

@event_routes.route("/delete_event/<int:event_id>", methods=["GET"])
def delete_event(event_id):
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"message": "Event not found"}), 404

    db.session.delete(event)
    db.session.commit()
    return redirect(url_for("other_routes.index"))