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

#TODO get rid of global variable
active_chat_username = None
logged_in_username = None


#TODO add ability to restore defaults, button in settings.html footer


### flask routes and template handling

@app.route('/')
@app.route('/stations', methods=['GET', 'POST'])
@app.route('/stations.html', methods=['GET', 'POST'])
def stations_route():
    global active_chat_username
    settings = get_settings()
    session['logged_in_username'] = settings['callsign']['value']
    
    if request.method == 'POST':
        active_chat_username = request.form.get('user')
        return ''
    else:
        if settings['callsign']['value'] == '':
            return redirect('/settings')

        active_chat_username = None
        return render_template('stations.html', settings = settings)

@app.route('/chat')
@app.route('/chat.html')
def chat_route():
    global active_chat_username
    settings = get_settings()

    mark_user_msgs_read(active_chat_username)

    return render_template('chat.html', user = active_chat_username, settings = settings)

@app.route('/settings', methods=['GET', 'POST'])
@app.route('/settings.html', methods=['GET', 'POST'])
def settings_route():
    settings = get_settings()

    if request.method == 'POST':
        # process posted settings
        for setting, value in request.form.items():
            if setting == 'callsign' or setting == 'grid':
                value = value.upper()

            print(setting)

            if setting in settings.keys() and value != settings[setting]['value']:
                valid, error = set_setting(setting, value)
                settings[setting]['error'] = error

                if valid:
                    settings[setting]['value'] = value

                print(setting, value, valid, error)

    return render_template('settings.html', settings = settings)



### socket.io functions

@socketio.on('msg')
def tx_msg(data):
    global js8call
    msg = process_tx_msg(data['user'], data['text'].upper(), time.time())

    js8call.send_directed_message(msg['to'], msg['text'])
    js8call.tx_monitor.monitor(msg['text'], identifier = msg['id'])
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
    global js8call
    spots = []

    # default to spots heard in last 10 minutes
    timestamp = time.time() - (60 * 10)
    spots = js8call.get_station_spots(since_timestamp = timestamp)
    if len(spots) > 0:
        heard(spots)

@socketio.on('conversation')
def update_conversations():
    conversations = get_stored_conversations()
    socketio.emit('conversation', conversations)

@socketio.on('init-chat')
def init_chat():
    global active_chat_username
    logged_in_username = get_setting('callsign')

    msgs = user_chat_history(active_chat_username, logged_in_username)
    socketio.emit('msg', msgs)
    
@socketio.on('get-settings')
def update_setting():
    settings = query('SELECT setting, value FROM settings').fetchall()
    settings = dict(settings)
    socketio.emit('get-settings', settings)

@socketio.on('power-on')
def power_on():
    global js8call

    # wait for current transactions to finish
    time.sleep(0.1)
    # start js8call
    if not js8call.online:
        js8call.start()

    socketio.emit('power-on')

@socketio.on('power-off')
def power_off():
    global js8call

    # wait for current transactions to finish
    time.sleep(0.1)
    # stop js8call
    js8call.stop()

    socketio.emit('power-off')



### helper functions

# directed message callback
# because this function is called via callback it does not automatically have the flask request context
def rx_msg(msg):
    global active_chat_username
    msg = process_rx_msg(msg['from'], msg['text'], msg['time'])

    # pass messages for selected chat user to client side
    if msg['from'] == active_chat_username:
        socketio.emit('msg', [msg])

    unread = bool(user_unread_count(msg['from']))

    # pass conversation to client side
    conversation = {
        'username': msg['from'], 
        'time': msg['time'],
        'unread': unread
    }

    socketio.emit('conversation', [conversation])

def mark_user_msgs_read(username):
    query('UPDATE messages SET unread = 0 WHERE "from" = :user', {'user': username})

def user_unread_count(username):
    unread = query('SELECT COUNT(*) FROM messages WHERE "from" = :user AND unread = 1', {'user': username}).fetchone()
    return int(unread[0])

def user_last_heard_timestamp(username):
    # get latest spot timestamp
    global js8call
    spots = js8call.get_station_spots(station = username)
    last_spot_timestamp = None
    last_msg_timestamp = None

    if spots != None and len(spots) > 0:
        spots.sort(key = lambda spot: spot['time'])
        last_spot_timestamp = spots[-1]['time']

    # get latest msg timestamp
    last_msg_timestamp = query('SELECT MAX(time) FROM messages WHERE "from" = :user', {'user': username}).fetchone()

    if last_msg_timestamp != None and len(last_msg_timestamp) > 0:
        last_msg_timestamp = last_msg_timestamp[0]

    if last_spot_timestamp == None:
        last_spot_timestamp = 0

    if last_msg_timestamp == None:
        last_msg_timestamp = 0

    # return the greater of the two timestamps
    return max(last_spot_timestamp, last_msg_timestamp)

def user_chat_history(user_a, user_b):
    users = {'user_a': user_a, 'user_b': user_b}
    # select both sides of the conversation for the given users
    columns = ['id', 'from', 'to', 'type', 'time', 'text', 'unread', 'sent']
    msgs = query('SELECT * FROM messages WHERE ("from" = :user_a AND "to" = :user_b) OR ("from" = :user_b AND "to" = :user_a)', users).fetchall()
    msgs = [dict(zip(columns, msg)) for msg in msgs]
    return msgs
    
def get_stored_conversations():
    conversations = []
    logged_in_username = get_setting('callsign')

    users = query('SELECT DISTINCT "from", "to" FROM messages WHERE "from" = :user OR "to" = :user', {'user': logged_in_username}).fetchall()

    # if there are no messages to process, end processing
    if users == None or len(users) == 0:
        return []
        
    # parse result row tuples into single list of unique values
    users = list(set([user for x in users for user in (x[0], x[1])]))
    users.remove(logged_in_username)

    for user in users:
        unread = user_unread_count(user)
        last_heard = user_last_heard_timestamp(user)

        conversation = {
            'username': user,
            'time': last_heard,
            'unread': bool(unread)
        }

        conversations.append(conversation)

    return conversations

def get_settings():
    columns = ['setting', 'value', 'label', 'default', 'required', 'options']
    settings = query('SELECT * FROM settings').fetchall()
    settings = [dict(zip(columns, setting)) for setting in settings]
    
    if len(settings) > 0:
        settings = {setting['setting']: setting for setting in settings}

        for setting in settings.keys():
            if settings[setting]['options'] != None:
                settings[setting]['options'] = json.loads(settings[setting]['options'])
    else:
        settings = {}

    return settings

def get_setting(setting):
    setting = query('SELECT value FROM settings WHERE setting = :setting', {'setting': setting}).fetchone()
    return setting[0]

def set_setting(setting, value):
    valid, error = validate_setting(setting, value)

    if valid:
        # store new setting value
        query('UPDATE settings SET value = :value WHERE setting = :setting', {'setting': setting, 'value': value})

        # handle settings affecting js8call
        if setting == 'callsign':
            js8call.set_station_callsign(value)
        elif setting == 'speed':
            js8call.set_speed(value)
        elif setting == 'grid':
            js8call.set_station_grid(value)
        elif setting == 'freq':
            js8call.set_freq(value)

    return (valid, error)

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
            'time': timestamp
        }
        heard.append(station)

    socketio.emit('spot', heard)

# because this function is called via callback it does not automatically have the flask request context
def process_rx_msg(callsign, text, time):
    global active_chat_username
    logged_in_username = get_setting('callsign')

    if callsign == active_chat_username:
        unread = False
    else:
        unread = True

    msg = {
        'id': secrets.token_urlsafe(16),
        'from': callsign,
        'to': logged_in_username,
        'type': 'rx',
        'time': time,
        'text': text,
        'unread': unread,
        'sent': None
    }
    
    if logged_in_username != '':
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
        'unread': False,
        'sent': 'Sending...'
    }
    
    query('INSERT INTO messages VALUES (:id, :from, :to, :type, :time, :text, :unread, :sent)', msg)

    return msg

def tx_complete(identifier):
    # works inconsistently without this delay, root cause unknown
    time.sleep(0.001)
    query('UPDATE messages SET sent = NULL WHERE id = :id', {'id': identifier})
    socketio.emit('remove-tx-status', identifier)

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
        error = 'Activity aging must be a number'

    return (valid, error)

def validate_freq(freq):
    error = None
    valid = False

    if freq.isnumeric():
        valid = True
    else:
        valid = False
        error = 'Frequency must be a number'

    return (valid, error)

def validate_setting(setting, value):
    settings = get_settings()
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
    elif setting == 'freq':
        valid, error = validate_freq(value)
    else:
        if settings[setting]['options'] != None and value in settings[setting]['options']:
            valid = True
        else:
            valid = False
            error = 'Invalid ' + setting

    return (valid, error)

def init_settings():
    global js8call
    settings = get_settings()

    js8call.set_station_callsign(settings['callsign']['value'])
    js8call.set_speed(settings['speed']['value'])
    js8call.set_station_grid(settings['grid']['value'])
    js8call.set_freq(int(settings['freq']['value']))




### database functions

def init_db():
    with sqlite3.connect('portal.db', detect_types=sqlite3.PARSE_DECLTYPES) as con:
        sqlite3.register_adapter(bool, int)
        sqlite3.register_converter('BOOLEAN', lambda v: v != '0')
        cur = con.cursor()

        tables = cur.execute('SELECT name FROM sqlite_master').fetchall()
        tables = [tables[i][0] for i in range(len(tables))]

        if 'messages' not in tables:
            cur.execute('CREATE TABLE messages(id, "from", "to", type, time, text, unread, sent)')
        if 'spots' not in tables:
            cur.execute('CREATE TABLE spots(callsign, time)')
        if 'settings' not in tables:
            cur.execute('CREATE TABLE settings(setting, value, label, "default", required, options)')
        
        settings = get_settings()
        global default_settings

        for setting, data in default_settings.items():
            if setting not in settings.keys():
                data['setting'] = setting

                if isinstance(data['options'], list):
                    data['options'] = json.dumps(data['options'])

                cur.execute('INSERT INTO settings VALUES (:setting, :value, :label, :default, :required, :options)', data)

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



default_settings = {
    'callsign': {
        'value': '',
        'label': 'Callsign',
        'default': '',
        'required': True,
        'options': None
    },
    'freq': {
        'value': '7078000', 
        'label': 'Frequency (Hz)',
        'default': '7078000',
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
    'theme': {
        'value': 'light', 
        'label': 'App Theme',
        'default': 'light',
        'required': False,
        'options': ['light', 'dark']
    },
    'tab': {
        'value': 'activity', 
        'label': 'Default Tab',
        'default': 'activity',
        'required': False,
        'options': ['activity', 'messages']
    },
    'size': {
        'value': 'normal', 
        'label': 'Font Size',
        'default': 'normal',
        'required': False,
        'options': ['normal', 'large']
    },
    # activity/spot aging in minutes
    'aging': {
        'value': '10', 
        'label': 'Aging (minutes)',
        'default': '10',
        'required': True,
        'options': None
    }
}


### initialize database ###
init_db()
settings = get_settings()

### initialize application ###
# running headless requires xvfb to be installed
js8call = pyjs8call.Client(headless = True)
atexit.register(js8call.stop)

if 'Portal' not in js8call.config.get_profile_list():
    js8call.config.create_new_profile('Portal')

js8call.set_config_profile('Portal')
# set max idle timeout (1440 minutes, 24 hours)
js8call.config.set('Configuration', 'TxIdleWatchdog', 1440)
# enable autoreply which allows API message tx 
js8call.config.set('Configuration', 'AutoreplyConfirmation', 'true')
js8call.config.set('Configuration', 'AutoreplyOnAtStartup', 'true')

js8call.config.set('Configuration', 'Miles', 'true')
# not critical to set freq here, but js8call will use this on restart
js8call.config.set('Common', 'DialFreq', int(settings['freq']['value']))

# allow initial startup with no callsign set
if settings['callsign']['value'] != '':
    js8call.set_station_callsign(settings['callsign']['value'])

js8call.start()

js8call.set_speed(settings['speed']['value'])
js8call.set_station_grid(settings['grid']['value'])
js8call.set_freq(int(settings['freq']['value']))
js8call.register_rx_callback(rx_msg, pyjs8call.Message.RX_DIRECTED)
js8call.tx_monitor.set_tx_complete_callback(tx_complete)
js8call.spot_monitor.set_new_spot_callback(heard)




if __name__ == 'main':
    socketio.run(app, debug=True)

