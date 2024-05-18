from flask import current_app

from portalmessenger import db


# lambda references to dict elements will not be updated after dict creation, even if dict changes (which it should not)
# 'display' indicates whether the setting should be displayed in the Settings view (may still be displayed elsewhere)
# 'validate' and 'update' are not stored in the db, only referenced from default_settings
# 'update' is set to a function from the modem object in __init__.create_app
# 'js8call-api' indicates whether a setting requires js8call to be running to change the setting
default_settings = {
    'modem': {
        'value': 'JS8Call', 
        'label': 'Modem',
        'default': 'JS8Call',
        'required': False,
        'options': ['JS8Call'],
        'display': False,
        'restart': False,
        'validate': lambda option: option in default_settings['modem']['options'],
        'update': lambda value: None,
        'js8call-api': False
    },
    'callsign': {
        'value': '',
        'label': 'Callsign',
        'default': '',
        'required': True,
        'options': None,
        'display': True,
        'restart': True,
        'validate': lambda callsign: any([char.isdigit() for char in callsign]) and len(callsign) <= 9,
        'update': lambda value: None,
        'js8call-api': False
    },
    'grid': {
        'value': '',
        'label': 'Grid Square',
        'default': '',
        'required': False,
        'options': None,
        'display': True,
        'restart': False,
        'validate': lambda grid: grid[0].isalpha() and grid[1].isalpha() and grid[2].isdigit() and grid[3].isdigit(),
        'update': lambda value: None,
        'js8call-api': True
    },
    'speed': {
        'value': 'normal',
        'label': 'JS8Call Speed',
        'default': 'normal',
        'required': False,
        'options': ['slow', 'normal', 'fast', 'turbo'],
        'display': True,
        'restart': True,
        'validate': lambda option: option in default_settings['speed']['options'],
        'update': lambda value: None,
        'js8call-api': False
    },
    'freq': {
        'value': '7078000', 
        'label': 'Frequency (Hz)',
        'default': '7078000',
        'required': True,
        'options': None,
        'display': True,
        'restart': False,
        'validate': lambda freq: freq.isnumeric(),
        'update': lambda value: None,
        'js8call-api': True
    },
    'groups': {
        'value': '',
        'label': 'Groups (@)',
        'default': '',
        'required': False,
        'options': None,
        'display': True,
        'restart': True,
        'validate': lambda groups: all([bool(group.strip().startswith('@') and len(group.strip()) <= 9) for group in groups.split(',')]),
        'update': lambda value: None,
        'js8call-api': False
    },
    # activity/spot aging in minutes
    'aging': {
        'value': '15', 
        'label': 'Aging (minutes)',
        'default': '15',
        'required': True,
        'options': None,
        'display': True,
        'restart': False,
        'validate': lambda aging: aging.isnumeric(),
        'update': lambda value: None,
        'js8call-api': False
    },
    'heartbeat': {
        'value': 'disable', 
        'label': 'Heartbeat Net',
        'default': 'disable',
        'required': False,
        'options': ['enable', 'disable'],
        'display': True,
        'restart': False,
        'validate': lambda option: option in default_settings['heartbeat']['options'],
        'update': lambda value: None,
        'js8call-api': True
    },
    'inbox': {
        'value': 'disable', 
        'label': 'Inbox Monitor',
        'default': 'disable',
        'required': False,
        'options': ['enable', 'disable', 'query @ALLCALL'],
        'display': True,
        'restart': False,
        'validate': lambda option: option in default_settings['inbox']['options'],
        'update': lambda value: None,
        'js8call-api': True
    },
    'tab': {
        'value': 'activity', 
        'label': 'Default Tab',
        'default': 'activity',
        'required': False,
        'options': ['activity', 'messages'],
        'display': True,
        'restart': False,
        'validate': lambda option: option in default_settings['tab']['options'],
        'update': lambda value: None,
        'js8call-api': False
    },
    'theme': {
        'value': 'dark', 
        'label': 'App Theme',
        'default': 'dark',
        'required': False,
        'options': ['light', 'dark'],
        'display': True,
        'restart': False,
        'validate': lambda option: option in default_settings['theme']['options'],
        'update': lambda value: None,
        'js8call-api': False
    },
    'size': {
        'value': 'normal', 
        'label': 'Font Size',
        'default': 'normal',
        'required': False,
        'options': ['normal', 'large'],
        'display': True,
        'restart': False,
        'validate': lambda option: option in default_settings['size']['options'],
        'update': lambda value: None,
        'js8call-api': False
    },
    'propagation': {
        'value': '60', 
        'label': 'Propagation Period (minutes)',
        'default': '60',
        'required': False,
        'options': ['30', '60', '120'],
        'display': False,
        'restart': False,
        'validate': lambda option: option in default_settings['propagation']['options'],
        'update': lambda value: None,
        'js8call-api': False
    }
}

# form_settings = flask.request.form from post request
def update_settings(form_settings):
    restart = False
    db_settings = db.get_settings()

    for setting in db_settings.keys():
        db_settings[setting]['restart'] = False
        db_settings[setting]['error'] = None
    
    for setting, value in form_settings.items():
        value = value.strip()
        
        if setting in ['callsign', 'grid', 'groups']:
            value = value.upper()

        if value == db_settings[setting]['value']:
            # skip further processing if setting not changed
            continue
            
        if not default_settings[setting]['validate'](value):
            db_settings[setting]['error'] = 'Invalid {}: {}'.format(setting, value)
            # skip further processing if setting value invalid
            continue

        # update setting in db
        db.set_setting(setting, value)
        db_settings[setting]['value'] = value

        # avoid updating js8call api settings if js8call is not running
        if default_settings[setting]['js8call-api'] and not current_app.config['MODEM'].js8call.connected():
            continue

        # update modem settings
        default_settings[setting]['update'](value)

        # indicate modem restart required to update setting
        db_settings[setting]['restart'] = default_settings[setting]['restart']
        
    return db_settings
    
