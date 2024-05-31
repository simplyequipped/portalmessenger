import os
import time
import signal

from flask import current_app
from flask_socketio import SocketIO

from portalmessenger import db
from portalmessenger import message


socketio = SocketIO()


# log to terminal
@socketio.on('log')
def log(data):
    print( '\tlog: {}'.format(data['msg']) )

# outgoing message
@socketio.on('msg')
def tx_msg(data):
    msg = current_app.config['MODEM'].send(data['user'], data['text'])
    msg = message.process_message(msg)
    # include processed message in active chat
    socketio.emit('msg', [msg])
    
@socketio.on('heard-user')
def heard_user(data):
    db_last_msg = db.get_last_user_msg_timestamp(data['user'])
    spot_last_heard = current_app.config['MODEM'].get_spots(origin=data['user'], count=1)

    db_last_msg = db_last_msg if db_last_msg is not None else 0
    spot_last_heard = spot_last_heard[0].timestamp if len(spot_last_heard) > 0 else 0
    last_heard = max(db_last_msg, spot_last_heard)

    socketio.emit('heard-user', last_heard)

# initilize station spot data
@socketio.on('spot')
def init_spots():
    # spots since aging setting
    age = 60 * db.get_setting_value('aging') # convert minutes to seconds
    spots = current_app.config['MODEM'].get_spots(age = age)

    if len(spots) > 0:
        spots = [{'username': spot.origin, 'time': spot.timestamp} for spot in spots]
        socketio.emit('spot', spots)

# get stored chat conversations: dict(username, last heard timestamp, unread count)
@socketio.on('conversation')
def init_conversations():
    conversations = db.get_user_conversations( db.get_setting_value('callsign') )
    socketio.emit('conversation', conversations)

# remove stored chat conversations for specified user
@socketio.on('remove-conversation')
def remove_conversation(data):
    db.remove_user_conversations(data['username'])
    socketio.emit('conversation-removed', {'username': data['username']})

# get chat history between users
@socketio.on('init-chat')
def init_chat():
    msgs = db.get_user_chat_history( current_app.config['ACTIVE_CHAT_USER'], db.get_setting_value('callsign') )
    socketio.emit('msg', msgs)

# get network activity data
@socketio.on('network')
def network_data():
    aging = db.get_setting_value('aging')
    # network activity since aging setting
    activity = current_app.config['MODEM'].get_call_activity(age = aging, hearing_age = aging * 10)
    network = []
    # html collapses empty elements, use character(s) or &nbsp;
    blank_str = ' --'

    for station in activity:
        # set station attributes to formatted value or non-blank space
        station = {
            'username': station['origin'],
            'grid': station['grid'] if station['grid'] is not None else blank_str,
            'distance': station['distance'] if station['distance'] is not None else '&nbsp;',
            'time': station['timestamp'],
            'time_str': station['local_time_str'],
            'snr': station['snr'] if station['snr'] is not None else blank_str,
            'speed': station['speed'][0].upper() + station['speed'][1:] if station['speed'] not in (None, '') else blank_str,
            'hearing': station['hearing'] if station['hearing'] is not None else blank_str,
            'heard_by': station['heard_by'] if station['heard_by'] is not None else blank_str
        }
        network.append(station)

    socketio.emit('network', network)

# get median grid propagation data
@socketio.on('propagation-data')
def propagation_data(max_age=60):
    # propagation data format: {'propagation': [ [lat, lon, snr], ... ], 'station': [lat, lon]}
    data = current_app.config['MODEM'].get_propagation_data(max_age = max_age)
    socketio.emit('propagation-data', data)

@socketio.on('restart-status')
def restart_status():
    socketio.emit('restart-status', current_app.config['MODEM'].online())

@socketio.on('close-portal')
def close_portal():
    time.sleep(0.1)
    current_app.config['MODEM'].stop()
    time.sleep(1)
    os.kill( os.getpid(), signal.SIGINT )
    
