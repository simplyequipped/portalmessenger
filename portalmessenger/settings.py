from flask import current_app

from portalmessenger import db


# note: lambda references to dict elements will not be updated after dict creation
default_settings = {
    'modem': {
        'value': 'JS8Call', 
        'label': 'Modem',
        'default': 'JS8Call',
        'required': False,
        'options': ['JS8Call'],
        'update': None,
        'validate': lambda option: option in default_settings['modem']['options']
    },
    'callsign': {
        'value': '',
        'label': 'Callsign',
        'default': '',
        'required': True,
        'options': None,
        'update': None,
        'validate': lambda callsign: any([char.isdigit() for char in callsign]) and len(callsign) <= 9
    },
    'freq': {
        'value': '7078000', 
        'label': 'Frequency (Hz)',
        'default': '7078000',
        'required': True,
        'options': None,
        'update': None,
        'validate': lambda freq: freq.isnumeric()
    },
    'grid': {
        'value': '',
        'label': 'Grid Square',
        'default': '',
        'required': False,
        'options': None,
        'update': None,
        'validate': lambda grid: grid[0].isalpha() and grid[1].isalpha() and grid[2].isdigit() and grid[3].isdigit()
    },
    'speed': {
        'value': 'normal',
        'label': 'JS8Call Speed',
        'default': 'normal',
        'required': False,
        'options': ['slow', 'normal', 'fast', 'turbo'],
        'update': None,
        'validate': lambda option: option in default_settings['speed']['options']
    },
    'theme': {
        'value': 'light', 
        'label': 'App Theme',
        'default': 'light',
        'required': False,
        'options': ['light', 'dark'],
        'update': None,
        'validate': lambda option: option in default_settings['theme']['options']
    },
    'tab': {
        'value': 'activity', 
        'label': 'Default Tab',
        'default': 'activity',
        'required': False,
        'options': ['activity', 'messages'],
        'update': None,
        'validate': lambda option: option in default_settings['tab']['options']
    },
    'size': {
        'value': 'normal', 
        'label': 'Font Size',
        'default': 'normal',
        'required': False,
        'options': ['normal', 'large'],
        'update': None,
        'validate': lambda option: option in default_settings['size']['options']
    },
    # activity/spot aging in minutes
    'aging': {
        'value': '15', 
        'label': 'Aging (minutes)',
        'default': '15',
        'required': True,
        'options': None,
        'update': None,
        'validate': lambda aging: aging.isnumeric()
    },
    'heartbeat': {
        'value': 'disable', 
        'label': 'Heartbeat Net',
        'default': 'disable',
        'required': False,
        'options': ['enable', 'disable'],
        'update': None,
        'validate': lambda option: option in default_settings['heartbeat']['options']
    },
    'inbox': {
        'value': 'disable', 
        'label': 'Inbox Monitor',
        'default': 'disable',
        'required': False,
        'options': ['enable', 'disable', 'query allcall'],
        'update': None,
        'validate': lambda option: option in default_settings['inbox']['options']
    }
#    },
#    # ECC/AES-256 encryption
#    'encryption': {
#        'value': 'disable', 
#        'label': 'Encryption',
#        'default': 'disable',
#        'required': False,
#        'options': ['enable', 'disable'],
#        'validate': lambda option: option in default_settings['encryption']['options']
#    }
}

def validate(setting, value):
    return default_settings[setting]['validate'](value)

# form_settings = flask.request.form from post request
def update_settings(form_settings):
    restart = False
    db_settings = db.get_settings()
    
    for setting, value in form_settings.items():
        if setting in ['callsign', 'grid']:
            value = value.upper()

        if value == db_settings[setting]['value']:
            db_settings[setting]['restart'] = False
            db_settings[setting]['error'] = None
            # skip further processing if settings not changed
            continue
            
        if not default_settings[setting]['validate'](value):
            db_settings[setting]['error'] = 'Invalid {}: {}'.format(setting, value)
            # skip further processing if setting value invalid
            continue

        #TODO update modem name handling to support other modems
        #if current_app.config['MODEM'].name.lower() == 'js8call':
        if default_settings[setting]['update'] is not None:
            db_settings[setting]['restart'] = default_settings[setting]['update'](value)
    
        db.set_setting(setting, value)
        
    return db_settings
    
