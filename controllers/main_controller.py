from flask import Blueprint, render_template, session, redirect, url_for
from functools import wraps
from models.problem_model import Problem

main_bp = Blueprint('main', __name__)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@main_bp.route('/')
@login_required
def index():
    problems = Problem.query.all()
    return render_template('index.html', problems=problems)

@main_bp.route('/problem/<pid>')
@login_required
def problem(pid):
    prob = Problem.query.get_or_404(pid)
    return render_template('problem.html', prob=prob)