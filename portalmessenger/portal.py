#import os
#import argparse
#import subprocess
import time

from flask import render_template, request, session, redirect, current_app
from flask_socketio import SocketIO

import portalmessenger
from portalmessenger import db



### flask routes and template handling

@app.route('/')
@app.route('/stations', methods=['GET', 'POST'])
@app.route('/stations.html', methods=['GET', 'POST'])
def stations_route():
    if request.method == 'POST':
         app.config['ACTIVE_CHAT_USER'] = request.form.get('user')
        return ''
    else:
        if db.get_setting_value('callsign') == '':
            return redirect('/settings')

        app.config['ACTIVE_CHAT_USER'] = None
        return render_template( 'stations.html', settings = db.get_settings() )

@app.route('/network')
@app.route('/network.html')
def network_route():
    return render_template('network.html', settings = db.get_settings())

@app.route('/chat')
@app.route('/chat.html')
def chat_route():
    mark_user_msgs_read(app.config['ACTIVE_CHAT_USERNAME'])
    return render_template('chat.html', user = app.config['ACTIVE_CHAT_USER'], settings = db.get_settings())

@app.route('/settings', methods=['GET', 'POST'])
@app.route('/settings.html', methods=['GET', 'POST'])
def settings_route():
    if request.method == 'POST':
        settings = db.get_settings()
        restart = False
        error_msg = []
        #TODO WIP here

        # process posted settings
        for setting, value in request.form.items():
            if setting == 'callsign' or setting == 'grid':
                value = value.upper()

            if setting in settings.keys() and value != settings[setting]['value']:
                # see settings.py for settings dict and validation criteria
                valid = portalmessenger.settings.settings[setting]['validate'](value)

                if valid:
                    db.set_setting(setting, value)

                    if app.config['MODEM'].name.lower() == 'js8call':
                        # update settings in js8call
                        if setting == 'callsign':
                            app.config['MODEM'].js8call.settings.set_station_callsign(value)
                            restart = True
                        elif setting == 'speed':
                            app.config['MODEM'].js8call.settings.set_speed(value)
                            restart = True
                        elif setting == 'grid':
                            app.config['MODEM'].js8call.settings.set_station_grid(value)
                        elif setting == 'freq':
                            app.config['MODEM'].js8call.settings.set_freq(value)
                        elif setting == 'heartbeat':
                            if value == 'enable':
                                app.config['MODEM'].js8call.heartbeat.enable()
                            else:
                                app.config['MODEM'].js8call.heartbeat.disable()
                        #TODO
                        #elif setting == 'encryption':
                        #    if value == 'enable':
                        #        current_app.config['MODEM'].enable_encryption()
                        #    else:
                        #        current_app.config['MODEM'].disable_encryption()

                    elif app.config['MODEM'].name.lower() == 'demo':
                        if setting == 'callsign':
                            app.config['MODEM'].callsign = value
    
                else:
                    settings[setting]['error'] = 'Invalid {}'.format(setting)

        if restart:
            app.config['MODEM'].restart()

    #TODO get server IP address at app init
    return render_template('settings.html', settings = settings, ip = app.config['LOCAL_IP'])



### socket.io functions

# log to terminal
@socketio.on('log')
def log(data):
    print( '\tlog: {}'.format(data['msg']) )

# outgoing message
@socketio.on('msg')
def tx_msg(data):
    msg = app.config['MODEM'].send(data['user'], data['text'])
    msg = process_message(msg)
    # include processed message in active chat
    socketio.emit('msg', [msg])

# initilize station spot data
@socketio.on('spot')
def init_spots():
    # spots since aging setting
    age = 60 * db.get_setting_value('aging') # convert minutes to seconds
    spots = app.config['MODEM'].get_spots(age = age)

    if len(spots) > 0:
        spots = [{'username': spot.origin, 'time': spot.timestamp} for spot in spots]
        socketio.emit('spot', spots)

# get stored chat conversations: dict(username, last heard timestamp, unread count)
@socketio.on('conversation')
def init_conversations():
    conversations = db.get_user_conversations( db.get_setting_value('callsign') )

    for i in range(len(conversations)):
        spots = app.config['MODEM'].get_spots(origin = conversations[i]['username'], count = 1)

        # use latest station spot timestamp if more recent
        if len(spots) > 0 and spots[0].timestamp > conversations[i]['time']:
             conversations[i]['time'] = spots[0].timestamp
    
    socketio.emit('conversation', conversations)

# get chat history between users
@socketio.on('init-chat')
def init_chat():
    msgs = db.get_user_chat_history( app.config['ACTIVE_CHAT_USERNAME'], db.get_setting_value('callsign') )
    socketio.emit('msg', msgs)

# get network activity data
@socketio.on('network')
def network_data():
    # activity since aging setting
    activity = app.config['MODEM'].js8call.get_call_activity( age = db.get_setting_value('aging') )
    network = []

    for station in activity:
        # set spot attributes to non-blank space if not set, formatted value otherwise
        if station['grid'] == '':
            grid = '&nbsp;'
        else:
            grid = station['grid']

        if station['distance'][0] is None:
            distance = '&nbsp;'
        else:
            # station['distance'] = (distance, distance_units, bearing)
            distance = '({:,} {})'.format(station['distance'][0], station['distance'][1])

        if station['speed'] == '':
            speed = '&nbsp;'
        else:
            speed = station['speed'][0].upper() + station['speed'][1,]

        if len(station['hearing']) == 0:
            hearing = '&nbsp;'
        else:
            hearing = ', '.join(station['hearing'])

        if len(station['heard_by']) == 0:
            heard_by = '&nbsp;'
        else:
            heard_by = ', '.join(station['heard_by'])

        station = {
            'username': station['origin'],
            'grid': grid,
            'distance': distance,
            'time': station['timestamp'],
            'time_str': station['local_time_str'],
            'snr': station['snr'],
            'speed': speed,
            'hearing': hearing,
            'heard_by': heard_by
        }

        network.append(station)

    socketio.emit('network', network)

@socketio.on('power-on')
def power_on():
    # wait for current transactions to finish
    time.sleep(0.1)
    if not app.config['MODEM'].online():
        # returns once application is started
        app.config['MODEM'].start()
    socketio.emit('power-on')

@socketio.on('power-off')
def power_off():
    # wait for current transactions to finish
    time.sleep(0.1)
    app.config['MODEM'].stop()
    socketio.emit('power-off')

@socketio.on('power-restart')
def power_restart():
    # wait for current transactions to finish
    time.sleep(0.1)
    socketio.emit('power-off')
    # returns once application restarts
    current_app.config['MODEM'].restart()
    socketio.emit('power-on')



### helper functions
# must use flask.current_app to get app context

# msg = pyjs8call.Message object
def process_message(msg):
    msg = {
        'id': msg.id,
        'origin': msg.origin,
        'destination': msg.destination,
        'type': msg.type[0:2].lower(), # RX.DIRECTED = 'rx', TX.SEND_MESSAGE = 'tx'
        'time': msg.timestamp,
        'text': msg.text,
        'encrypted': msg.get('encrypted'),
        'error': msg.error,
        'unread': False,
        'status': msg.status
        }

    if msg['type'] == 'rx' and msg['origin'] != current_app.config['ACTIVE_CHAT_USER']:
        msg['unread'] = True

    if msg['type'] == 'tx':
        msg['origin'] = db.get_setting_value('callsign')

        if msg['status'] != 'failed':
            msg['status'] = 'queued'
    
    db.store_message(msg)

    return msg

# incoming directed message callback
#TODO confirm: this function does not have the flask request context because it is called via callback
def incoming_message(msg):
    msg = process_message(msg)

    if msg['origin'] == current_app.config['ACTIVE_CHAT_USER']:
    # pass messages for active chat to client side
        socketio.emit('msg', [msg])

    unread = bool( db.get_user_unread_message_count(msg['origin']) )

    conversation = {
        'username': msg['origin'], 
        'time': msg['time'],
        'unread': unread
    }

    # pass conversation to client side
    socketio.emit('conversation', [conversation])

# new spots callback
def new_spots(spots):
    spots = [{'username': spot.origin, 'time': spot.timestamp} for spot in spots]
    socketio.emit('spot', spots)
    
# outgoing message status change callback
def outgoing_status(msg):
    # works inconsistently without this delay, root cause unknown
    time.sleep(0.001)
    db.update_outgoing_message_status(msg)
    socketio.emit('update-tx-status', {'id': msg.id, 'status': msg.status})




### parse args ###
#parser = argparse.ArgumentParser()
#parser.add_argument('--headless', action='store_true', help='show or hide the JS8Ccall app using xvfb')
#parser.add_argument('-d', '--demo', action='store_true', help='run without requiring a modem app to be installed')
#parser.add_argument('--app')
#parser.add_argument('run')
#TODO parser.add_argument('-i', '--incognito', action='store_true', help='use sqlite in memory only, no data is stored after exit')
#args = parser.parse_args()


    
if __name__ == 'main':
    app = portalmessenger.create_app()
    app.run(host='0.0.0.0')
    socketio = SocketIO(app)
    # TODO turn off debugging in production
    socketio.run(app, debug=True)
    
