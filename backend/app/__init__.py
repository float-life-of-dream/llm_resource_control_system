from __future__ import annotations

from flask import Flask
from flask_cors import CORS

from app.api.health import blp as health_blp
from app.api.monitor import blp as monitor_blp
from app.config import Config
from app.extensions.docs import api


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, resources={r"/api/*": {"origins": "*"}})
    api.init_app(app)
    api.register_blueprint(health_blp)
    api.register_blueprint(monitor_blp)

    return app

