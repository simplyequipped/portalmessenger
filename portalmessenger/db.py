import json
import sqlite3

from flask import current_app, g

from portalmessenger.settings import settings


#breakpoint()

#TODO
# commit on db inserts
   

### general db

def get_db():
    if 'db' not in g:
        sqlite3.register_adapter(bool, int)
        sqlite3.register_converter('BOOLEAN', lambda v: v != '0')
        
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db

def init_db():
    with current_app.open_resource('schema.sql') as f:
        get_db().executescript( f.read().decode('utf8') )

    # skip init default settings if settings already exist
    #if len( get_settings() ) > 0:
    #    return
    
    for setting, details in settings.items():
        # flatten dict
        db_setting = {'setting': setting}
        db_setting.update(details)
        db_setting.pop('validate')

        if db_setting['options'] is not None:
            # convert options list to json string
            db_setting['options'] = json.dumps(db_setting['options'])
        
        # insert setting into settings table
        get_db().execute('INSERT INTO settings VALUES (:setting, :value, :label, :default, :required, :options)', db_setting)

    get_db().commit() 

def close_db(e=None):
    db = g.pop('db', None)
    
    if db is not None:
        db.close()


### settings

def get_settings_list():
    return get_db().execute('SELECT setting FROM settings').fetchall()

def get_settings():
    db_settings = get_db().execute('SELECT * FROM settings').fetchall()

    if len(db_settings) == 0:
        return {}
        
    # convert list to dict
    db_settings = {setting['setting']: setting for setting in db_settings}

    # convert options from json to list
    for setting in db_settings.keys():
        if db_settings[setting]['options'] != None:
            db_settings[setting]['options'] = json.loads(db_settings[setting]['options'])

    return db_settings

def get_setting_value(setting):
    db_setting = get_db().execute('SELECT value FROM settings WHERE setting=?', (setting,) ).fetchone()
    db_setting = db_setting['value']

    if db_setting is None:
        return db_setting
    elif db_setting.isnumeric():
        return int(db_setting)

    return db_setting

def set_setting(setting, value):    
    if setting not in get_settings_list():
        raise ValueError('Invalid setting: {}'.format(setting))

    get_db().execute('UPDATE settings SET value=? WHERE setting=?', (setting, value) )
    get_db().commit() 


### messages

def get_user_conversations(username):
    conversations = []
    users = get_db().execute('SELECT DISTINCT origin, destination FROM messages WHERE origin=? OR destination=?', (username, username) ).fetchall()

    if users is None or len(users) == 0:
        # no messages to process
        return conversations
        
    unique_users = []
    for user in users:
        if user['origin'] not in unique_users and user['origin'] != username:
            unique_users.append(user['origin'])
        if user['destination'] not in unique_users and user['destination'] != username:
            unique_users.append(user['destination'])

    for user in unique_users:
        unread = get_user_unread_message_count(user)
        last_heard = get_user_last_heard_timestamp(user)

        conversation = {
            'username': user,
            'time': last_heard,
            'unread': bool(unread)
        }

        conversations.append(conversation)

    return conversations

def set_user_messages_read(username):
    get_db().execute('UPDATE messages SET unread=0 WHERE origin=?', (username,) )
    get_db().commit() 

def get_user_unread_message_count(username):
    unread = get_db().execute('SELECT COUNT(*) FROM messages WHERE origin=? AND unread=1', (username,) ).fetchone()
    return int(unread[0])

def get_user_chat_history(user_a, user_b):
    users = {'user_a': user_a, 'user_b': user_b}
    # select both sides of the conversation for the given users
    return get_db().execute('SELECT * FROM messages WHERE (origin=:user_a AND destination=:user_b) OR (origin=:user_b AND destination=:user_a)', users).fetchall()

# msg = pyjs8call.Message object
def store_message(msg):
    get_db().execute('INSERT INTO messages VALUES (:id, :origin, :destination, :type, :time, :text, :unread, :status, :error, :encrypted)', msg)
    get_db().commit() 

# msg = pyjs8call.Message object
def update_outgoing_message_status(msg):
    get_db().execute('UPDATE messages SET status=? WHERE id=?', (msg.status, msg.id) )
    get_db().commit() 

def get_user_last_heard_timestamp(username):
    timestamp = get_db().execute('SELECT MAX(time) FROM messages WHERE origin=?', (username,) ).fetchone()
    
    if len(timestamp) == 0:
        return 0
    
    return timestamp[0]
    
