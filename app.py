import os
import uuid

from flask import Flask, jsonify
from flask_smorest import Api
from flask_jwt_extended import JWTManager, create_access_token
from flask_migrate import Migrate
from db import db
import models

from resources.item import blp as ItemBlueprint
from resources.store import blp as StoreBlueprint
from resources.tags import blp as TagBlueprint
from resources.user import blp as UserBlueprint

from blocklist import BLOCKLIST

def create_app(db_url: str = None):
    app = Flask(__name__)
    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.config["API_TITLE"] = "Stores REST API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url or os.getenv("DATABASE_URL", "sqlite:///./data.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    migrate = Migrate(app, db)
    api = Api(app)
    api.register_blueprint(ItemBlueprint)
    api.register_blueprint(StoreBlueprint)
    api.register_blueprint(TagBlueprint)
    api.register_blueprint(UserBlueprint)

    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", '3649d062-1604-44e5-ab69-3b467a0aef68')
    jwt = JWTManager(app)

    @jwt.token_in_blocklist_loader
    def check_if_token_in_blocklist(jwt_header, jwt_payload):
        jti = jwt_payload["jti"]
        return jti in BLOCKLIST
    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        return jsonify({'message': 'Fresh token required.', "error": "fresh_token_required"}), 401
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return jsonify({'message': 'Token revoked.', "error": "invalid_revoked"}), 401
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'message': 'Token expired. Please log in again.', "error": "invalid_token"}), 401
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'message': 'Signature verification failed.', "error": "invalid_token"}), 401
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'message': 'Request does not contain an access token.', "error": "authorization_required"}), 401
    # with app.app_context():
    #     db.create_all()

    return app

if __name__ == "__main__":
    create_app().run(port=5000, debug=True)



