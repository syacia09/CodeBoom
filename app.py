from flask import Flask
from config import Config
from extensions import db

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Register blueprints
to_register = [
    ('controllers.auth_controller', 'auth_bp'),
    ('controllers.main_controller', 'main_bp'),
    ('controllers.submission_controller', 'sub_bp')
]
for module_path, bp_name in to_register:
    module = __import__(module_path, fromlist=[bp_name])
    blueprint = getattr(module, bp_name)
    app.register_blueprint(blueprint)

# inject current_user into templates
def get_current_user():
    from flask import session
    from models.user_model import User
    uid = session.get('user_id')
    return User.get_by_id(uid) if uid else None

@app.context_processor
def inject_user():
    return dict(current_user=get_current_user())

if __name__ == '__main__':
    app.run(debug=True)