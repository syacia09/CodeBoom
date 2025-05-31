from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from extensions import db
from models.user_model import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not username or not password:
            flash('Username dan password wajib diisi.', 'error')
        elif User.get_by_username(username):
            flash('Username sudah ada.', 'error')
        else:
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Register sukses, silakan login', 'info')
            return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.get_by_username(username)
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('Login sukses', 'info')
            return redirect(url_for('main.index'))
        flash('Login gagal', 'error')
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out', 'info')
    return redirect(url_for('auth.login'))