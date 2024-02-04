import json
import sqlite3

from flask import current_app, g

from portalmessenger.settings import settings


# general db

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
    if len( get_settings() ) > 0:
        return
    
    for setting, details in settings.copy().items():
        # flatten dict
        db_setting = {'setting': setting}
        db_setting.update(details)
        db_setting.pop('validate')
        
        if db_setting['options'] is not None:
            # convert options list to json string
            db_setting['options'] = json.dumps(db_setting['options'])
        
        # insert setting into settings table
        get_db().execute('INSERT INTO settings VALUES (:setting, :value, :label, :default, :required, :options)', db_setting)

def close_db(e=None):
    db = g.pop('db', None)
    
    if db is not None:
        db.close()

def get_tables():
    tables = get_db().execute('SELECT name FROM sqlite_master').fetchall()
    tables = [tables[i][0] for i in range( len(tables) )]
    return tables

def get_table_columns(table):
    if table not in get_tables():
        raise ValueError('Invalid table: {}'.format(table))
        
    columns = get_db().execute('PRAGMA table_info()',).fetchall()
    columns = [column[1] for column in columns]
    return columns


### settings

def get_settings_list():
    #TODO check format of returned value from query
    settings = get_db().execute('SELECT setting FROM settings').fetchall()
    return settings

def get_settings():
    #columns = get_table_columns('settings')
    settings = get_db().execute('SELECT * FROM settings').fetchall()
    #settings = [dict(zip(columns, setting)) for setting in settings]

    #TODO
    print(settings)

    if len(settings) == 0:
        return {}
        
    # flatten to single level dict
    settings = {setting['setting']: setting for setting in settings}

    # convert options from json to list
    for setting in settings.keys():
        if settings[setting]['options'] != None:
            settings[setting]['options'] = json.loads(settings[setting]['options'])

    return settings

def get_setting_value(setting):
    #TODO check format of query result
    setting = get_db().execute('SELECT value FROM settings WHERE setting=:setting', {'setting': setting}).fetchone()
    setting = setting[0]
    
    if setting.isnumeric():
        setting = int(setting)

    return setting

def set_setting(setting, value):    
    if setting not in get_settings():
        raise ValueError('Invalid setting: {}'.format(setting))

    get_db().execute('UPDATE settings SET value=:value WHERE setting=:setting', {'setting': setting, 'value': value})


# messages

def get_user_conversations(username):
    conversations = []
    users = get_db().execute('SELECT DISTINCT origin, destination FROM messages WHERE origin = :user OR destination = :user', {'user': username}).fetchall()

    if users is None or len(users) == 0:
        # no messages to process
        return []
        
    # parse result row tuples into single list of unique values
    users = list(set([user for x in users for user in (x[0], x[1])]))
    users.remove(username)

    for user in users:
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
    get_db().execute('UPDATE messages SET unread = 0 WHERE origin = :user', {'user': username})

def get_user_unread_message_count(username):
    unread = get_db().execute('SELECT COUNT(*) FROM messages WHERE origin = :user AND unread = 1', {'user': username}).fetchone()
    return int(unread[0])

def get_user_chat_history(user_a, user_b):
    users = {'user_a': user_a, 'user_b': user_b}
    # select both sides of the conversation for the given users
    columns = db.get_table_columns('messages')
    msgs = get_db().execute('SELECT * FROM messages WHERE (origin = :user_a AND destination = :user_b) OR (origin = :user_b AND destination = :user_a)', users).fetchall()
    msgs = [dict(zip(columns, msg)) for msg in msgs]
    return msgs

# msg = pyjs8call.Message object
def store_message(msg):
    get_db().execute('INSERT INTO messages VALUES (:id, :origin, :destination, :type, :time, :text, :unread, :status, :error, :encrypted)', msg)

# msg = pyjs8call.Message object
def update_outgoing_message_status(msg):
    get_db().execute('UPDATE messages SET status = :status WHERE id = :id', {'id': msg.id, 'status': msg.status})

def get_user_last_heard_timestamp(username):
    last_msg_timestamp = get_db().execute('SELECT MAX(time) FROM messages WHERE origin = :user', {'user': username}).fetchone()

    if last_msg_timestamp not in [None, (None,)] and len(last_msg_timestamp) > 0:
        last_msg_timestamp = last_msg_timestamp[0]
    else:
        last_msg_timestamp = 0

    return last_msg_timestamp
    
