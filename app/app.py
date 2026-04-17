import logging
from flask import Flask, jsonify
from extensions import db, jwt, limiter
from config import get_config


def create_app(config_class=None):
    app = Flask(__name__)

    # ── Config ────────────────────────────────────────────────────────────────
    app.config.from_object(config_class or get_config())

    # ── Logging ───────────────────────────────────────────────────────────────
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    # ── Extensions ────────────────────────────────────────────────────────────
    db.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)

    # ── Blueprints ────────────────────────────────────────────────────────────
    from routes import api
    app.register_blueprint(api, url_prefix="/api/v1")

    # ── DB Init ───────────────────────────────────────────────────────────────
    with app.app_context():
        db.create_all()

    # ── Global error handlers ─────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Route not found."}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method not allowed."}), 405

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return jsonify({"error": "Too many requests. Please slow down."}), 429

    @app.errorhandler(500)
    def server_error(e):
        app.logger.error(f"Internal error: {e}")
        return jsonify({"error": "Internal server error."}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=False)
