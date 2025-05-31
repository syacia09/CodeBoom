from app import app
from extensions import db
from models.user_model import User
from models.problem_model import Problem
from models.submission_model import Submission
import json, os
from config import Config

with app.app_context():
    db.create_all()

    # If 'problems' table is empty, preload from JSON
    if Problem.query.count() == 0:
        path = os.path.join(Config.BASE_DIR, 'data', 'problems.json')
        try:
            with open(path, 'r', encoding='utf-8') as f:
                probs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading problems.json: {e}")
            probs = []

        for item in probs:
            p = Problem(
                id=item['id'],
                title=item['title'],
                statement=item['statement'],
                input_format=item['input_format'],
                output_format=item['output_format'],
                samples=item.get('samples', [])
            )
            db.session.add(p)
        db.session.commit()
        print("Database initialized with problems.")
    else:
        print("Problems already loaded.")
