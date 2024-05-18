import os
import socket
import secrets
import configparser

from flask import Flask

# app factory
def create_app(test_config=None, headless=True, debugging=False, pyjs8call_settings_path=None, database_path=None):
    # create and configure the app
    app = Flask(__name__)
    app.config['SECRET_KEY'] = secrets.token_hex()
    app.config['DATABASE'] = '.portal.sqlite'
    app.config['LOCAL_IP'] = get_local_ip()
    app.config['ACTIVE_CHAT_USER'] = None

    if test_config is not None:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    if database_path is not None and os.path.exists(database_path):
        if os.path.isdir(database_path):
            database_path = os.path.join(database_path, '.portal.sqlite')

        database_path = os.path.expanduser(database_path)
        database_path = os.path.abspath(database_path)
        app.config['DATABASE'] = database_path

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

        # configure modem setting update functions
        from . import settings
        settings.default_settings['callsign']['update'] = app.config['MODEM'].update_callsign
        settings.default_settings['speed']['update'] = app.config['MODEM'].update_speed
        settings.default_settings['groups']['update'] = app.config['MODEM'].update_groups
        settings.default_settings['freq']['update'] = app.config['MODEM'].update_freq
        settings.default_settings['grid']['update'] = app.config['MODEM'].update_grid
        settings.default_settings['heartbeat']['update'] = app.config['MODEM'].update_heartbeat
        settings.default_settings['inbox']['update'] = app.config['MODEM'].update_inbox
    
        loaded_settings = {}
        if pyjs8call_settings_path is not None:
            # load pyjs8call settings from file and initialize app settings
            app.config['MODEM'].js8call.settings.load(pyjs8call_settings_path)
            pyjs8call_loaded_settings = app.config['MODEM'].js8call.settings.loaded_settings

            if 'station' in pyjs8call_loaded_settings and 'callsign' in pyjs8call_loaded_settings['station']:
                loaded_settings['callsign'] = pyjs8call_loaded_settings['station']['callsign']
            if 'station' in pyjs8call_loaded_settings and 'speed' in pyjs8call_loaded_settings['station']:
                loaded_settings['speed'] = pyjs8call_loaded_settings['station']['speed']
            if 'station' in pyjs8call_loaded_settings and 'grid' in pyjs8call_loaded_settings['station']:
                loaded_settings['grid'] = pyjs8call_loaded_settings['station']['grid']
            if 'station' in pyjs8call_loaded_settings and 'freq' in pyjs8call_loaded_settings['station']:
                loaded_settings['freq'] = pyjs8call_loaded_settings['station']['freq']
            if 'general' in pyjs8call_loaded_settings and 'groups' in pyjs8call_loaded_settings['general']:
                loaded_settings['groups'] = pyjs8call_loaded_settings['general']['groups']
            if 'heartbeat' in pyjs8call_loaded_settings and 'enable' in pyjs8call_loaded_settings['heartbeat']:
                loaded_settings['heartbeat'] = 'enable' if pyjs8call_loaded_settings['heartbeat']['enable'].lower() in ('true', 'yes') else 'disable'

            updated_settings = settings.update_settings(loaded_settings)
            updated_settings_errors = [updated_settings[setting]['error'] for setting in updated_settings if updated_settings[setting]['error'] is not None]
            
            if len(updated_settings_errors) > 0:
                raise ValueError(', '.join(updated_settings_error))

        # set js8call config file settings before starting the modem
        # loaded settings take priority
        if 'callsign' not in loaded_settings:
            callsign = db.get_setting_value('callsign')
            if callsign not in (None, ''):
                #app.config['MODEM'].update_callsign(callsign)
                settings.default_setting['callsign']['update'](callsign)
        if 'speed' not in loaded_settings:
            #app.config['MODEM'].update_speed(db.get_setting_value('speed'))
            settings.default_setting['speed']['update'](db.get_setting_value('speed'))
        if 'groups' not in loaded_settings:
            #app.config['MODEM'].update_speed(db.get_setting_value('speed'))
            settings.default_setting['groups']['update'](db.get_setting_value('groups'))

        # start pyjs8call modem
        print('Starting JS8Call modem via pyjs8call...')
        app.config['MODEM'].start(headless=headless, debugging=debugging)
        print('JS8Call started')

        # initialize running modem application settings
        #app.config['MODEM'].update_freq(db.get_setting_value('freq'))
        settings.default_settings['freq']['update'](db.get_setting_value('freq'))
        #app.config['MODEM'].update_grid(db.get_setting_value('grid'))
        settings.default_settings['grid']['update'](db.get_setting_value('grid'))
        #app.config['MODEM'].update_heartbeat(db.get_setting_value('heartbeat'))
        settings.default_settings['heartbeat']['update'](db.get_setting_value('heartbeat'))
        #app.config['MODEM'].update_inbox(db.get_setting_value('inbox'))
        settings.default_settings['inbox']['update'](db.get_setting_value('inbox'))

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

