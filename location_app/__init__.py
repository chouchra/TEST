from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    # Importer les modèles
    from location_app import models

    # Enregistrer les routes
    from location_app.routes import main_bp
    app.register_blueprint(main_bp)

    return app
