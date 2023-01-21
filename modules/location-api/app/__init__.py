import logging
from flask import Flask, jsonify
from flask_cors import CORS
from flask_restx import Api
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import HTTPException

db = SQLAlchemy()


def create_app(env=None):
    from app.config import config_by_name
    from app.routes import register_routes

    app = Flask(__name__)
    app.config.from_object(config_by_name[env or "test"])
    api = Api(app, title="UdaConnect Location API", version="0.1.0")

    CORS(app)  # Set CORS for development

    register_routes(api, app)
    db.init_app(app)

    @app.route("/health")
    def health():
        return jsonify("healthy")

    @app.errorhandler(Exception)
    def handle_exception(e):
        """Return JSON instead of HTML for HTTP errors."""

        logging.exception(e)
        status_code = e.code if isinstance(e, HTTPException) else 500
        response = jsonify(message=str(e),status_code = status_code)
        return response
    
    app.register_error_handler(Exception, handle_exception)

    return app
