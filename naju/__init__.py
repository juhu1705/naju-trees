import os
from threading import Thread

from flask import Flask


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    os.makedirs(app.instance_path, exist_ok=True)

    app.config.from_mapping(SECRET_KEY=read_or_generate_secret_key(app),
                            DATABASE=os.path.join(app.instance_path, 'dfs.sqlite'))

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    os.makedirs(os.path.join(app.instance_path, 'assets/pictures/profile'), exist_ok=True)

    # thread = Thread(target=server.run)
    # thread.start()

    from . import database
    database.init_app(app)

    from . import naju
    app.register_blueprint(naju.bp)

    from . import admin
    app.register_blueprint(admin.bp)

    return app


def read_or_generate_secret_key(app: Flask) -> bytes:
    """ Liest den Secret Key aus bzw. generiert ihn, falls noch keiner vorhanden ist. """
    secret_key_path = os.path.join(app.instance_path, "SECRET_KEY")

    if not os.path.isfile(secret_key_path):
        with open(os.open(secret_key_path, os.O_WRONLY | os.O_CREAT, mode=0o600), "wb") as file:
            secret_key = os.urandom(128)
            file.write(secret_key)
    else:
        with open(secret_key_path, "rb") as file:
            secret_key = file.read()

    return secret_key
