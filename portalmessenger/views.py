from flask import Blueprint, render_template, request, redirect, current_app

import portalmessenger
from portalmessenger import db
from portalmessenger import settings


bp = Blueprint('portalmessenger', __name__)


@bp.route('/')
@bp.route('/stations', methods=['GET', 'POST'])
@bp.route('/stations.html', methods=['GET', 'POST'])
def stations_route():
    if request.method == 'POST':
        username = request.form.get('user').strip()

        if '>' in username:
            # remove spaces around relay characters
            username = '>'.join([user.strip() for user in username.split('>')])
        
        current_app.config['ACTIVE_CHAT_USER'] = username
        return ''
    else:
        if db.get_setting_value('callsign') == '':
            return redirect('/settings')

        current_app.config['ACTIVE_CHAT_USER'] = None
        return render_template('stations.html', settings = db.get_settings())

@bp.route('/quit')
@bp.route('/quit.html')
def quit_route():
    return render_template('quit.html', settings = db.get_settings())

@bp.route('/network')
@bp.route('/network.html')
def network_route():
    return render_template('network.html', settings = db.get_settings())

@bp.route('/chat')
@bp.route('/chat.html')
def chat_route():
    db.set_user_messages_read(current_app.config['ACTIVE_CHAT_USER'])
    return render_template('chat.html', user = current_app.config['ACTIVE_CHAT_USER'], settings = db.get_settings())

@bp.route('/settings', methods=['GET', 'POST'])
@bp.route('/settings.html', methods=['GET', 'POST'])
def settings_route():
    if request.method == 'POST':
        # validate and update posted settings
        updated_settings = settings.update_settings(request.form)

        # restart modem if required
        if any([updated_settings[setting]['restart'] for setting in updated_settings]):
            current_app.config['MODEM'].restart()

        return render_template('settings.html', settings = updated_settings, ip = current_app.config['LOCAL_IP'])
        
    return render_template('settings.html', settings = db.get_settings(), ip = current_app.config['LOCAL_IP'])

@bp.route('/propagation')
@bp.route('/propagation.html')
def propagation_route():
    return render_template('propagation.html', settings = db.get_settings())
    
