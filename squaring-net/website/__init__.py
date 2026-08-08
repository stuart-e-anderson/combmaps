from flask import Flask


def create_app(config=None):
    app = Flask(__name__)

    if config:
        app.config.from_mapping(config)

    from .routes import main
    app.register_blueprint(main)

    return app
