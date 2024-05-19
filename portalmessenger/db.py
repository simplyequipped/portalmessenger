import json
import sqlite3

from flask import current_app, g
   

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

# initialize db from schema
# allows for addition of new settings in future revisions without affecting existing settings
def init_db():
    with current_app.open_resource('schema.sql') as f:
        get_db().executescript( f.read().decode('utf8'))

    existing_settings = get_settings()
    from portalmessenger.settings import default_settings

    for setting, details in default_settings.items():
        # skip if setting already exists
        if setting in existing_settings:
            continue
        
        # flatten dict
        db_setting = {'setting': setting}
        db_setting.update(details)

        # remove unstored setting properties
        for key in ['validate', 'update', 'js8call-api']:
            db_setting.pop(key)

        if db_setting['options'] is not None:
            # convert options list to json string
            db_setting['options'] = json.dumps(db_setting['options'])
        
        # insert setting into settings table
        get_db().execute('INSERT INTO settings VALUES (:setting, :value, :label, :default, :required, :options, :display)', db_setting)

    get_db().commit() 

def close_db(e=None):
    db = g.pop('db', None)
    
    if db is not None:
        db.close()


### settings

def get_settings():
    db_settings = get_db().execute('SELECT * FROM settings').fetchall()

    if len(db_settings) == 0:
        return {}
        
    # convert list of row objects to dict of dicts
    db_settings = {setting['setting']: dict(setting) for setting in db_settings}

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
    if setting not in get_settings().keys():
        raise ValueError('Invalid setting: {}'.format(setting))

    get_db().execute('UPDATE settings SET value=? WHERE setting=?', (value, setting) )
    get_db().commit() 


### messages

def get_user_conversations(username):
    conversations = []
    query = '''
    SELECT DISTINCT destination FROM messages WHERE origin=? AND destination NOT LIKE '@%'
    UNION
    SELECT DISTINCT origin FROM messages WHERE destination=? AND origin NOT LIKE '@%'
    UNION
    SELECT DISTINCT destination FROM messages WHERE destination LIKE '@%'
    '''
    users = get_db().execute(query, (username, username) ).fetchall()

    if users is None or len(users) == 0:
        # no messages to process
        return conversations
    
#    unique_users = []
#    for user in users:
#        if user['origin'] not in unique_users and user['origin'] != username:
#            unique_users.append(user['origin'])
#        if user['destination'] not in unique_users and user['destination'] != username:
#            unique_users.append(user['destination'])
#
#    for user in unique_users:
    for user in users:
        unread = get_user_unread_message_count(user[0])
        last_msg = get_last_user_msg_timestamp(user[0])

        conversation = {
            'username': user[0],
            'time': last_msg,
            'unread': bool(unread)
        }

        conversations.append(conversation)

    return conversations

def remove_user_conversations(username):
    get_db().execute('DELETE FROM messages WHERE origin=? OR destination=?', (username, username) )
    get_db().commit() 

def set_user_messages_read(username):
    if username.startswith('@'):
        query = 'UPDATE messages SET unread=0 WHERE destination=?'
    else:
        query = 'UPDATE messages SET unread=0 WHERE origin=?'

    get_db().execute(query, (username,) )
    get_db().commit() 

def get_user_unread_message_count(username):
    if username.startswith('@'):
        query = 'SELECT COUNT(*) FROM messages WHERE destination=? AND unread=1'
    else:
        query = 'SELECT COUNT(*) FROM messages WHERE origin=? AND unread=1'

    unread = get_db().execute(query, (username,) ).fetchone()
    return int(unread[0])

def get_user_chat_history(chat_user, local_user):
    users = {'chat_user': chat_user, 'local_user': local_user}

    if chat_user.startswith('@'):
        query = 'SELECT * FROM messages WHERE destination=:chat_user'
    else:
        query = 'SELECT * FROM messages WHERE (origin=:chat_user AND destination=:local_user) OR (origin=:local_user AND destination=:chat_user)'

    # select both sides of the conversation for the given users
    history = get_db().execute(query, users).fetchall()
    return [dict(msg) for msg in history]

# msg = pyjs8call.Message object
def store_message(msg):
    get_db().execute('INSERT INTO messages VALUES (:id, :origin, :destination, :type, :time, :text, :unread, :status, :error)', msg)
    get_db().commit() 

# msg = pyjs8call.Message object
def update_outgoing_message_status(msg):
    get_db().execute('UPDATE messages SET status=? WHERE id=?', (msg.status, msg.id) )
    get_db().commit() 

def get_last_user_msg_timestamp(username):
    if username.startswith('@'):
        callsign = get_setting_value('callsign')
        query = 'SELECT MAX(time) FROM messages WHERE destination=? AND origin != ?'
        timestamp = get_db().execute(query, (username, callsign) ).fetchone()
    else:
        query = 'SELECT MAX(time) FROM messages WHERE origin=?'
        timestamp = get_db().execute(query, (username,) ).fetchone()

    if timestamp[0] is None:
        return 0
    
    return int(timestamp[0])
    
