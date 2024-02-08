import os
import socket
import secrets
import configparser
import importlib.util

from flask import Flask


# app factory
def create_app(test_config=None, headless=True, pyjs8call_config_path=None):
    # create and configure the app
    app = Flask(__name__)
    app.config['SECRET_KEY'] = secrets.token_hex()
    app.config['DATABASE'] = '.portal.sqlite'
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
        #TODO set callsign after init for consistency
        app.config['MODEM'] = JS8CallModem(db.get_setting_value('callsign'), headless=headless)

        # load and parse pyjs8call config from file
        if pyjs8call_config_path not in [None, ''] and os.path.exists(pyjs8call_config_path):
            # import pyjs8call config file as module
            spec = importlib.util.spec_from_file_location('pyjs8call_config_module', pyjs8call_config_path)
            pyjs8call_config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(pyjs8call_config_module)
            
            # get dict of variable names and values, ignoring special variables, functions, and classes
            pyjs8call_config = {var.lower(): getattr(pyjs8call_config_module, var) for var in dir(pyjs8call_config_module)
                                if not var.startswith('__') and
                                not callable(getattr(pyjs8call_config_module, var)) and
                                not isinstance(getattr(pyjs8call_config_module, var), type)}

            # call each pyjs8call.settings function
            for func, value in pyjs8call_config.items():
                pyjs8call_settings_func = getattr(app.config['MODEM'].js8call.settings, func)

                if value is None:
                    pyjs8call_settings_func()
                else:
                    pyjs8call_settings_func(value)
            
        # initialize pyjs8call config before start (see pyjs8call.settings docs)
        app.config['MODEM'].js8call.settings.set_speed( db.get_setting_value('speed') )
        # start pyjs8call modem
        print('Starting JS8Call modem via pyjs8call...')
        app.config['MODEM'].start()
        print('JS8Call started')
        
        # initialize running modem application settings
        app.config['MODEM'].js8call.settings.set_station_grid( db.get_setting_value('grid') )
        app.config['MODEM'].js8call.settings.set_freq( db.get_setting_value('freq') )
    
        if db.get_setting_value('heartbeat') == 'enable':
            app.config['MODEM'].js8call.heartbeat.enable()
            
        if db.get_setting_value('inbox') == 'enable':
            app.config['MODEM'].js8call.inbox.enable()
        elif 'query' in db.get_setting_value('inbox'):
            app.config['MODEM'].js8call.inbox.enable(query=True)

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

