from xml.dom import minidom

from werkzeug.security import check_password_hash

from naju.database import get_db


def read(file):

    document = minidom.parse(file)

    users = document.getElementsByTagName('user')
    db = get_db()

    valid_user = False

    for user in users:
        to_check = db.execute('SELECT * FROM user WHERE name=? OR email=?',
                              (user.attributes['name'].value, user.attributes['name'].value)).fetchone()
        if to_check is not None and check_password_hash(to_check['pwd_hash'], user.attributes['pass'].value):
            valid_user = True

    if not valid_user:
        return False

    handle_area(document, db)
    handle_trees(document, db)
    handle_param_types(document, db)
    handle_params(document, db)

    db.commit()

    import os
    if os.path.exists(file):
        os.remove(file)

    return True


def handle_area(document, db=get_db()):
    areas = document.getElementsByTagName('area')

    for area in areas:
        to_edit = db.execute('SELECT * FROM area WHERE name = ?', (area.attributes['name'].value, )).fetchone()
        if to_edit is None:
            db.execute('INSERT INTO area (name, address, link, short) VALUES (?, ?, ?, ?)',
                       (area.attributes['name'].value, area.attributes['address'].value,
                        area.attributes['link'].value, area.attributes['short'].value))
            to_edit = db.execute('SELECT * FROM area WHERE name = ?', (area.attributes['name'].value,)).fetchone()

        id = to_edit['id']

        if area.firstChild.data != to_edit['name']:
            db.execute("UPDATE area SET name=? WHERE id=?",
                       (area.firstChild.data, id))
        if area.attributes['short'].value != to_edit['short']:
            db.execute("UPDATE area SET short=? WHERE id=?",
                       (area.attributes['short'].value, id))
        if area.attributes['address'].value != to_edit['address']:
            db.execute("UPDATE area SET address=? WHERE id=?",
                       (area.attributes['address'].value, id))
        if area.attributes['link'].value != to_edit['link']:
            db.execute("UPDATE area SET link=? WHERE id=?",
                       (area.attributes['link'].value, id))
        if area.attributes['delete'].value == 'delete':
            trees = db.execute('SELECT * FROM tree WHERE area_id=?', (id,)).fetchall()

            for tree in trees:
                db.execute('DELETE FROM tree WHERE id=?', (tree['id'],))
                db.execute('DELETE FROM tree_param WHERE tree_id=?', (tree['id'],))

            db.execute('DELETE FROM area WHERE id=?', (id,))


def handle_trees(document, db=get_db()):
    trees = document.getElementsByTagName('tree')

    for tree in trees:
        area = db.execute('SELECT * FROM area WHERE name = ?', (tree.attributes['area_name'].value, )).fetchone()

        if area is None:
            continue

        to_edit = db.execute('SELECT * FROM tree WHERE number = ? AND area_id = ?',
                             (tree.attributes['number'].value, area['id'])).fetchone()
        if to_edit is None:
            db.execute('INSERT INTO tree (number, area_id) VALUES (?, ?)',
                       (tree.attributes['number'].value, area['id']))
            to_edit = db.execute('SELECT * FROM tree WHERE number = ? AND area_id = ?',
                                 (tree.attributes['number'].value, area['id'])).fetchone()

        if to_edit['number'] != tree.firstChild.data:
            db.execute("UPDATE tree SET number=? WHERE id=?",
                       (area.firstChild.data, to_edit['id']))
        if tree.attributes['delete'].value == 'delete':
            db.execute('DELETE FROM tree WHERE id=?', (to_edit['id'],))
            db.execute('DELETE FROM tree_param WHERE tree_id=?', (to_edit['id'],))


def handle_param_types(document, db=get_db()):
    param_types = document.getElementsByTagName('type')

    for param_type in param_types:
        to_edit = db.execute('SELECT * FROM tree_param_type WHERE name = ?',
                             (param_type.attributes['name'].value,)).fetchone()

        if to_edit is None:
            db.execute('INSERT INTO tree_param_type (name, type, order_id) VALUES (?, ?, ?)',
                       (param_type.attributes['name'].value, param_type.attributes['type'].value,
                        param_type.attributes['order_id'].value))
            to_edit = db.execute('SELECT * FROM tree_param_type WHERE name = ?',
                                 (param_type.attributes['name'].value, )).fetchone()

        if to_edit['name'] != param_type.firstChild.data:
            db.execute("UPDATE tree_param_type SET name=? WHERE id=?",
                       (param_type.firstChild.data, to_edit['id']))
        if to_edit['type'] != param_type.firstChild.data:
            db.execute("UPDATE tree_param_type SET type=? WHERE id=?",
                       (param_type.attributes['type'].value, to_edit['id']))
        if to_edit['order_id'] != param_type.firstChild.data:
            db.execute("UPDATE tree_param_type SET order_id=? WHERE id=?",
                       (param_type.attributes['order_id'].value, to_edit['id']))
        if param_type.attributes['delete'].value == 'delete':
            db.execute('DELETE FROM tree_param WHERE param_id=?', (to_edit['id'],))
            db.execute('DELETE FROM tree_param_type WHERE id=?', (to_edit['id'],))


def handle_params(document, db=get_db()):
    params = document.getElementsByTagName('param')

    for param in params:
        tree = db.execute('SELECT * FROM area a, tree t WHERE t.area_id = a.id AND t.number = ? AND a.name = ?',
                          (param.attributes['tree_number'].value, param.attributes['tree_area_name'].value)).fetchone()
        param_type = db.execute('SELECT * FROM tree_param_type WHERE name = ?',
                                (param.attributes['param_type'].value,)).fetchone()

        if tree is None or param_type is None:
            continue

        to_edit = db.execute('SELECT * FROM tree_param WHERE tree_id = ? AND param_id = ?',
                             (tree['id'], param_type['id'])).fetchone()
        if to_edit is None:
            db.execute('INSERT INTO tree_param (tree_id, param_id, value) VALUES (?, ?, ?)',
                       (tree['id'], param_type['id'], param.attributes['value'].value))
            to_edit = db.execute('SELECT * FROM tree_param WHERE tree_id = ? AND param_id = ?',
                                 (tree['id'], param_type['id'])).fetchone()

        if to_edit['value'] != param.attributes['value'].value:
            db.execute("UPDATE tree_param SET value=? WHERE tree_id=? AND param_id=?",
                       (param.attributes['value'].value, tree['id'], param_type['id']))
