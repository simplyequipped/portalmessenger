import threading
from flask import Blueprint, render_template, request, redirect, current_app, make_response

import portalmessenger
from portalmessenger import db
from portalmessenger import settings


bp = Blueprint('portalmessenger', __name__)

# decorator for view functions to set headers to prevent cacheing
def no_cache(view):
    def no_cache_view(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    return no_cache_view


@no_cache
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

@no_cache
@bp.route('/quit')
@bp.route('/quit.html')
def quit_route():
    return render_template('quit.html', settings = db.get_settings())

@no_cache
@bp.route('/network')
@bp.route('/network.html')
def network_route():
    return render_template('network.html', settings = db.get_settings())

@no_cache
@bp.route('/chat')
@bp.route('/chat.html')
def chat_route():
    db.set_user_messages_read(current_app.config['ACTIVE_CHAT_USER'])
    return render_template('chat.html', user = current_app.config['ACTIVE_CHAT_USER'], settings = db.get_settings())

@no_cache
@bp.route('/settings', methods=['GET', 'POST'])
@bp.route('/settings.html', methods=['GET', 'POST'])
def settings_route():
    # possible status:
    #    view: initial view render
    #    success: settings update successful
    #    error: error while validating settings
    #    restart: js8call restart required to update settings
    if request.method == 'POST':
        status = 'success'
        # validate and update posted settings
        updated_settings = settings.update_settings(request.form)
        
        if any([updated_settings[setting]['error'] for setting in updated_settings]):
            status = 'error'

        if status != 'error' and any([updated_settings[setting]['restart'] for setting in updated_settings]):
            status = 'restart'
            current_app.config['MODEM'].restart_async()
            # post-restart settings moved to callbacks.py -> restart_callback()
        return render_template('settings.html', settings = updated_settings, ip = current_app.config['LOCAL_IP'], status=status)
        
    return render_template('settings.html', settings = db.get_settings(), ip = current_app.config['LOCAL_IP'], status='view')

@no_cache
@bp.route('/propagation')
@bp.route('/propagation.html')
def propagation_route():
    return render_template('propagation.html', settings = db.get_settings())
    
