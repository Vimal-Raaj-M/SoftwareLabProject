from flask import render_template, redirect, url_for,session
from config import app,db
from models import Users_Info,Users_Events_Map,Private_Events,Public_Events
from routes.event_routes import event_routes
from routes.other_routes import other_routes
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_dance.contrib.google import make_google_blueprint

admin = Admin(app, name='Event Management Database', template_mode='bootstrap3')

class MapView(ModelView):
    #it will list the columns view in the flask_admin database custmomize
    column_list = ('user_id', 'event_id','c_event_id','event_type')

class StudentsView(ModelView):
    #it will list the columns view in the flask_admin database custmomize
    column_list = ('user_id', 'email_id', 'refresh_token')

class PublicView(ModelView):
    #it will list the columns view in the flask_admin database custmomize
    column_list = ('user_id','event_id','summary','location','description','start_datetime','end_datetime','timezone','attendees','use_default_reminders','reminder_minutes','category','popularity')

class PrivateView(ModelView):
    #it will list the columns view in the flask_admin database custmomize
    column_list = ('user_id','event_id','summary','location','description','start_datetime','end_datetime','timezone','attendees','use_default_reminders','reminder_minutes','category')

#normal view it will give what ever in the database 
admin.add_view(MapView(Users_Events_Map, db.session))

#normal view it will give what ever in the database 
admin.add_view(StudentsView(Users_Info, db.session))

#normal view it will give what ever in the database 
admin.add_view(PublicView(Private_Events, db.session))

#normal view it will give what ever in the database 
admin.add_view(PrivateView(Public_Events, db.session))

##reference documentation https://flask-dance.readthedocs.io/en/latest/providers.html#module-flask_dance.contrib.google
app.secret_key='e37ac0f19b0a62b05f01f8d42b3c4a7296bfe1c65b467'

google_blueprint = make_google_blueprint(
    #This id is taken givrn by google cloud for our application
    client_id='',
    #This key combined with client_id to identify our project in google
    client_secret='',
    #this tells us what are the scope(info) we will get (VRM)
    scope=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/calendar.events"
    ],
    #This is set to true so we can get refesh token(offline access)
    offline=True,
    #This is where after the authentication done the page will be redirected to
    redirect_to='other_routes.gauthorized'
    )

app.register_blueprint(google_blueprint)
app.register_blueprint(event_routes)
app.register_blueprint(other_routes)

@app.route("/")
def login():
    session["populate"]=True
    return redirect(url_for('google.login'))

@app.route("/create")
def manual():
        
        new_student=Users_Info(
            email_id='vimalraaj32@gmail.com',
            refresh_token='1//0g7jOdsDQDpqbCgYIARAAGBASNwF-L9IrMMfXO0lORPzMYsUEKuBc_wCs4w7LygJGO6kSiEVmIyCeBDPUmAZFw9RNSGgpJG19vj8'
        )
        db.session.add(new_student)
        db.session.commit()

@app.route("/logout")
def logout():
    session.clear() 
    return redirect(url_for('login'))  

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True,ssl_context=('certificates/cert.crt','certificates/cert.key'))
