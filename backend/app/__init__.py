from __future__ import annotations

from flask import Flask
from flask_cors import CORS

from app.api.auth import blp as auth_blp
from app.api.analysis import blp as analysis_blp
from app.api.chat import blp as chat_blp
from app.api.health import blp as health_blp
from app.api.logs import blp as logs_blp
from app.api.model_monitor import blp as model_monitor_blp
from app.api.monitor import blp as monitor_blp
from app.api.prometheus import blp as prometheus_blp
from app.api.system import blp as system_blp
from app.api.tenant import blp as tenant_blp
from app.config import Config
from app.extensions.db import db, migrate
from app.extensions.docs import api
from app.extensions.metrics import instrument_app
from app.services.auth_service import bootstrap_security


def create_app(test_config: dict | None = None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    CORS(app, resources={r"/api/*": {"origins": app.config["FRONTEND_ORIGINS"]}})
    instrument_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    api.init_app(app)
    api.register_blueprint(health_blp)
    api.register_blueprint(auth_blp)
    api.register_blueprint(system_blp)
    api.register_blueprint(tenant_blp)
    api.register_blueprint(monitor_blp)
    api.register_blueprint(model_monitor_blp)
    api.register_blueprint(prometheus_blp)
    api.register_blueprint(logs_blp)
    api.register_blueprint(analysis_blp)
    api.register_blueprint(chat_blp)

    with app.app_context():
        bootstrap_security()

    return app
