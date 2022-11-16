import json
import secrets
import random
import time
import sqlite3
import atexit

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
def stations_route():
    settings = get_settings()
    session['logged_in_username'] = settings['callsign']['value']
    
    if request.method == 'POST':
        session['active_chat_username'] = request.form.get('user')
        return ''
    else:
        if settings['callsign']['value'] == '':
            return redirect('/settings')

        if 'active_chat_username' in session.keys():
            del session['active_chat_username']

        return render_template('stations.html', settings = settings)

@app.route('/chat')
@app.route('/chat.html')
def chat_route():
    settings = get_settings()
    username = session.get('active_chat_username')
    return render_template('chat.html', user = username, settings = settings)

@app.route('/settings', methods=['GET', 'POST'])
@app.route('/settings.html', methods=['GET', 'POST'])
def settings_route():
    settings = get_settings()

    if request.method == 'POST':
        # process posted settings
        for setting, value in request.form.items():
            if setting in settings.keys() and value != settings[setting]['value']:
                valid, error = validate_setting(setting, value, settings)

                if valid:
                    # store new setting value
                    query('UPDATE settings SET value = :value WHERE setting = :setting', {'setting': setting, 'value': value})
                    settings[setting]['value'] = value

                    #TODOjs8call
                    # handle settings affecting js8call modem
                    #if setting == 'callsign':
                    #    js8call.set_station_callsign(value)
                    #if setting == 'speed':
                    #    js8call.set_speed(value)
                    #if setting == 'grid':
                    #    js8call.set_station_grid(value)

    return render_template('settings.html', settings = settings)




### socket.io functions

@socketio.on('msg')
def tx_msg(data):
    #TODOjs8call
    #global js8call
    msg = process_tx_msg(data['user'], data['text'], time.time())
    #TODOjs8call
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
    settings = query('SELECT setting, value FROM settings').fetchall()
    settings = dict(settings)
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
    users = {'user_a': user_a, 'user_b': user_b}
    # select both sides of the conversation for the given users
    columns = ['id', 'from', 'to', 'type', 'time', 'text', 'unread', 'sent']
    msgs = query('SELECT * FROM messages WHERE ("from" = :user_a AND "to" = :user_b) OR ("from" = :user_b AND "to" = :user_a)', users).fetchall()
    msgs = [dict(zip(columns, msg)) for msg in msgs]
    return msgs
    
def get_stored_conversations():
    conversations = {}
    logged_in_username = session.get('logged_in_username')

    columns = ['id', 'from', 'to', 'type', 'time', 'text', 'unread', 'sent']
    msgs = query('SELECT * FROM messages WHERE "from" = :user OR "to" = :user', {'user': logged_in_username}).fetchall()
    msgs = [dict(zip(columns, msg)) for msg in msgs]

    for msg in msgs:
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
            # no spots but msg is from user, use msg timestamp
            if last_heard == 0 and msg['from'] == username:
                last_heard = msg['time']

            conversations[username] = {
                'username': username,
                'time': last_heard,
                'unread': msg['unread']
            }

    return list(conversations.values())

def get_settings():
    columns = ['setting', 'value', 'label', 'default', 'required', 'options']
    settings = query('SELECT * FROM settings').fetchall()
    settings = [dict(zip(columns, setting)) for setting in settings]
    settings = {setting['setting']: setting for setting in settings}

    for setting in settings.keys():
        if settings[setting]['options'] != None:
            settings[setting]['options'] = json.loads(settings[setting]['options'])

    return settings

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
    
    query('INSERT INTO messages VALUES (:id, :from, :to, :type, :time, :text, :unread, :sent)', msg)

    return msg

def process_tx_msg(callsign, text, time):
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
    
    query('INSERT INTO messages VALUES (:id, :from, :to, :type, :time, :text, :unread, :sent)', msg)

    return msg

#TODO handle uppercase text returned from pyjs8call.TxMonitor
#TODO handle multiple messages with the same text
#TODO improve pyjs8call.TxMonitor to handle msg id's
def tx_complete(text):

    msg = query('SELECT id FROM messages WHERE sent != NULL AND text = :text', {'text': text}).fetchone()
    socketio.emit('remove-tx-status', msg[0])

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

def validate_setting(setting, value, settings):
    error = None
    valid = False

    if setting not in settings:
        error = 'Invalid setting'
        return (valid, error)

    if setting == 'callsign':
        valid, error = validate_callsign(value)
    elif setting == 'grid':
        valid, error = validate_grid(value)
    elif setting == 'aging':
        valid, error = validate_aging(value)
    else:
        if settings[setting]['options'] != None and value in settings[setting]['options']:
            valid = True
        else:
            valid = False
            error = 'Invalid ' + setting

    return (valid, error)





### database functions

def init_db():
    with sqlite3.connect('portal.db', detect_types=sqlite3.PARSE_DECLTYPES) as con:
        sqlite3.register_adapter(bool, int)
        sqlite3.register_converter('BOOLEAN', lambda v: v != '0')
        cur = con.cursor()

        tables = cur.execute('SELECT name FROM sqlite_master').fetchall()
        tables = [tables[i][0] for i in range(len(tables))]

        if 'settings' not in tables:
            cur.execute('CREATE TABLE settings(setting, value, label, "default", required, options)')
            global default_settings

            for setting, data in default_settings.items():
                data['setting'] = setting

                if isinstance(data['options'], list):
                    data['options'] = json.dumps(data['options'])

                cur.execute('INSERT INTO settings VALUES (:setting, :value, :label, :default, :required, :options)', data)

        if 'messages' not in tables:
            cur.execute('CREATE TABLE messages(id, "from", "to", type, time, text, unread, sent)')
    
        if 'spots' not in tables:
            cur.execute('CREATE TABLE spots(callsign, time)')
    
        con.commit()

def query(query, parameters=None):
    with sqlite3.connect('portal.db', detect_types=sqlite3.PARSE_DECLTYPES) as con:
        sqlite3.register_adapter(bool, int)
        sqlite3.register_converter('BOOLEAN', lambda v: v != '0')
        db = con.cursor()

        if parameters == None:
            result = db.execute(query)
        else:
            result = db.execute(query, parameters)

        con.commit()

    return result

    






### initialize application ###

js8call = pyjs8call.Client()

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



default_settings = {
    'callsign': {
        'value': '',
        'label': 'Callsign',
        'default': '',
        'required': True,
        'options': None
    },
    'grid': {
        'value': '',
        'label': 'Grid Square',
        'default': '',
        'required': False,
        'options': None
    },
    'speed': {
        'value': 'fast',
        'label': 'JS8Call Speed',
        'default': 'fast',
        'required': False,
        'options': ['slow', 'normal', 'fast', 'turbo']
    },
    # activity/spot aging in minutes
    'aging': {
        'value': '10', 
        'label': 'Aging (minutes)',
        'default': '10',
        'required': False,
        'options': None
    },
    'theme': {
        'value': 'light', 
        'label': 'App Theme',
        'default': 'light',
        'required': False,
        'options': ['light', 'dark']
    },
    'size': {
        'value': 'normal', 
        'label': 'Font Size',
        'default': 'normal',
        'required': False,
        'options': ['normal', 'large']
    },
    'tab': {
        'value': 'activity', 
        'label': 'Default Tab',
        'default': 'activity',
        'required': False,
        'options': ['activity', 'messages']
    }
}


# initialize database
init_db()


if __name__ == 'main':
    # initialize socket io
    socketio.run(app, debug=True)

