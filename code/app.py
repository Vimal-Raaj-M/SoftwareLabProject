from flask import render_template, redirect, url_for,session
from config import app,db, scheduler
from models import Users_Info,Users_Events_Map,Private_Events,Public_Events
from routes.other_routes import other_routes
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_dance.contrib.google import make_google_blueprint
import os

admin = Admin(app, name='Event Management Database', template_mode='bootstrap3')

class MapView(ModelView):
    
    column_list = ('user_id', 'event_id','c_event_id','event_type')

class StudentsView(ModelView):
    
    column_list = ('user_id', 'email_id', 'refresh_token')

class PublicView(ModelView):
    
    column_list = ('user_id','event_id','summary','location','description','category','start_datetime','end_datetime','timezone','attendees','use_default_reminders','reminder_minutes','popularity')

class PrivateView(ModelView):
    
    column_list = ('user_id','event_id','summary','location','description','start_datetime','end_datetime','timezone','attendees','use_default_reminders','reminder_minutes','category')


admin.add_view(MapView(Users_Events_Map, db.session))


admin.add_view(StudentsView(Users_Info, db.session))


admin.add_view(PublicView(Private_Events, db.session))


admin.add_view(PrivateView(Public_Events, db.session))


app.secret_key=#INSERT HERE

google_blueprint = make_google_blueprint(
    
    client_id=#INSERT HERE,
    
    client_secret=#INSERT HERE,
    
    scope=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/calendar.events"
    ],
    
    offline=True,
    
    redirect_to='other_routes.gauthorized'
    )

app.register_blueprint(google_blueprint)
app.register_blueprint(other_routes)

@app.route("/")
def login():
    session["populate"]=True
    return redirect(url_for('google.login'))



@app.route("/logout")
def logout():
    print("hello logout")
    session.clear() 
    return redirect(url_for('login'))  

if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        scheduler.start()
    with app.app_context():
        db.create_all()
    app.run(debug=True,ssl_context=('certificates/cert.crt','certificates/cert.key'), host = "0.0.0.0", port=5000)
