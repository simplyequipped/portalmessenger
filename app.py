import json
import secrets
import random
import time

import pyjs8call

from flask import Flask, render_template, request, session
from flask_socketio import SocketIO

app = Flask(__name__)
app.secret_key = secrets.token_hex()
socketio = SocketIO(app)

#TODO stop js8call app when socketio closed



### flask routes and template handling

@app.route('/')
@app.route('/conversations', methods=['GET', 'POST'])
@app.route('/conversations.html', methods=['GET', 'POST'])
def conversations():
    if request.method == 'POST':
        session['username'] = request.form.get('user')
        return ''
    else:
        return render_template('conversations.html')

@app.route('/chat')
@app.route('/chat.html')
def chat():
    username = session.get('username')
    last_heard_timestamp = user_last_heard_timestamp(username)

    chat_data = {
        'username': username,
        'history': user_chat_history(username),
        'presence': presence(last_heard_timestamp),
        'last_heard': last_heard_minutes(last_heard_timestamp)
    }
    print(chat_data)

    return render_template('chat.html', chat_data = chat_data)

@app.route('/settings')
@app.route('/settings.html')
def settings():
    return render_template('settings.html')



### socket.io functions

@socketio.on('user')
def set_user(data):
    #session['username'] = data['user']
    #print(session['username'])
    pass

@socketio.on('tx msg')
def tx_msg(data):
    js8call.send_directed_message(session.get('username'), data['msg'])
    
def rx_msg(msg):
    chat_msg = {
        'id': secrets.token_urlsafe(16),
        'type': 'incoming',
        'time': time.strftime('%X%p', time.localtime(msg['time'])).lower(),
        'text': msg['value'],
        'tx_status': None
    }

    socketio.emit('rx msg', chat_msg)

@socketio.on('log')
def log(data):
    print('\tlog: ' + str(data['msg']))

@socketio.on('heard-user')
def heard_user(data):
    last_heard = user_last_heard_timestamp(data['user'])

    if last_heard != None:
        last_heard = last_heard_minutes(last_heard)
        socketio.emit('heard-user', last_heard)

#TODO
@socketio.on('test-conv')
def test_conv():
    spots = [{
    'username': 'HG5HTG',
    'last_heard': 5
    }]
    socketio.emit('heard-list', spots)


@socketio.on('pin')
def pin_user(data):
    pass

@socketio.on('unpin')
def unpin_user(data):
    pass



### helper functions

def local_time_str(timestamp):
    return time.strftime('%X%p', time.localtime(timestamp))

def last_heard_minutes(timestamp):
    return int((time.time() - timestamp) / 60)


def user_last_heard_timestamp(username):
    #TODO
    return time.time() - random.randint(0, 60 * 60)

    spots = js8call.get_station_spots(station = username)

    if len(spots) > 0:
        spots.sort(key = lambda spot: spot['time'])
        return spots[-1]
    else:
        return None

#TODO
def presence(timestamp):
    #TODO calculate presence based on timestamp
    return random.choice(['active', 'inactive', 'unknown'])

#TODO
def user_chat_history(username):
    history = []
    chat = {
        'id': secrets.token_urlsafe(16),
        'type': 'rx',
        'time': '8:56pm',
        'text': 'Hello there, how are you?',
        'tx_status': None
    }
    history.append(chat)

    chat = {
        'id': secrets.token_urlsafe(16),
        'type': 'tx',
        'time': '8:57pm',
        'text': 'Hey! Good, how about you?',
        'tx_status': None
    }
    history.append(chat)

    chat = {
        'id': secrets.token_urlsafe(16),
        'type': 'rx',
        'time': '8:57pm',
        'text': 'Glad to hear it. What\'s new?',
        'tx_status': None
    }
    history.append(chat)

    chat = {
        'id': secrets.token_urlsafe(16),
        'type': 'tx',
        'time': '8:58pm',
        'text': 'Not much new here',
        'tx_status': 'Sending...'
    }
    history.append(chat)

    chat = {
        'id': secrets.token_urlsafe(16),
        'type': 'rx',
        'time': '8:56pm',
        'text': 'Hello there, how are you?',
        'tx_status': None
    }
    history.append(chat)

    chat = {
        'id': secrets.token_urlsafe(16),
        'type': 'tx',
        'time': '8:57pm',
        'text': 'Hey! Good, how about you?',
        'tx_status': None
    }
    history.append(chat)

    chat = {
        'id': secrets.token_urlsafe(16),
        'type': 'rx',
        'time': '8:57pm',
        'text': 'Glad to hear it. What\'s new?',
        'tx_status': None
    }
    history.append(chat)

    chat = {
        'id': secrets.token_urlsafe(16),
        'type': 'tx',
        'time': '8:58pm',
        'text': 'Not much new here',
        'tx_status': 'Sending...'
    }
    history.append(chat)

    chat = {
        'id': secrets.token_urlsafe(16),
        'type': 'rx',
        'time': '8:56pm',
        'text': 'Hello there, how are you?',
        'tx_status': None
    }
    history.append(chat)

    chat = {
        'id': secrets.token_urlsafe(16),
        'type': 'tx',
        'time': '8:57pm',
        'text': 'Hey! Good, how about you?',
        'tx_status': None
    }
    history.append(chat)

    chat = {
        'id': secrets.token_urlsafe(16),
        'type': 'rx',
        'time': '8:57pm',
        'text': 'Glad to hear it. What\'s new?',
        'tx_status': None
    }
    history.append(chat)

    chat = {
        'id': secrets.token_urlsafe(16),
        'type': 'tx',
        'time': '8:58pm',
        'text': 'Not much new here',
        'tx_status': 'Sending...'
    }
    history.append(chat)

    return history

def heard(spots):
    # only unique spots with the latest timestamp
    heard_data = {}
    for spot in spots:
        if spot['from'] not in heard_data.keys():
            heard_data[spot['from']] = spot['time']
        elif spot['time'] > heard_data[spot['from']]:
            heard_data[spot['from']] = spot['time']

    for username, timestamp in heard_data.items():
        heard = {
            'username': username, 
            'last_heard': last_heard_minutes(timestamp)
            }
        socketio.emit('heard', heard)



### initialize js8call client

#js8call = pyjs8call.Client()
#if 'Portal' not in js8call.config.get_profile_list():
#    js8call.config.create_new_profile('Portal')
#
#js8call.set_config_profile('Portal')
#js8call.register_rx_callback(rx_msg, pyjs8call.Message.RX_DIRECTED)
#js8call.start()
#js8call.spot_monitor.set_new_spot_callback(heard)


if __name__ == 'main':
    socketio.run(app, debug=True)

