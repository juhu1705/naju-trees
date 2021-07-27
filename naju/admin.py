import functools
from sqlite3 import ProgrammingError, DatabaseError

from flask import Blueprint, url_for, redirect, flash, g, render_template, request, current_app
from werkzeug.security import generate_password_hash

from naju import util
from naju.database import get_db
from naju.util import random_uri_safe_string

bp = Blueprint('admin', __name__)


def get_admin_key():
    return 1


def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not g.user or g.user['level'] < get_admin_key():
            flash('Du benötigst Administratorberechtigungen!')
            return redirect(url_for('naju.index'))
        return view(**kwargs)

    return wrapped_view


@bp.route('/register', methods=('GET', 'POST'))
@admin_required
def register():
    if request.method == 'POST':
        try:
            username = str(request.form['username']).lower()
            mail = str(request.form['mail']).lower()
            agreement = request.form['agreement']
        except:
            flash('Post incorrect!')
            flash('Unter umständen wurde der Datenschutzvereinbarung nicht zugestimmt! Diese Zustimmung ist '
                  'erforderlich!')
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
            db.execute('INSERT INTO user (name, email, pwd_hash, level, email_confirmed, confirmation_token)'
                       ' VALUES (?, ?, ?, ?, ?, ?)',
                       (username, mail, '', 0, 0, token))
            db.commit()
            user = db.execute('SELECT * FROM user WHERE name = ? AND email = ?', (username, mail,)).fetchone()
            from naju.emails import send_confirmation_email

            send_confirmation_email(user['email'], user, token)

            return redirect(url_for('naju.home'))
        flash(error)

    return render_template('naju/register.html')

@bp.route('/sql', methods=('GET', 'POST'))
@admin_required
def sql_access():
    """ SQL-Zugriffsseite """
    reload_response = redirect(url_for(".sql_access"), code=303)

    if request.method != "POST":
        return render_template("naju/sql_access.html", query="", result=None)

    # ELSE

    query = request.form["query"]

    if not query:
        flash("Bitte geben Sie eine SQL-Abfrage ein.", "error")
        return reload_response

    # Query ausführen
    db = get_db()
    try:
        result = db.execute(query)
    except DatabaseError as exc:
        flash(f"Die SQL-Abfrage konnte nicht ausgeführt werden.\n\nFehlerbeschreibung:\n{exc}", "error")
        return render_template("naju/sql_access.html", query=query, result=None)

    db.commit()

    flash("Die SQL-Abfrage wurde erfolgreich ausgeführt.", "success")

    return render_template("naju/sql_access.html", query=query, result=result)


@bp.route('/reset_password/<token>', methods=('GET', 'POST'))
def reset_password(token):
    if token is None or token == "" or token == 'None':
        return redirect('naju.index')
    if request.method == 'POST':
        try:
            username = str(request.form['username']).lower()
            password = request.form['password']
            check = request.form['passwordcheck']
            agreement = request.form['agreement']
        except:
            flash('Post incorrect!')
            flash('Unter umständen wurde der Datenschutzvereinbarung nicht zugestimmt! Diese Zustimmung ist '
                  'erforderlich!')
            return render_template('naju/activate_user.html')

        if not agreement:
            flash('Es wurde der Datenschutzvereinbarung nicht zugestimmt!')
            return render_template('naju/activate_user.html')

        if password == '' or str(password).isspace():
            flash('Es muss ein Password angegeben sein!')
            return render_template('naju/activate_user.html')

        if check != password:
            flash('Die Passwörter müssen übereinstimmen!')
            return render_template('naju/activate_user.html')

        db = get_db()

        user = db.execute('SELECT * FROM user WHERE confirmation_token=? AND name=?',
                          (token, username, )).fetchone()

        if user is not None:
            db.execute('UPDATE user SET pwd_hash=?, confirmation_token=?, email_confirmed=? WHERE id=?',
                       (generate_password_hash(password), None, 1, user['id'], ))
            db.commit()

            return redirect(url_for('naju.index'))

        flash('Maybe your username was typed wrong. Please try again!')
    return render_template('naju/activate_user.html')


@bp.route('/accounts')
@admin_required
def accounts():
    users = get_db().execute('SELECT * FROM user ORDER BY name ASC').fetchall()
    return render_template('naju/accounts.html', users=users)


@bp.route('/account/delete/<int:id>')
@admin_required
def del_user(id):
    db = get_db()

    db.execute('DELETE FROM user WHERE id = ?', (id, ))
    db.commit()

    return redirect(url_for('naju.home'))
