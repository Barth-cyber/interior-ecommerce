# Render / Gunicorn entrypoint
# DO NOT add routes or configs here

from app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)