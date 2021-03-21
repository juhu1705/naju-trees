import os
from threading import Thread

from flask import Flask


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(SECRET_KEY='219z4r34äc3ü696567ß50917325#897235jhkle65bju#5',
                            DATABASE=os.path.join(app.instance_path, 'dfs.sqlite'))

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
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
