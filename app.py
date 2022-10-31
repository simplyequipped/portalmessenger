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
    return render_template('chat.html')

@app.route('/settings')
@app.route('/settings.html')
def settings():
    return render_template('settings.html')

@socketio.on('user')
def set_user(data):
    #session['username'] = data['user']
    #print(session['username'])
    pass

@socketio.on('init chat')
def init_chat():
    user_data = {}
    username = session.get('username')
    last_heard_timestamp = get_user_last_heard_timestamp(username)

    user_data['username'] = username
    user_data['history'] = get_user_chat_history(username)
    user_data['heard'] = get_last_heard_text(last_heard_timestamp)
    user_data['presence'] = get_user_presence(last_heard_timestamp)

    socketio.emit('init chat', user_data)

#TODO
def get_last_heard_text(timestamp):
    #TODO parse timestamp to local time
    return '1 minute'

#TODO
def get_user_last_heard_timestamp(username):
    return '8:57pm'

#TODO
def get_user_presence(timestamp):
    #TODO calculate presence based on timestamp
    return random.choice(['active', 'inactive', 'unknown'])

#TODO
def get_user_chat_history(username):
    history = []
    chat = {
        'id': secrets.token_urlsafe(16),
        'type': 'incoming',
        'time': '8:56pm',
        'text': 'Hello there, how are you?',
        'tx_status': None
    }
    history.append(chat)

    chat = {
        'id': secrets.token_urlsafe(16),
        'type': 'outgoing',
        'time': '8:57pm',
        'text': 'Hey! Good, how about you?',
        'tx_status': None
    }
    history.append(chat)

    chat = {
        'id': secrets.token_urlsafe(16),
        'type': 'incoming',
        'time': '8:57pm',
        'text': 'Glad to hear it. What\'s new?',
        'tx_status': None
    }
    history.append(chat)

    chat = {
        'id': secrets.token_urlsafe(16),
        'type': 'outgoing',
        'time': '8:58pm',
        'text': 'Not much new here',
        'tx_status': 'Sending...'
    }
    history.append(chat)

    return history




@socketio.on('tx msg')
def tx_msg(data):
    js8call.send_directed_message(session.get('username'), data['msg'])
    
def rx_msg(msg):
    chat_msg = {
        'id': secrets.token_urlsafe(16),
        'type': 'incoming',
        'time': time.strftime('%X%p', time.localtime(msg['time']).lower(),
        'text': msg['value'],
        'tx_status': None
    }

    socketio.emit('rx msg', chat_msg)



@socketio.on('log')
def log(data):
    print('\tlog: ' + str(data['msg']))


# initialize js8call client
js8call = pyjs8call.Client()
if 'Portal' not in js8call.config.get_profile_list():
    js8call.config.create_new_profile('Portal')

js8call.set_config_profile('Portal')
js8call.register_rx_callback(rx_msg, pyjs8call.Message.RX_DIRECTED)
js8call.start()


if __name__ == 'main':
    socketio.run(app, debug=True)

