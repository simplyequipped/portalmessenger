import os
import secrets

from flask import Flask


# app factory
def create_app(test_config=None):
    # create and configure the app
    #app = Flask(__name__, instance_relative_config=True)
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY = secrets.token_hex(),
        DATABASE = os.path.join(app.instance_path, 'portal.sqlite')
    )

#    if test_config is None:
#        # load the instance config, if it exists, when not testing
#        app.config.from_pyfile('config.py', silent=True)
#    else:
#        # load the test config if passed in
#        app.config.from_mapping(test_config)

    # ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # initialize database from schema
    from . import db
    db.init_app(app)

    # import view blueprints
    from . import portal
    app.register_blueprint(portal.bp)

    # initalize js8call modem
    from .modem import js8callmodem
    app.config['MODDEM'] = js8callmodem()
    app.config['MODDEM'].start()
    
    return app
