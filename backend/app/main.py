"""Flask app factory. `app/__init__.py` stays empty per convention, so this
is the module `flask --app app.main:create_app run` targets."""

from __future__ import annotations

from flask import Flask

from app.routes.settlement import settlement_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(settlement_bp)
    return app


def main() -> None:
    create_app().run(debug=True)


if __name__ == "__main__":
    main()
