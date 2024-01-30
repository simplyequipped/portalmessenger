import sqlite3

import click
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
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript( f.read().decode('utf8') )

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_app():
    app.teardown_appcontext(close_db)
    init_db()
