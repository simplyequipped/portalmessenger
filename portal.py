import json
import os
import argparse
import subprocess
import time
import sqlite3
import secrets

import portal

from flask import Flask, render_template, request, session, redirect
from flask_socketio import SocketIO

app = Flask(__name__)
app.secret_key = secrets.token_hex()
socketio = SocketIO(app)



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
    global modem
    db_settings = settings.db_settings()
    local_ip = settings.get('ip')

    if request.method == 'POST':
        restart = False

        # process posted settings
        for setting, value in request.form.items():
            if setting == 'callsign' or setting == 'grid':
                value = value.upper()

            if setting in db_settings.keys() and value != db_settings[setting]['value']:
                valid, error = settings.set(setting, value)
                db_settings[setting]['error'] = error

                if valid:
                    db_settings[setting]['value'] = value

                    if modem.name.lower() == 'js8call':
                        # update settings in js8call
                        if setting == 'callsign':
                            modem.js8call.settings.set_station_callsign(value)
                            restart = True
                        elif setting == 'speed':
                            modem.js8call.settings.set_speed(value)
                            restart = True
                        elif setting == 'grid':
                            modem.js8call.settings.set_station_grid(value)
                        elif setting == 'freq':
                            modem.js8call.settings.set_freq(value)

                    elif modem.name.lower() == 'demo':
                        if setting == 'callsign':
                            modem.callsign = value

        if modem.name.lower() == 'js8call' and restart:
            #TODO is this the right place to restart? should client side drive this?
            modem.restart()

    return render_template('settings.html', settings = db_settings, ip = local_ip)



### socket.io functions

@socketio.on('msg')
def tx_msg(data):
    global modem

    msg = process_msg( modem.send(data['user'], data['text']) )
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

    # spots since aging setting
    age = 60 * int(settings.get('aging')) # convert minutes to seconds
    spots = modem.get_spots(age = age)

    if len(spots) > 0:
        spots = [{'username': spot.origin, 'time': spot.timestamp} for spot in spots]
        socketio.emit('spot', spots)

    #TODO test, no longer needed?
    #if len(spots) > 0:
    #    heard(spots)

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
    if not modem.online():
        # returns once application is started
        modem.start()

    socketio.emit('power-on')

@socketio.on('power-off')
def power_off():
    global modem

    # wait for current transactions to finish
    time.sleep(0.1)
    modem.stop()

    socketio.emit('power-off')

@socketio.on('power-restart')
def power_restart():
    global modem

    # wait for current transactions to finish
    time.sleep(0.1)
    socketio.emit('power-off')
    # returns once application restarts
    modem.restart()
    socketio.emit('power-on')



### helper functions

# directed message callback
# because this function is called via callback it does not automatically have the flask request context
def incoming_msg(msg):
    global settings
    active_chat_username = settings.get('active_chat_username')
    msg = process_msg(msg)

    # pass messages for active chat user to client side
    if msg['origin'] == active_chat_username:
        socketio.emit('msg', [msg])

    unread = bool(user_unread_count(msg['origin']))

    # pass conversation to client side
    conversation = {
        'username': msg['origin'], 
        'time': msg['time'],
        'unread': unread
    }

    socketio.emit('conversation', [conversation])

def mark_user_msgs_read(username):
    query('UPDATE messages SET unread = 0 WHERE origin = :user', {'user': username})

def user_unread_count(username):
    unread = query('SELECT COUNT(*) FROM messages WHERE origin = :user AND unread = 1', {'user': username}).fetchone()
    return int(unread[0])

def user_last_heard_timestamp(username):
    # get latest spot timestamp
    global modem

    # get user spots
    spots = modem.get_spots(origin = username)

    if spots is not None and len(spots) > 0:
        last_spot_timestamp = spots[-1].timestamp
    else:
        last_spot_timestamp = 0

    # get latest msg timestamp
    last_msg_timestamp = query('SELECT MAX(time) FROM messages WHERE origin = :user', {'user': username}).fetchone()

    if last_msg_timestamp not in [None, (None,)] and len(last_msg_timestamp) > 0:
        last_msg_timestamp = last_msg_timestamp[0]
    else:
        last_msg_timestamp = 0

    # return the greater of the two timestamps
    return max(last_spot_timestamp, last_msg_timestamp)

def user_chat_history(user_a, user_b):
    users = {'user_a': user_a, 'user_b': user_b}
    # select both sides of the conversation for the given users
    columns = ['id', 'origin', 'destination', 'type', 'time', 'text', 'unread', 'status']
    msgs = query('SELECT * FROM messages WHERE (origin = :user_a AND destination = :user_b) OR (origin = :user_b AND destination = :user_a)', users).fetchall()
    msgs = [dict(zip(columns, msg)) for msg in msgs]
    return msgs
    
def get_stored_conversations():
    global settings
    conversations = []
    logged_in_username = settings.get('callsign')

    users = query('SELECT DISTINCT origin, destination FROM messages WHERE origin = :user OR destination = :user', {'user': logged_in_username}).fetchall()

    # if there are no messages to process, end processing
    if users is None or len(users) == 0:
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

def new_spots(spots):
    spots = [{'username': spot.origin, 'time': spot.timestamp} for spot in spots]
    socketio.emit('spot', spots)

def process_msg(msg):
    global settings

    #TODO remove this and use msg.text normally after pyjs8call 0.2.1 release
    if msg.text is None:
        msg.set('text', msg.value)

    msg = {
        'id': msg.id,
        'origin': msg.origin,
        'destination': msg.destination,
        'type': msg.type[0:2].lower(), # RX.DIRECTED = 'rx', TX.SEND_MESSAGE = 'tx'
        'time': msg.timestamp,
        'text': msg.text,
        'unread': False,
        'status': None
        }

    if msg['type'] == 'rx' and msg['origin'] != settings.get('active_chat_username'):
        msg['unread'] = True

    if msg['type'] == 'tx':
        msg['origin'] = settings.get('callsign')
        msg['status'] = 'queued'
    
    query('INSERT INTO messages VALUES (:id, :origin, :destination, :type, :time, :text, :unread, :status)', msg)

    return msg

def outgoing_status(msg):
    #TODO works inconsistently without this delay, root cause unknown
    time.sleep(0.001)
    query('UPDATE messages SET status = :status WHERE id = :id', {'id': msg.id, 'status': msg.status})
    socketio.emit('update-tx-status', {'id': msg.id, 'status': msg.status})



### database functions

def init_db():
        tables = query('SELECT name FROM sqlite_master').fetchall()
        tables = [tables[i][0] for i in range(len(tables))]

        if 'messages' not in tables:
            query('CREATE TABLE messages(id, origin, destination, type, time, text, unread, status)')
        
def query(query, parameters=None):
    global settings

    with sqlite3.connect(settings.get('db_file'), detect_types=sqlite3.PARSE_DECLTYPES) as con:
        sqlite3.register_adapter(bool, int)
        sqlite3.register_converter('BOOLEAN', lambda v: v != '0')
        db = con.cursor()

        if parameters is None:
            result = db.execute(query)
        else:
            result = db.execute(query, parameters)

        con.commit()

    return result



### parse args ###
#parser = argparse.ArgumentParser()
#parser.add_argument('--headless', action='store_true', help='show or hide the JS8Ccall app using xvfb')
#parser.add_argument('-d', '--demo', action='store_true', help='run without requiring a modem app to be installed')
#parser.add_argument('--app')
#parser.add_argument('run')
#TODO parser.add_argument('-i', '--incognito', action='store_true', help='use sqlite in memory only, no data is stored after exit')
#args = parser.parse_args()

### initialize settings ###
db_file = 'portal.db'
settings = portal.Settings(db_file)
#settings.set('headless', args.headless)
settings.set('headless', True)

# get local IP address
try:
    devnull = open(os.devnull, 'w')
    local_ip = subprocess.check_output(['hostname', '-I'], stderr = devnull).decode('utf-8').split(' ')[0]
except (FileNotFoundError, subprocess.CalledProcessError):
    local_ip = 'IP unavailable'

settings.set('ip', local_ip)

### initialize database ###
init_db()

### initialize modem ###
#if args.demo:
#    modem = 'DemoModem'
#else:
modem = settings.get('modem')

#TODO force demo modem
#modem = 'DemoModem'

if modem == 'JS8Call':
    from portal.modem.js8callmodem import JS8CallModem

    modem = JS8CallModem(settings.get('callsign'), headless=settings.get('headless'))
    # initialize config settings before start
    modem.js8call.settings.set_speed(settings.get('speed'))
    # set callback functions
    modem.incoming = incoming_msg
    modem.spots = new_spots
    modem.outgoing = outgoing_status

    modem.start()

    # initialize settings with running application
    modem.js8call.settings.set_station_grid(settings.get('grid'))
    modem.js8call.settings.set_freq(int(settings.get('freq')))

elif modem == 'FSKModem':
    pass

elif modem == 'DemoModem':
    from portal.modem.demomodem import DemoModem
    
    modem = DemoModem(settings.get('callsign'))
    # set callback functions
    modem.incoming = incoming_msg
    modem.spots = new_spots
    modem.outgoing = outgoing_status


    
if __name__ == 'main':
    app.run(host='0.0.0.0')
    socketio.run(app, debug=True)
