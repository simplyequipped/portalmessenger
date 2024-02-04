from flask import Blueprint, render_template, request, redirect, current_app

from portalmessenger import db


bp = Blueprint('portalmessenger', __name__)


@bp.route('/')
@bp.route('/stations', methods=['GET', 'POST'])
@bp.route('/stations.html', methods=['GET', 'POST'])
def stations_route():
    if request.method == 'POST':
        current_app.config['ACTIVE_CHAT_USER'] = request.form.get('user')
        return ''
    else:
        if db.get_setting_value('callsign') == '':
            return redirect('/settings')

        current_app.config['ACTIVE_CHAT_USER'] = None
        return render_template( 'stations.html', settings = db.get_settings() )

@bp.route('/network')
@bp.route('/network.html')
def network_route():
    return render_template('network.html', settings = db.get_settings())

@bp.route('/chat')
@bp.route('/chat.html')
def chat_route():
    db.set_user_messages_read(current_app.config['ACTIVE_CHAT_USERNAME'])
    return render_template('chat.html', user = current_app.config['ACTIVE_CHAT_USER'], settings = db.get_settings())

@bp.route('/settings', methods=['GET', 'POST'])
@bp.route('/settings.html', methods=['GET', 'POST'])
def settings_route():
    if request.method == 'POST':
        settings = db.get_settings()
        restart = False
        error_msg = []

        # process posted settings
        for setting, value in request.form.items():
            if setting == 'callsign' or setting == 'grid':
                value = value.upper()

            if setting in settings.keys() and value != settings[setting]['value']:
                # see settings.py for settings dict and validation criteria
                valid = portalmessenger.settings.settings[setting]['validate'](value)

                if valid:
                    db.set_setting(setting, value)

                    if current_app.config['MODEM'].name.lower() == 'js8call':
                        # update settings in js8call
                        if setting == 'callsign':
                            current_app.config['MODEM'].js8call.settings.set_station_callsign(value)
                            restart = True
                        elif setting == 'speed':
                            current_app.config['MODEM'].js8call.settings.set_speed(value)
                            restart = True
                        elif setting == 'grid':
                            current_app.config['MODEM'].js8call.settings.set_station_grid(value)
                        elif setting == 'freq':
                            current_app.config['MODEM'].js8call.settings.set_freq(value)
                        elif setting == 'heartbeat':
                            if value == 'enable':
                                current_app.config['MODEM'].js8call.heartbeat.enable()
                            else:
                                current_app.config['MODEM'].js8call.heartbeat.disable()
                        #TODO
                        #elif setting == 'encryption':
                        #    if value == 'enable':
                        #        current_app.config['MODEM'].enable_encryption()
                        #    else:
                        #        current_app.config['MODEM'].disable_encryption()

                    #TODO
                    #elif current_app.config['MODEM'].name.lower() == 'demo':
                    #    if setting == 'callsign':
                    #        current_app.config['MODEM'].callsign = value
    
                else:
                    settings[setting]['error'] = 'Invalid {}'.format(setting)

        if restart:
            current_app.config['MODEM'].restart()

    #TODO get server IP address at app init
    return render_template('settings.html', settings = settings, ip = current_app.config['LOCAL_IP'])


