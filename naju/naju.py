import functools
import os
import re
from urllib.parse import urlparse

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app, send_from_directory,
    send_file, session
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from naju.database import get_db
from naju.util import random_uri_safe_string, nbit_int

bp = Blueprint('naju', __name__)


ALLOWED_EXTENSIONS = {'txt', 'xml', 'html'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def is_http_url(string):
    o = urlparse(string)
    return o.scheme in ('http', 'https') and len(o.netloc) > 0


types = ("Text", "Datum", "Nummer", "Kommazahl", "Link", "Wahr / Falsch")


def is_type_valid(param_type):
    return param_type in types


def is_param_valid(param, type):
    if not is_type_valid(type):
        return False
    if type == "Link":
        return is_http_url(param)
    return True


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not g.user:
            flash('Du musst eingeloggt sein!')
            return redirect(url_for('naju.index'))
        return view(**kwargs)

    return wrapped_view


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute('SELECT * FROM user WHERE id = ?', (user_id,)).fetchone()


@bp.route('/', methods=('GET', 'POST'))
def index():
    if g.user is not None:
        return redirect(url_for('naju.home'))

    if request.method == 'POST':
        try:
            test_name = request.form['username']
            password = request.form['password']
            username = str(test_name).lower()
        except:
            flash('Post incorrect!')
            print('Post incorrect!')
            return render_template('naju/login.html')

        db = get_db()
        error = None

        user = db.execute('SELECT * FROM user WHERE name = ? OR email = ? OR name = ?', (username, username, test_name)).fetchone()

        if password == '':
            error = 'Es wurde kein Passwort angegeben!'
        elif user is None:
            error = 'Der Benutzername existiert nicht.'
        elif not check_password_hash(user['pwd_hash'], password):
            error = 'Das Passwort ist falsch.'
        elif user['email_confirmed'] == 0:
            error = 'Ihre E-Mail ist noch nicht verifiziert.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']

            return redirect(url_for('naju.home'))
        flash(error)

    return render_template('naju/login.html')


@bp.route('/account/reset', methods=('GET', 'POST'))
def reset_password_request():
    if request.method == 'POST':
        try:
            username = str(request.form['username']).lower()
            mail = str(request.form['mail']).lower()
        except:
            flash('Post incorrect!')
            print('Post incorrect!')
            return render_template('naju/login.html')

        db = get_db()

        user = db.execute('SELECT * FROM user WHERE name = ? AND email = ?', (username, mail,)).fetchone()

        print(str(user))
        users = db.execute('SELECT * FROM user').fetchone()
        print(users['email'])

        if user is not None:
            token = random_uri_safe_string(64)

            db.execute('UPDATE user SET password_reset_token = ? WHERE id = ?', (token, user['id'],))
            db.commit()

            from naju.emails import send_password_reset_email

            send_password_reset_email(user['email'], user, token)
            return redirect(url_for('naju.index'))
    return render_template('naju/reset_request.html')


@bp.route('/reset/<token>', methods=('GET', 'POST'))
def password_reset(token):
    db = get_db()
    user = db.execute('SELECT * FROM user WHERE password_reset_token = ?', (token,)).fetchone()
    if user is not None:
        if request.method == 'POST':
            try:
                name = str(request.form['username']).lower()
                password = request.form['password']
                check = request.form['passwordcheck']
            except:
                flash('Post incorrect!')
                return redirect(url_for('home.index'))

            if password == '' or str(password).isspace():
                flash('You must give a password')
                return render_template('naju/reset_password.html')

            user = db.execute('SELECT * FROM user WHERE password_reset_token = ? AND name = ?', (token, name, )).fetchone()

            if user is not None and password == check:
                db = get_db()
                db.execute('UPDATE user SET pwd_hash = ?, password_reset_token = ? WHERE id = ?',
                           (generate_password_hash(password), None, user['id'], ))
                db.commit()
                return redirect(url_for('naju.index'))
        return render_template('naju/reset_password.html')
    else:
        return redirect(url_for('naju.index'))


@bp.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect(url_for('naju.index'))


@bp.route('/home/', methods=('GET', 'POST'))
@login_required
def home():
    if request.method == 'POST':
        import naju.excel as e

        file = e.create_table()

        attachment_name = "Baumbestand.xlsx"

        return send_file(file, as_attachment=True, attachment_filename=attachment_name)

    db = get_db()

    trees = db.execute("SELECT * FROM tree t, area a WHERE t.area_id = a.id ORDER BY name, number").fetchall()

    params = db.execute("SELECT * FROM tree_param_type ORDER BY order_id, name").fetchall()

    areas = db.execute("SELECT * FROM area a ORDER BY name").fetchall()

    datas = []

    from markupsafe import escape

    for tree in trees:
        data = '<tr><td class="searchable Fläche"><a href="' + url_for('naju.area', id=tree['area_id']) + '">' + str(escape(tree['name'])) + '</a></td>'
        data += '<td class="searchable Nummer">' + str(escape(tree['number'])) + '</td>'

        for par in params:
            value = db.execute("SELECT * FROM tree_param WHERE tree_id = ? AND param_id = ? ", (tree['id'], par['id'])).fetchone()
            if value is None:
                data += '<td class="searchable ' + str(escape(par['name'])) + '">None</td>'
            elif par['type'] == 'Link':
                data += '<td class="searchable ' + str(escape(par['name'])) + '"><a href="' + str(escape(value['value'])) + '">' + str(escape(value['value'])) + '</a></td>'
            else:
                data += '<td class="searchable ' + str(escape(par['name'])) + '">' + str(escape(value['value'])) + '</td>'

        data += '<td class="editable-cell"><a href="' + url_for('naju.edit_tree', id=tree['id']) + '"><i class="far fa-edit"></i></a></td>'
        data += '<td class="editable-cell"><a href="' + url_for('naju.delete_tree', id=tree['id']) + """" onclick="return confirm('Wollen sie diesen Baum wirklich löschen? Er kann nicht wiederhergestellt werden!')"><i class="fas fa-trash"></i></a></td>"""
        data += '</tr>'
        datas.append(data)

    return render_template('naju/main.html', datas=datas, areas=areas, params=params, trees=trees, filters=[])


@bp.route('/home/<search>', methods=('GET', 'POST'))
@login_required
def filtered_home(search=''):
    if search == '':
        return redirect(url_for('naju.home'))

    filters = search.split('|', -1)
    filter_datas = []

    for search_filter in filters:
        expressions = search_filter.split(':', 1)
        if len(expressions) < 2:
            continue

        filter_type = expressions[0]
        filter_search = expressions[1]
        filter_datas.append([filter_type, filter_search])

    if request.method == 'POST':
        import naju.excel as e

        file = e.create_table(filters=filters)

        attachment_name = "Baumbestand_" + search + ".xlsx"
        return send_file(file, as_attachment=True, attachment_filename=attachment_name)

    db = get_db()

    trees = db.execute("SELECT * FROM tree t, area a WHERE t.area_id = a.id ORDER BY name, number").fetchall()

    params = db.execute("SELECT * FROM tree_param_type ORDER BY order_id, name").fetchall()

    areas = db.execute("SELECT * FROM area a ORDER BY name").fetchall()

    datas = []

    filtered_trees = []

    from markupsafe import escape

    for tree in trees:
        is_tree_valid = True

        for search_filter in filters:
            expressions = search_filter.rsplit(':')
            if len(expressions) < 2:
                continue

            filter_type = expressions[0]
            filter_search = expressions[1]

            if filter_type.lower() == 'alle':
                is_filter_in = False
                if str(tree['number']).lower() == filter_search.lower():
                    is_filter_in = True
                if str(tree['name']).lower().find(filter_search.lower()) > -1:
                    is_filter_in = True
                for par in params:
                    value = db.execute("SELECT * FROM tree_param WHERE tree_id = ? AND param_id = ? ",
                                       (tree['id'], par['id'])).fetchone()
                    if str(value['value']).lower().find(filter_search.lower()) > -1:
                        is_filter_in = True
                        break
                if not is_filter_in:
                    is_tree_valid = False
                    break
            if filter_type.lower() == 'nummer':
                if str(tree['number']).lower() != filter_search.lower():
                    is_tree_valid = False
                    break
            elif filter_type.lower() == 'Fläche'.lower():
                if str(tree['name']).lower().find(filter_search.lower()) == -1:
                    is_tree_valid = False
                    break
            else:
                for par in params:
                    if str(par['name']).lower() == filter_type.lower():
                        value = db.execute("SELECT * FROM tree_param WHERE tree_id = ? AND param_id = ? ",
                                           (tree['id'], par['id'])).fetchone()
                        if value is None:
                            is_tree_valid = False
                            break
                        elif str(value['value']).lower().find(filter_search.lower()) == -1 or str(value['value']) == '':
                            is_tree_valid = False
                            break

        if not is_tree_valid:
            continue

        filtered_trees.append(tree)

        data = '<tr><td class="searchable Fläche"><a href="' + url_for('naju.area', id=tree['area_id']) + '">' + str(
            escape(tree['name'])) + '</a></td>'
        data += '<td class="searchable Nummer">' + str(escape(tree['number'])) + '</td>'

        for par in params:
            value = db.execute("SELECT * FROM tree_param WHERE tree_id = ? AND param_id = ? ",
                               (tree['id'], par['id'])).fetchone()
            if value is None:
                data += '<td class="searchable ' + str(escape(par['name'])) + '">None</td>'
            elif par['type'] == 'Link':
                data += '<td class="searchable ' + str(escape(par['name'])) + '"><a href="' + str(
                    escape(value['value'])) + '">' + str(escape(value['value'])) + '</a></td>'
            else:
                data += '<td class="searchable ' + str(escape(par['name'])) + '">' + str(
                    escape(value['value'])) + '</td>'

        data += '<td class="editable-cell"><a href="' + url_for('naju.edit_tree', id=tree[
            'id']) + '"><i class="far fa-edit"></i></a></td>'
        data += '<td class="editable-cell"><a href="' + url_for('naju.delete_tree', id=tree[
            'id']) + """" onclick="return confirm('Wollen sie diesen Baum wirklich löschen? Er kann nicht wiederhergestellt werden!')"><i class="fas fa-trash"></i></a></td>"""
        data += '</tr>'
        datas.append(data)

    return render_template('naju/main.html', datas=datas, areas=areas, params=params, trees=filtered_trees, filters=filter_datas)


@bp.route('/home/download/<string:type>/<string:filter>', methods=['GET'])
@bp.route('/home/download', methods=['GET'])
@login_required
def download_file(type="", filter=""):
    import naju.excel as e
    file = e.create_table(type, filter)

    attachment_name = "Baumbestand_" + filter + ".xlsx"
    return send_file(file, as_attachment=True, attachment_filename=attachment_name)


@bp.route('/add/tree', methods=('GET', 'POST'))
@login_required
def add_tree():
    db = get_db()

    if request.method == 'POST':
        try:
            area = request.form['area']
            number = request.form['number']
        except:
            flash('Post incorrect!')
            print('Post incorrect!')
            return redirect(url_for('naju.add_tree'))

        error = None

        if area is None:
            error = "Es muss eine Fläche ausgewählt werden"
        if number is None:
            error = "Es wird eine Nummer benötigt"

        try:
            number = nbit_int(number)
        except ValueError:
            error = "Es wird eine Zahl benötigt"

        db = get_db()
        check = None
        if error is None:
            check = db.execute("SELECT * FROM tree t, area a WHERE a.id = t.area_id AND t.number = ? AND a.name = ?",
                               (number, area)).fetchone()
        if check is not None:
            error = "Dieser Baum existiert bereits!"

        if error is None:
            area_id = db.execute("SELECT id FROM area WHERE name = ?", (area,)).fetchone()

            db.execute("INSERT INTO tree (number, area_id) VALUES (?, ?)",
                       (number, area_id['id']))

            params = db.execute('SELECT * FROM tree_param_type').fetchall()

            tree = db.execute('SELECT * FROM tree WHERE number = ? AND area_id = ?',
                              (number, area_id['id'])).fetchone()

            for param in params:
                db.execute("INSERT INTO tree_param (tree_id, param_id, value) VALUES (?, ?, ?)",
                           (tree['id'], param['id'], ""))

            db.commit()

            return redirect(url_for('naju.home'))
        flash(error)

    areas = db.execute('SELECT * FROM area ORDER BY name').fetchall()

    return render_template('naju/add_tree.html', areas=areas)


@bp.route('/add/area', methods=('GET', 'POST'))
@login_required
def add_area():
    if request.method == 'POST':
        try:
            name = request.form['name']
            short = request.form['short']
            address = request.form['address']
            link = request.form['link']
        except:
            flash('Post incorrect!')
            print('Post incorrect!')
            return render_template('naju/add_area.html')

        error = None

        if name is None:
            error = "Es wird ein Name benötigt"
        if short is None:
            error = "Es wird ein kürzel benötigt"
        if address is None:
            error = "Es wird eine Addresse benötigt"
        if link is None or not is_http_url(link):
            error = "Es wird ein Link benötigt"

        db = get_db()
        check = db.execute("SELECT * FROM area WHERE short = ? OR name = ?", (short, name)).fetchone()
        if check is not None:
            error = "Diese Fläche existiert bereits!"

        if error is None:
            db.execute("INSERT INTO area (name, short, address, link) VALUES (?, ?, ?, ?)",
                       (name, short, address, link))
            db.commit()

            return redirect(url_for('naju.home'))
        flash(error)
    return render_template('naju/add_area.html')


@bp.route('/add/param', methods=('GET', 'POST'))
@login_required
def add_param():
    db = get_db()

    if request.method == 'POST':
        try:
            name = request.form['name']
            type = request.form['type']
        except:
            flash('Post incorrect!')
            print('Post incorrect!')
            return redirect(url_for('naju.add_tree'))

        error = None

        if name is None:
            error = "Es muss ein Name angegeben werden"
        if type is None or not is_type_valid(type):
            error = "Es wird ein valider Datentyp benötigt"

        db = get_db()
        check = db.execute("SELECT * FROM tree_param_type WHERE name = ?",
                           (name,)).fetchone()

        if check is not None:
            error = "Dieser Parameter existirt bereits"

        if error is None:
            db.execute('INSERT INTO tree_param_type (name, type, order_id) VALUES (?, ?, ?)', (name, type, 0))

            param = db.execute('SELECT * FROM tree_param_type WHERE name=? AND type=?', (name, type)).fetchone()

            trees = db.execute('SELECT * FROM tree').fetchall()

            for tree in trees:
                db.execute("INSERT INTO tree_param (tree_id, param_id, value) VALUES (?, ?, ?)",
                           (tree['id'], param['id'], ""))

            db.commit()

            return redirect(url_for('naju.home'))
        flash(error)

    return render_template('naju/add_param.html')


@bp.route('/edit/tree/<int:id>', methods=('GET', 'POST'))
@login_required
def edit_tree(id):
    db = get_db()

    tree = db.execute('SELECT * FROM tree t, area a WHERE t.area_id = a.id AND t.id = ?', (id,)).fetchone()

    params = db.execute('SELECT * FROM tree_param tp, tree_param_type tpt '
                        'WHERE tp.tree_id = ? AND tpt.id = tp.param_id ORDER BY tpt.name', (id,)).fetchall()

    if request.method == 'POST':
        try:
            number = request.form['number']
        except:
            flash('Post incorrect!')
            print('Post incorrect!')
            return render_template('naju/edit_tree.html', tree=tree, params=params)

        if number != tree['number']:
            try:
                number = nbit_int(number)
            except ValueError:
                flash("Bitte gebe eine valide Zahl an!")
                return render_template('naju/edit_tree.html', tree=tree, params=params)

            check = db.execute("SELECT * FROM tree t, area a WHERE a.id = t.area_id AND t.number = ? AND a.id = ?",
                               (number, tree['area_id'])).fetchone()

            if check is not None and check['id'] != id:
                flash("Dieser Baum existiert bereits!")
                return render_template('naju/edit_tree.html', tree=tree, params=params)

            db.execute('UPDATE tree SET number=? WHERE id=?', (number, id))

        for param in params:
            try:
                p = request.form[param['name']]
            except:
                p = None

            if p is not None or param['type'] == "Wahr / Falsch":
                if param['type'] == "Wahr / Falsch" or is_param_valid(p, param['type']):
                    if param['type'] == "Wahr / Falsch":
                        if p:
                            db.execute('UPDATE tree_param SET value=? WHERE tree_id=? AND param_id=?',
                                       ("Ja", id, param['id']))
                        else:
                            db.execute('UPDATE tree_param SET value=? WHERE tree_id=? AND param_id=?',
                                       ("Nein", id, param['id']))
                    else:
                        db.execute('UPDATE tree_param SET value=? WHERE tree_id=? AND param_id=?',
                                   (p, id, param['id']))
                else:
                    flash('Incorrect input')
                    print('Post incorrect!')
                    return render_template('naju/edit_tree.html', tree=tree, params=params)

            db.commit()

        return redirect(url_for('naju.home'))

    return render_template('naju/edit_tree.html', tree=tree, params=params)


@bp.route('/edit/area/<int:id>', methods=('GET', 'POST'))
@login_required
def edit_area(id):
    db = get_db()

    my_area = db.execute('SELECT * FROM area WHERE id=?', (id,)).fetchone()

    if request.method == 'POST':
        try:
            name = request.form['name']
            short = request.form['short']
            address = request.form['address']
            link = request.form['link']
        except:
            flash('Post incorrect!')
            print('Post incorrect!')
            return render_template('naju/add_area.html')

        error = None

        if name is None:
            error = "Es wird ein Name benötigt"
        if short is None:
            error = "Es wird ein kürzel benötigt"
        if address is None:
            error = "Es wird eine Addresse benötigt"
        if link is None or not is_http_url(link):
            error = "Es wird ein Link benötigt"

        check = db.execute("SELECT * FROM area WHERE short = ? OR name = ?", (short, name)).fetchone()
        if check is not None and check['id'] != id:
            error = "Diese Fläche existiert bereits!"

        if error is None:
            if my_area['name'] != name:
                db.execute("UPDATE area SET name=? WHERE id=?",
                           (name, id))
            if my_area['short'] != short:
                db.execute("UPDATE area SET short=? WHERE id=?",
                           (short, id))
            if my_area['address'] != name:
                db.execute("UPDATE area SET address=? WHERE id=?",
                           (address, id))
            if my_area['link'] != short:
                db.execute("UPDATE area SET link=? WHERE id=?",
                           (link, id))

            db.commit()
            return redirect(url_for('naju.home'))
        flash(error)
    return render_template('naju/edit_area.html', area=my_area)


@bp.route('/edit/param/<int:id>', methods=('GET', 'POST'))
@login_required
def edit_param(id):
    db = get_db()

    param = db.execute('SELECT * FROM tree_param_type WHERE id=?', (id,)).fetchone()

    if request.method == 'POST':
        try:
            name = request.form['name']
            type = request.form['type']
            order_id = request.form['number']
        except:
            flash('Post incorrect!')
            print('Post incorrect!')
            return redirect(url_for('naju.add_tree'))

        error = None

        if name is None:
            error = "Es muss ein Name angegeben werden"
        if type is None or not is_type_valid(type):
            error = "Es wird ein valider Datentyp benötigt"

        db = get_db()
        check = db.execute("SELECT * FROM tree_param_type WHERE name = ?",
                           (name,)).fetchone()

        if check is not None and check['id'] != id:
            error = "Dieser Parameter existirt bereits"

        if error is None:
            db.execute('UPDATE tree_param_type SET name=?, type=?, order_id=? WHERE id=?', (name, type, order_id, id))

            db.commit()

            return redirect(url_for('naju.home'))
        flash(error)

    return render_template('naju/edit_param.html', param=param)


@bp.route('/delete/tree/<int:id>')
@login_required
def delete_tree(id):
    db = get_db()

    db.execute('DELETE FROM tree WHERE id=?', (id,))
    db.execute('DELETE FROM tree_param WHERE tree_id=?', (id,))
    db.commit()

    return redirect(url_for('naju.home'))


@bp.route('/delete/area/<int:id>')
@login_required
def delete_area(id):
    db = get_db()

    trees = db.execute('SELECT * FROM tree WHERE area_id=?', (id,)).fetchall()

    for tree in trees:
        db.execute('DELETE FROM tree WHERE id=?', (tree['id'],))
        db.execute('DELETE FROM tree_param WHERE tree_id=?', (tree['id'],))

    db.execute('DELETE FROM area WHERE id=?', (id,))

    db.commit()

    return redirect(url_for('naju.home'))


@bp.route('/delete/param/<int:id>')
@login_required
def delete_param(id):
    db = get_db()

    db.execute('DELETE FROM tree_param WHERE param_id=?', (id,))
    db.execute('DELETE FROM tree_param_type WHERE id=?', (id,))

    db.commit()

    return redirect(url_for('naju.home'))


@bp.route('/help/')
def help():
    return render_template('naju/help.html')


@bp.route('/area/<int:id>/')
@login_required
def area(id):
    area = get_db().execute('SELECT * FROM area WHERE id = ?', (id,)).fetchone()
    return render_template('naju/area.html', area=area)


@bp.route('/tree/<int:id>/')
@login_required
def tree(id):
    db = get_db()

    tree = db.execute('SELECT * FROM tree t, area a WHERE t.area_id = a.id AND t.id = ?', (id,)).fetchone()

    params = db.execute('SELECT * FROM tree_param tp, tree_param_type tpt '
                        'WHERE tp.tree_id = ? AND tpt.id = tp.param_id ORDER BY tpt.name', (id,)).fetchall()

    return render_template('naju/tree.html', tree=tree, params=params)


@bp.route('/confirm/<token>', methods=('GET', 'POST'))
def confirm_mail(token):
    db = get_db()
    user = db.execute('SELECT * FROM user WHERE confirmation_token = ?', (token,)).fetchone()
    if user is not None:

        db = get_db()
        db.execute('UPDATE user SET email_confirmed = ?, confirmation_token = ?',
                   (1, None,))
        db.commit()

        return redirect(url_for('naju.index'))
    else:
        return redirect(url_for('home.index'))


@bp.route('/license')
def license():
    return render_template('home/license.html')


@bp.route('/imprint')
def imprint():
    return render_template('home/imprint.html')


@bp.route('/privacy')
def privacy():
    return render_template('home/privacy.html')


@bp.route('/app/android')
def android_app():
    file = os.path.join(current_app.instance_path, 'app-release.apk')

    return send_file(file, as_attachment=True, attachment_filename='NaJu-Baumbestand.apk')


@bp.route('/update', methods=('GET', 'POST'))
def update_data():
    if request.method == 'POST':
        try:
            data = request.files['data']
        except:
            return '<error>Fehler: Daten sind falsch angegeben</error>'

        if data and allowed_file(data.filename):
            from . import read_xml
            filename = secure_filename(data.filename)
            filename = filename.rsplit('.')[0]
            import time
            path = os.path.join(current_app.instance_path, 'assets', 'uploads')
            os.makedirs(path, exist_ok=True)
            path = os.path.join(path, str(time.time()) + filename + '.xml')
            data.save(path)
            if read_xml.read(path):
                db = get_db()

                trees = db.execute('SELECT * FROM tree').fetchall()
                areas = db.execute('SELECT * FROM area').fetchall()
                tree_params = db.execute('SELECT * FROM tree_param').fetchall()
                tree_param_types = db.execute('SELECT * FROM tree_param_type').fetchall()

                return render_template('export.html', trees=trees, areas=areas,
                                       tree_params=tree_params, tree_param_types=tree_param_types)
        return '<error>Fehler: Falscher Benutzername oder Passwort</error>'
    return render_template('import.html')
