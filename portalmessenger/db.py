import json
import sqlite3

from flask import current_app, g


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

def close_db(e=None):
    db = g.pop('db', None)
    
    if db is not None:
        db.close()

def init_app(app):
    app.teardown_appcontext(close_db)
    init_db()

def get_tables():
    tables = get_db().execute('SELECT name FROM sqlite_master').fetchall()
    tables = [tables[i][0] for i in range( len(tables) )]
    return tables

def get_table_columns(table):
    if table not in get_tables():
        raise ValueError('Invalid table: {}'.format(table))
        
    columns = get_db().execute('PRAGMA table_info(:table)', {'table': table}).fetchall()
    columns = [column[1] for column in columns]
    return columns

def get_settings_list():
    #TODO check format of returned value from query
    settings = get_db().execute('SELECT setting FROM settings').fetchall()
    return settings

def get_settings():
    columns = get_table_columns('settings')
    settings = get_db().execute('SELECT * FROM settings').fetchall()
    settings = [dict(zip(columns, setting)) for setting in settings]

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
    
    if setting.isnumeric():
        setting = int(setting)

    return setting

def set_setting(setting, value):    
    if setting not in get_settings():
        raise ValueError('Invalid setting: {}'.format(setting))

    get_db().execute('UPDATE settings SET value=:value WHERE setting=:setting', {'setting': setting, 'value': value})
    
