import os
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, jsonify, Response, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

IS_PROD         = os.getenv('FLASK_ENV') == 'production'
ALLOWED_ORIGINS = [o.strip() for o in os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',')]

LOG_LEVEL = logging.INFO if IS_PROD else logging.DEBUG
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logger = logging.getLogger('app')

if IS_PROD:
    os.makedirs('logs', exist_ok=True)
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=5 * 1024 * 1024, backupCount=5)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s'))
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

app = Flask(__name__)
app.config['SECRET_KEY']                     = os.getenv('SECRET_KEY', 'dev-secret-change-me')
app.config['SQLALCHEMY_DATABASE_URI']        = os.getenv('DATABASE_URL', 'sqlite:///worker_hours.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SAMESITE']        = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY']        = True
app.config['SESSION_COOKIE_SECURE']          = IS_PROD

CORS(app, supports_credentials=True, origins=ALLOWED_ORIGINS)

from extensions import db, migrate, limiter
db.init_app(app)
migrate.init_app(app, db)
limiter.init_app(app)

from routes.auth     import bp as auth_bp
from routes.users    import bp as users_bp
from routes.projects import bp as projects_bp
from routes.tasks    import bp as tasks_bp
from routes.invites  import bp as invites_bp
from routes.hours    import bp as hours_bp
from routes.leave    import bp as leave_bp
from openapi_spec    import OPENAPI_SPEC
from seed            import seed_database

app.register_blueprint(auth_bp)
app.register_blueprint(users_bp)
app.register_blueprint(projects_bp)
app.register_blueprint(tasks_bp)
app.register_blueprint(invites_bp)
app.register_blueprint(hours_bp)
app.register_blueprint(leave_bp)


@app.route('/api/openapi.json', methods=['GET'])
def openapi_json():
    return jsonify(OPENAPI_SPEC), 200


@app.route('/api/docs', methods=['GET'])
def swagger_ui():
    html = """<!DOCTYPE html>
<html lang="lt">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>WorkerH REST API — OpenAPI Dokumentacija</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.17.14/swagger-ui.css" />
  <style>
    body { margin: 0; background: #fafafa; }
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5.17.14/swagger-ui-bundle.js"></script>
  <script>
    window.onload = () => {
      window.ui = SwaggerUIBundle({
        url: '/api/openapi.json',
        dom_id: '#swagger-ui',
        deepLinking: true,
        persistAuthorization: true,
      });
    };
  </script>
</body>
</html>"""
    return Response(html, mimetype='text/html')


FRONTEND_DIST = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'dist'))


@app.errorhandler(400)
def bad_request(_e):
    return jsonify({'error': 'Netinkamai suformuota užklausa (400 Bad Request)'}), 400


@app.errorhandler(404)
def not_found(_e):
    if not request.path.startswith('/api') and os.path.isdir(FRONTEND_DIST):
        rel_path = request.path.lstrip('/')
        full_path = os.path.join(FRONTEND_DIST, rel_path)
        if rel_path and os.path.isfile(full_path):
            return send_from_directory(FRONTEND_DIST, rel_path)
        index_path = os.path.join(FRONTEND_DIST, 'index.html')
        if os.path.isfile(index_path):
            return send_from_directory(FRONTEND_DIST, 'index.html')
    return jsonify({'error': 'Resurso nerasta'}), 404


@app.errorhandler(405)
def method_not_allowed(_e):
    return jsonify({'error': 'Metodas neleidžiamas'}), 405


@app.errorhandler(422)
def unprocessable_entity(_e):
    return jsonify({'error': 'Nepavyko apdoroti duomenų (422 Unprocessable Entity)'}), 422


@app.errorhandler(429)
def rate_limited(_e):
    return jsonify({'error': 'Per daug užklausų. Bandykite vėliau.'}), 429


@app.errorhandler(500)
def server_error(_e):
    logger.error('Unhandled exception', exc_info=True)
    return jsonify({'error': 'Vidinė serverio klaida. Bandykite vėliau.'}), 500


with app.app_context():
    seed_database(reset=False)

if __name__ == '__main__':
    app.run(debug=not IS_PROD)
