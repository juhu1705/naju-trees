import functools

from flask import Blueprint, url_for, redirect, flash, g, render_template, request
from werkzeug.security import generate_password_hash

from naju import util
from naju.database import get_db
from naju.util import random_uri_safe_string

bp = Blueprint('auth', __name__)


def get_admin_key():
    return 1


def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not g.user or g.user['level'] < get_admin_key():
            flash('Du benötigst Administratorberechtigungen!')
            return redirect(url_for('auth.login'))
        return view(**kwargs)

    return wrapped_view


@admin_required
@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        try:
            username = request.form['username']
            mail = request.form['mail']
            agreement = request.form['agreement']
        except:
            flash('Post incorrect!')
            flash('Unter umständen wurde der Datenschutzvereinbarung nicht zugestimmt! Diese Zustimmung ist erforderlich!')
            return redirect(url_for('naju.index'))
        db = get_db()
        error = None
        user = db.execute('SELECT * FROM user WHERE name = ? or email = ?', (username, mail,)).fetchone()

        if not agreement:
            error = 'Es wurde der Datenschutzvereinbarung nicht zugestimmt!'
        elif user is not None:
            error = 'Der Benutzername oder die E-Mailaddresse sind bereits in Benutzung.'
        elif not username:
            error = 'Sie haben keinen Benutzernamen angegeben.'
        elif not mail or not util.check_email(mail):
            error = 'Sie haben keine E-Mail Addresse angegeben.'

        if error is None:
            token = random_uri_safe_string(64)
            db.execute('INSERT INTO user (name, email, pwd_hash, level, email_confirmed, confirmation_token, visible)'
                       ' VALUES (?, ?, ?, ?, ?, ?, ?)',
                       (username, mail, '', 0, 0, token, 0))
            db.commit()
            user = db.execute('SELECT * FROM user WHERE name = ? AND email = ?', (username, mail,)).fetchone()
            from naju.emails import send_confirmation_email

            send_confirmation_email(user['email'], user, token)

            return redirect(url_for('naju.home'))
        flash(error)

    return render_template('admin/register.html')


@bp.route('/reset_password/<token>', methods=('GET', 'POST'))
def reset_password(token):
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        check = request.form['check']

        if password == '' or str(password).isspace():
            flash('Es muss ein Password angegeben sein!')
            return render_template('naju/reset_password.html')

        if check != password:
            flash('Die Passwörter müssen übereinstimmen!')
            return render_template('naju/reset_password.html')

        db = get_db()

        user = db.execute('SELECT * FROM user WHERE confirmation_token=? AND name=?', (token, username)).fetchone()

        if user is not None:
            db.execute('UPDATE user SET pwd_hash=? WHERE id=?', (generate_password_hash(password), user['id']))
            db.commit()

        return redirect('naju.index')
    return render_template('naju/reset_password.html')
