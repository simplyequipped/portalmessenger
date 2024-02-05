import time

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

    for i in range(len(conversations)):
        spots = current_app.config['MODEM'].get_spots(origin = conversations[i]['username'], count = 1)

        # use latest station spot timestamp if more recent
        if len(spots) > 0 and spots[0].timestamp > conversations[i]['time']:
             conversations[i]['time'] = spots[0].timestamp
    
    socketio.emit('conversation', conversations)

# get chat history between users
@socketio.on('init-chat')
def init_chat():
    msgs = db.get_user_chat_history( current_app.config['ACTIVE_CHAT_USER'], db.get_setting_value('callsign') )
    socketio.emit('msg', msgs)

# get network activity data
@socketio.on('network')
def network_data():
    # activity since aging setting
    activity = current_app.config['MODEM'].js8call.get_call_activity( age = db.get_setting_value('aging') )
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
    if not current_app.config['MODEM'].online():
        # returns once application is started
        current_app.config['MODEM'].start()
    socketio.emit('power-on')

@socketio.on('power-off')
def power_off():
    # wait for current transactions to finish
    time.sleep(0.1)
    current_app.config['MODEM'].stop()
    socketio.emit('power-off')

@socketio.on('power-restart')
def power_restart():
    # wait for current transactions to finish
    time.sleep(0.1)
    socketio.emit('power-off')
    # returns once application restarts
    current_app.config['MODEM'].restart()
    socketio.emit('power-on')

