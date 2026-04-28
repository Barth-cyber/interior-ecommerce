from flask import jsonify


def register_health(app):
    @app.route("/api/health", endpoint="api_health")
    def api_health():
        return jsonify({"status": "ok", "message": "Duct AI backend live"}), 200
