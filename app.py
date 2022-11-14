import json
import secrets
import random
import time
import sqlite3

import pyjs8call

from flask import Flask, render_template, request, session, redirect
from flask_socketio import SocketIO

app = Flask(__name__)
app.secret_key = secrets.token_hex()
socketio = SocketIO(app)

#TODO stop js8call app when socketio closed



### flask routes and template handling

@app.route('/')
@app.route('/stations', methods=['GET', 'POST'])
@app.route('/stations.html', methods=['GET', 'POST'])
def stations():
    if request.method == 'POST':
        session['active_chat_username'] = request.form.get('user')
        #TODO
        session['logged_in_username'] = 'KC3KVT'
        return ''
    else:
        global settings
        if settings['callsign']['value'] == '':
            return redirect('/settings')

        if 'active_chat_username' in session.keys():
            del session['active_chat_username']

        return render_template('stations.html')

@app.route('/chat')
@app.route('/chat.html')
def chat():
    username = session.get('active_chat_username')
    return render_template('chat.html', user = username)

@app.route('/settings', methods=['GET', 'POST'])
@app.route('/settings.html', methods=['GET', 'POST'])
def settings():
    global settings

    if request.method == 'POST':
        for setting, value in request.form.items():
            if setting in settings.keys():
                valid, error = validate_setting(setting, value)

                if valid:
                    # store new setting value
                    settings[setting]['value'] = value
            

    return render_template('settings.html', settings = settings)



### socket.io functions

@socketio.on('msg')
def tx_msg(data):
    #TODOjs8call
    #global js8call
    msg = process_tx_msg(data['user'], data['text'], time.time())
    #js8call.send_directed_message(msg['to'], msg['text'])
    socketio.emit('msg', [msg])
    
@socketio.on('log')
def log(data):
    print('\tlog: ' + str(data['msg']))

@socketio.on('heard-user')
def heard_user(data):
    last_heard = user_last_heard_timestamp(data['user'])
    socketio.emit('heard-user', last_heard)

# initilize spot data
@socketio.on('spot')
def update_spots():
    #TODOjs8call
    #global js8call
    spots = []

    #TODO remove test data
    #spots = [
    #    {'username': 'A4GOULD', 'time': user_last_heard_timestamp('')},
    #    {'username': 'BKG14', 'time': user_last_heard_timestamp('')},
    #    {'username': 'DRWNICK87', 'time': user_last_heard_timestamp('')}
    #]
    #socketio.emit('spot', spots)

    #TODOjs8call
    # default to spots heard in last 10 minutes
    #timestamp = time.time() - (60 * 10)
    #spots = js8call.get_station_spots(since_timestamp = timestamp)
    if len(spots) > 0:
        heard(spots)

@socketio.on('conversation')
def update_conversations():
    conversations = get_stored_conversations()
    #TODO
    #conversations = [
    #    {'username': 'BKG14', 'time': user_last_heard_timestamp(''), 'unread': True},
    #]
    socketio.emit('conversation', conversations)

@socketio.on('init-chat')
def init_chat():
    active_chat_username = session.get('active_chat_username')
    logged_in_username = session.get('logged_in_username')

    msgs = user_chat_history(active_chat_username, logged_in_username)
    socketio.emit('msg', msgs)
    
@socketio.on('setting')
def update_setting(data):
    global settings
    setting = data['name']
    value = data['value']

    if setting in settings.keys():
        valid, error = validate_setting(setting, value)

        if valid:
            # store new setting value
            settings[setting]['value'] = value
        else:
            # get current setting value
            value = settings[setting]['value']
        
        socketio.emit('setting', {'setting': setting, 'value': value, 'error': error})
            
@socketio.on('get-settings')
def update_setting():
    global settings
    socketio.emit('get-settings', settings)






### helper functions

# directed message callback
def rx_msg(msg):
    msg = process_rx_msg(msg['from'], msg['value'], msg['time'])
    # pass messages for selected chat user to client side
    if 'active_chat_username' in session.keys() and msg['from'] == session.get('active_chat_username'):
        socketio.emit('msg', [msg])

def user_last_heard_timestamp(username):
    #TODO
    #return time.time() - random.randint(0, 60 * 10)

    #TODOjs8call
    spots = []
    #global js8call
    #spots = js8call.get_station_spots(station = username)

    if len(spots) > 0:
        spots.sort(key = lambda spot: spot['time'])
        return spots[-1]
    else:
        return 0

def user_chat_history(user_a, user_b):
    #TODO
    #global db
    #query_data = {'user_a': user_a, 'user_b': user_b}
    # select both sides of the conversation for the given users
    #messages = db.execute('SELECT * FROM messages WHERE (from = :user_a AND to = :user_b) OR (from = :user_b AND to = :user_a)', query_data)
    global message_store

    msgs = []
    #TODO
    users = [user_a, user_b]
    for message in message_store:
        if (
            message['from'] == user_a and message['to'] == user_b or
            message['from'] == user_b and message['to'] == user_a
        ):
            msgs.append(message)
    #for message in messages:
    #    msg = {
    #        'id': message[0],
    #        'from': message[1],
    #        'to': message[2],
    #        'type': message[3],
    #        'time': message[4],
    #        'text': message[5],
    #        'unread': message[6],
    #        'sent': message[7]
    #    }
    #    msgs.append(msg)

    return msgs
    
def get_stored_conversations():
    global message_store
    conversations = {}
    logged_in_username = session.get('logged_in_username')

    for msg in message_store:
        if msg['from'] == logged_in_username:
            username = msg['to']
        elif msg['to'] == logged_in_username:
            username = msg['from']
        else:
            continue
            
        if username in conversations.keys():
            if conversations[username]['unread'] == False:
                conversations[username]['unread'] = msg['unread']
            if msg['time'] > conversations[username]['time']:
                conversations[username]['time'] = msg['time']
                
        else:
            last_heard = user_last_heard_timestamp(username)
            if last_heard == 0:
                last_heard = msg['time']

            conversations[username] = {
                'username': username,
                'time': last_heard,
                'unread': msg['unread']
            }

    print(list(conversations.values()))
    return list(conversations.values())

#TODO
def build_test_msgs(count):
    active_chat_username = session.get('active_chat_username')
    logged_in_username = 'KC3KVT'
    msgs = []
    last_from = logged_in_username

    for i in range(count):
        if last_from == logged_in_username:
            from_user = active_chat_username
        else:
            from_user = logged_in_username;

        last_from = from_user

        if from_user == active_chat_username:
            to_user = logged_in_username
        else:
            to_user = active_chat_username

        if from_user == logged_in_username:
            msg_type = 'tx'
        else:
            msg_type = 'rx'

        if msg_type == 'rx':
            unread = random.choice([True, False])
        else:
            unread = None

        messages = [
            'Hello there neighbor!',
            'Hey there, how are you doing?',
            'Doing good here, how about you?',
            'Doing well, thanks for asking',
            'Hope to see you all soon! Tell everyone there hello.'
        ]

        msg = {
            'id': secrets.token_urlsafe(16),
            'from': from_user,
            'to': to_user,
            'type': msg_type,
            'time': time.time() - random.randint(0, 60 * 60),
            'text': random.choice(messages),
            'unread': unread,
            'sent': None
        }

        msgs.append(msg)

    return msgs

# new spots callback
def heard(spots):
    # only unique spots with the latest timestamp
    heard_data = {}
    for spot in spots:
        if spot['from'] not in heard_data.keys():
            heard_data[spot['from']] = spot['time']
        elif spot['time'] > heard_data[spot['from']]:
            heard_data[spot['from']] = spot['time']

    heard = []
    for username, timestamp in heard_data.items():
        station = {
            'username': username, 
            'time': last_heard_minutes(timestamp)
            }
        heard.append(station)

    socketio.emit('spot', heard)

def process_rx_msg(callsign, text, time):
    #global db
    msg = {
        'id': secrets.token_urlsafe(16),
        'from': callsign,
        'to': session.get('logged_in_username'),
        'type': 'rx',
        'time': time,
        'text': text,
        'unread': True,
        'sent': None
    }
    
    #db.execute('INSERT INTO messages VALUES (:id, :from, :to, :type, :time, :text, :unread, :sent)', msg)
    #db.commit()

    #TODO
    global message_store
    message_store.append(msg)

    return msg

def process_tx_msg(callsign, text, time):
    #global db
    msg = {
        'id': secrets.token_urlsafe(16),
        'from': session.get('logged_in_username'),
        'to': callsign,
        'type': 'tx',
        'time': time,
        'text': text,
        'unread': None,
        #TODO
        'sent': 'Sending...'
        #'sent': None
    }
    
    #db.execute('INSERT INTO messages VALUES (:id, :from, :to, :type, :time, :text, :unread, :sent)', msg)
    #db.commit()

    #TODO
    global message_store
    message_store.append(msg)

    return msg


#TODO migrate to db solution
#TODO improve pyjs8call.TxMonitor to handle msg id's
def tx_complete(text):
    global message_store

    for msg in message_store:
        if msg['sent'] != None and msg['text'].upper() == text.upper():
            socketio.emit('remove-tx-status', msg['id'])



### database functions

def init_db(db):
    table_names = db.execute('SELECT name FROM sqlite_master').fetchall()
    #TODO
    print(table_names)

    if 'settings' not in table_names:
        db.execute('CREATE TABLE settings(name, value)')
        #TODO initialize settings

    if 'messages' not in table_names:
        db.execute('CREATE TABLE messages(id, from, to, type, time, text, unread, sent)')
    
    if 'spots' not in table_names:
        db.execute('CREATE TABLE spots(callsign, time)')


def validate_callsign(callsign):
    error = None
    valid = False

    if any([char.isdigit() for char in callsign]):
        valid = True
    else:
        valid = False
        error = 'Callsign must contain at least one digit [0-9]'

    if len(callsign) <=9:
        if valid:
            valid = True
    else:
        valid = False
        if error == None:
            error = 'Callsign max length is 9 characters'
        else:
            error += ', and have a max length of 9 characters'

    return (valid, error)

def validate_grid(grid):
    error = None
    valid = False

    if len(grid) == 4:
        valid = True
    else:
        valid = False
        error = 'Grid square length must be 4 characters'
        return (valid, error)

    if grid[0].isalpha() and grid[1].isalpha() and grid[2].isdigit() and grid[3].isdigit():
        if valid:
            valid = True
    else:
        valid = False
        if error == None:
            error = 'Grid square format must be AB12'
        else:
            error += ', and formatted as AB12'

    return (valid, error)

def validate_aging(aging):
    error = None
    valid = False

    if aging.isnumeric():
        valid = True
    else:
        valid = False
        error = 'Activity Aging must be a number'

    return (valid, error)


def validate_setting(setting, value):
    global settings
    error = None
    valid = False

    if setting not in settings:
        error = 'Invalid setting'
        return (valid, error)

    if settings[setting]['validate'] == None:
        if settings[setting]['options'] != None and value in settings[setting]['options']:
            valid = True
        else:
            valid = False
            error = 'Invalid ' + setting
    else:
        valid, error = settings[setting]['validate'](value)

    return (valid, error)


settings = {
    'callsign': {
        'value': '',
        'label': 'Callsign',
        'validate': validate_callsign,
        'default': '',
        'required': True,
        'options': None
    },
    'grid': {
        'value': '',
        'label': 'Grid Square',
        'validate': validate_grid,
        'default': '',
        'required': False,
        'options': None
    },
    'speed': {
        'value': 'fast',
        'label': 'JS8Call Speed',
        'validate': None,
        'default': 'fast',
        'required': False,
        'options': ['slow', 'normal', 'fast', 'turbo']
    },
    # activity/spot aging in minutes
    'aging': {
        'value': '10', 
        'label': 'Aging (minutes)',
        'validate': validate_aging, 
        'default': '10',
        'required': False,
        'options': None
    },
    'theme': {
        'value': 'light', 
        'label': 'App Theme',
        'validate': None, 
        'default': 'light',
        'required': False,
        'options': ['light', 'dark']
    },
    'size': {
        'value': 'normal', 
        'label': 'Font Size',
        'validate': None, 
        'default': 'normal',
        'required': False,
        'options': ['small', 'normal', 'large']
    },
    'tab': {
        'value': 'activity', 
        'label': 'Default Tab',
        'validate': None, 
        'default': 'activity',
        'required': False,
        'options': ['activity', 'conversations']
    }
}


#TODO global js8call doesn't work either
message_store = []
js8call = pyjs8call.Client()

if __name__ == 'main':
    # initialize socket io
    socketio.run(app, debug=True)
    #TODO temp msg storage

    #TODOjs8call
    # initialize js8call client
    #global js8call
    #if 'Portal' not in js8call.config.get_profile_list():
    #    js8call.config.create_new_profile('Portal')

    #js8call.set_config_profile('Portal')
    #js8call.register_rx_callback(rx_msg, pyjs8call.Message.RX_DIRECTED)
    #js8call.start()
    #TODO use channel DIG-40: 7055000
    #js8call.set_freq(7078000)
    #js8call.tx_monitor.tx_complete_callback(tx_complete)

    # initialize database
    #db_con = sqlite3.connect('portal.db', detect_types=sqlite3.PARSE_DECLTYPES)
    #sqlite3.register_adapter(bool, int)
    #sqlite3.register_converter('BOOLEAN', lambda v: v != '0')
    #db = db_con.cursor()
    #init_db(db)

