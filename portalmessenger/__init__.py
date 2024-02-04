import os
import socket
import secrets

from flask import Flask

#from portalmessenger import portal


# app factory
def create_app(test_config=None):
    # create and configure the app
    #app = Flask(__name__, instance_relative_config=True)
    app = Flask(__name__)
    app.config['SECRET_KEY'] = secrets.token_hex()
    app.config['DATABASE'] = 'portal.sqlite'
    app.config['LOCAL_IP'] = get_local_ip()

    print(app.config['DATABASE'])

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    from . import db
    # close database on app teardown
    app.teardown_appcontext(db.close_db)

    # initialize database from schema
    with app.app_context():
        db.init_db()

        # initalize js8call modem
        from .modem.js8callmodem import JS8CallModem
        app.config['MODEM'] = JS8CallModem( db.get_setting_value('callsign') )
        # initialize pyjs8call config before start
        app.config['MODEM'].js8call.settings.set_speed( db.get_setting_value('speed') )
        # set callback functions
        #app.config['MODEM'].incoming = portal.incoming_message
        #app.config['MODEM'].spots = portal.new_spots
        #app.config['MODEM'].outgoing = portal.outgoing_status
        # start pyjs8call
        app.config['MODEM'].start()
        
        # initialize settings with running application
        app.config['MODEM'].js8call.settings.set_station_grid( db.get_setting_value('grid') )
        app.config['MODEM'].js8call.settings.set_freq( db.get_setting_value('freq') )
    
        if db.get_setting_value('heartbeat') == 'enable':
            app.config['MODEM'].js8call.heartbeat.enable()

    # stop modem on app teardown
    app.teardown_appcontext(app.config['MODEM'].js8call.stop)
    
    return app

def get_local_ip():
    try:
        return socket.gethostbyname( socket.gethostname() )
    except socket.error:
        return 'unavailable'
