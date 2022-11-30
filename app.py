import json
import secrets
import subprocess
import time
import sqlite3

import portal
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
    global settings
    db_settings = settings.db_settings()
    
    if request.method == 'POST':
        settings.set('active_chat_username', request.form.get('user'))
        return ''
    else:
        if db_settings['callsign']['value'] == '':
            return redirect('/settings')

        settings.set('active_chat_username', None)
        return render_template('stations.html', settings = db_settings)

@app.route('/chat')
@app.route('/chat.html')
def chat_route():
    global settings
    db_settings = settings.db_settings()
    active_chat_username = settings.get('active_chat_username')

    mark_user_msgs_read(active_chat_username)

    return render_template('chat.html', user = active_chat_username, settings = db_settings)

@app.route('/settings', methods=['GET', 'POST'])
@app.route('/settings.html', methods=['GET', 'POST'])
def settings_route():
    global settings
    db_settings = settings.db_settings()
    local_ip = settings.get('ip')

    if request.method == 'POST':
        # process posted settings
        for setting, value in request.form.items():
            if setting == 'callsign' or setting == 'grid':
                value = value.upper()

            if setting in db_settings.keys() and value != db_settings[setting]['value']:
                valid, error = settings.set(setting, value)
                db_settings[setting]['error'] = error

                if valid:
                    db_settings[setting]['value'] = value

    return render_template('settings.html', settings = db_settings, ip = local_ip)



### socket.io functions

@socketio.on('msg')
def tx_msg(data):
    global modem
    msg = process_tx_msg(data['user'], data['text'].upper(), time.time())

    modem.tx(msg['to'], msg['text'])
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
    global modem
    global settings
    spots = []

    # spots since aging setting (minutes)
    aging = int(settings.get('aging')
    timestamp = time.time() - (60 * aging)
    spots = modem.spots(since_timestamp = timestamp)

    if len(spots) > 0:
        heard(spots)

@socketio.on('conversation')
def update_conversations():
    conversations = get_stored_conversations()
    socketio.emit('conversation', conversations)

@socketio.on('init-chat')
def init_chat():
    global settings
    active_chat_username = settings.get('active_chat_username')
    logged_in_username = settings.get('callsign')

    msgs = user_chat_history(active_chat_username, logged_in_username)
    socketio.emit('msg', msgs)
    
@socketio.on('get-settings')
def update_setting():
    global settings
    socketio.emit('get-settings', settings.settings())

@socketio.on('power-on')
def power_on():
    global modem

    # wait for current transactions to finish
    time.sleep(0.1)
    if not modem.online:
        modem.start()

    socketio.emit('power-on')

@socketio.on('power-off')
def power_off():
    global modem

    # wait for current transactions to finish
    time.sleep(0.1)
    modem.stop()

    socketio.emit('power-off')



### helper functions

# directed message callback
# because this function is called via callback it does not automatically have the flask request context
def rx_msg(msg):
    global settings
    active_chat_username = settings.get('active_chat_username')
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
    global modem
    spots = modem.spots(station = username)
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

# new spots callback
def heard(spots):
    heard = []
    for spot in spots:
        station = {
            'username': spot['from'], 
            'time': spot['time']
        }
        heard.append(station)

    socketio.emit('spot', heard)

# because this function is called via callback it does not automatically have the flask request context
def process_rx_msg(callsign, text, time):
    global settings
    active_chat_username = settings.get('active_chat_username')
    logged_in_username = settings.get('callsign')

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
    global settings

    msg = {
        'id': secrets.token_urlsafe(16),
        'from': settings.get('logged_in_username'),
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



### database functions

def init_db():
        tables = query('SELECT name FROM sqlite_master').fetchall()
        tables = [tables[i][0] for i in range(len(tables))]

        if 'messages' not in tables:
            query('CREATE TABLE messages(id, "from", "to", type, time, text, unread, sent)')
        if 'spots' not in tables:
            query('CREATE TABLE spots(callsign, time)')
        
def query(query, parameters=None):
    global settings

    with sqlite3.connect(settings.get('db_file'), detect_types=sqlite3.PARSE_DECLTYPES) as con:
        sqlite3.register_adapter(bool, int)
        sqlite3.register_converter('BOOLEAN', lambda v: v != '0')
        db = con.cursor()

        if parameters == None:
            result = db.execute(query)
        else:
            result = db.execute(query, parameters)

        con.commit()

    return result



### initialize database ###
init_db()


### initialize settings ###
db_file = 'portal.db'
settings = portal.Settings(db_file)

local_ip = subprocess.check_output(['hostname', '-I']).decode('utf-8').split(' ')[0]
settings.set('ip', local_ip)
# running headless requires xvfb to be installed
settings.set('headless', True)


### initialize modem ###
modem = settings.get('modem')

if modem == 'JS8Call':
    callsign = settings.get('callsign')
    headless = settings.get('headless')
    freq = settings.get('freq')

    modem = portal.JS8CallModem(callsign, freq = freq, headless = headless)
    modem.start()

    modem.js8call.set_speed(settings['speed']['value'])
    modem.js8call.set_station_grid(settings['grid']['value'])
    modem.js8call.set_freq(int(settings['freq']['value']))

    modem.set_rx_callback(rx_msg)
    modem.set_spot_callback(heard)
    modem.set_tx_complete_callback(tx_complete)

elif modem == 'FSKModem':
    pass



if __name__ == 'main':
    socketio.run(app, debug=True)

