import os
import socket
import secrets
import configparser

from flask import Flask

# app factory
def create_app(test_config=None, headless=True, debugging=False, pyjs8call_settings_path=None):
    # create and configure the app
    app = Flask(__name__)
    app.config['SECRET_KEY'] = secrets.token_hex()
    app.config['DATABASE'] = '.portal.sqlite'
    app.config['LOCAL_IP'] = get_local_ip()
    app.config['ACTIVE_CHAT_USER'] = None

    if test_config is not None:
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
        app.config['MODEM'] = JS8CallModem()

        # load pyjs8call settings from file and initialize in app settings
        loaded_settings = {}
        if pyjs8call_settings_path is not None:
            app.config['MODEM'].js8call.settings.load(pyjs8call_settings_path)
            
            for setting in ['callsign', 'speed', 'grid', 'freq']:
                if setting in app.config['MODEM'].js8call.settings.loaded_settings['station']:
                    loaded_settings[setting] = app.config['MODEM'].js8call.settings.loaded_settings['station'][setting]

            if 'enable' in app.config['MODEM'].js8call.settings.loaded_settings['heartbeat']:
                loaded_settings['heartbeat'] = 'enable' if app.config['MODEM'].js8call.settings.loaded_settings['heartbeat']['enable'].lower() in ['true', 'yes'] else 'disable'

            from . import settings
            updated_settings = settings.update_settings(loaded_settings)
            updated_settings_errors = [updated_settings[setting]['error'] for setting in updated_settings if updated_settings[setting]['error'] is not None]

            if len(updated_settings_errors) > 0:
                raise ValueError(', '.join(updated_settings_error))

        # initialize pyjs8call config before start (see pyjs8call.settings docs)
        if 'callsign' not in loaded_settings:
            callsign = db.get_setting_value('callsign')
            if callsign not in [None, '']:
                app.config['MODEM'].update_callsign(callsign)
        if 'speed' not in loaded_settings:
            app.config['MODEM'].update_speed(db.get_setting_value('speed'))

        # start pyjs8call modem
        print('Starting JS8Call modem via pyjs8call...')
        app.config['MODEM'].start(headless=headless, debugging=debugging)
        print('JS8Call started')

        # initialize running modem application settings
        app.config['MODEM'].update_freq(db.get_setting_value('freq'))
        app.config['MODEM'].update_grid(db.get_setting_value('grid'))
        app.config['MODEM'].update_heartbeat(db.get_setting_value('heartbeat'))
        app.config['MODEM'].update_inbox(db.get_setting_value('inbox'))

        app.jinja_env.add_extension('jinja2.ext.loopcontrols')

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

