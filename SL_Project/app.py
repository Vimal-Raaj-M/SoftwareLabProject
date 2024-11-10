from config import app, db
from routes.event_routes import event_routes
from routes.other_routes import other_routes

app.register_blueprint(event_routes)
app.register_blueprint(other_routes)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)