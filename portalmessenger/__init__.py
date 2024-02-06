import os
import socket
import secrets

from flask import Flask


# app factory
def create_app(test_config=None):
    # create and configure the app
    #app = Flask(__name__, instance_relative_config=True)
    app = Flask(__name__)
    app.config['SECRET_KEY'] = secrets.token_hex()
    app.config['DATABASE'] = 'portal.sqlite'
    app.config['LOCAL_IP'] = get_local_ip()

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    from . import views
    app.register_blueprint(views.bp)

    from . import db
    # close database on app teardown
    app.teardown_appcontext(db.close_db)

    with app.app_context():
        # initialize database from schema and default settings
        db.init_db()

        # initalize pyjs8call modem
        from .modem.js8callmodem import JS8CallModem
        app.config['MODEM'] = JS8CallModem( db.get_setting_value('callsign') )
        # initialize pyjs8call config before start (see pyjs8call.settings docs)
        app.config['MODEM'].js8call.settings.set_speed( db.get_setting_value('speed') )
        # start pyjs8call modem
        app.config['MODEM'].start()
        
        # initialize settings with running application
        app.config['MODEM'].js8call.settings.set_station_grid( db.get_setting_value('grid') )
        app.config['MODEM'].js8call.settings.set_freq( db.get_setting_value('freq') )
    
        if db.get_setting_value('heartbeat') == 'enable':
            app.config['MODEM'].js8call.heartbeat.enable()

    def app_context_aware(func):
        def _wrapped_function(*args, **kwargs):
            with app.app_context():
                func(*args, **kwargs)
        return _wrapped_function

    # set modem callback functions
    from . import callbacks
    app.config['MODEM'].incoming = app_context_aware(callbacks.incoming_message)
    app.config['MODEM'].spots = app_context_aware(callbacks.new_spots)
    app.config['MODEM'].outgoing = app_context_aware(callbacks.outgoing_status)
    
    # configure modem setting update functions
    from .settings import default_settings
    default_settings['callsign']['update'] = app.config['MODEM'].update_callsign
    default_settings['freq']['update'] = app.config['MODEM'].update_freq
    default_settings['grid']['update'] = app.config['MODEM'].update_grid
    default_settings['speed']['update'] = app.config['MODEM'].update_speed
    default_settings['heartbeat']['update'] = app.config['MODEM'].update_heartbeat
    default_settings['inbox']['update'] = app.config['MODEM'].update_inbox
    
    from . import websockets
    websockets.socketio.init_app(app)

    return (app, websockets.socketio)

def get_local_ip():
    try:
        # create a dummy connection to get the local IP address
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except socket.error:
        return 'unavailable'

