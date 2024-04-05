from flask import current_app

from portalmessenger import db


# lambda references to dict elements will not be updated after dict creation, even if dict changes (which it should not)
# 'display' indicates whether the setting should be displayed in the Settings view (may still be displayed elsewhere)
# 'validate' is not stored in the db, only referenced from default_settings
default_settings = {
    'modem': {
        'value': 'JS8Call', 
        'label': 'Modem',
        'default': 'JS8Call',
        'required': False,
        'options': ['JS8Call'],
        'display': False,
        'restart': False,
        'validate': lambda option: option in default_settings['modem']['options']
    },
    'callsign': {
        'value': '',
        'label': 'Callsign',
        'default': '',
        'required': True,
        'options': None,
        'display': True,
        'restart': True,
        'validate': lambda callsign: any([char.isdigit() for char in callsign]) and len(callsign) <= 9
    },
    'grid': {
        'value': '',
        'label': 'Grid Square',
        'default': '',
        'required': False,
        'options': None,
        'display': True,
        'restart': False,
        'validate': lambda grid: grid[0].isalpha() and grid[1].isalpha() and grid[2].isdigit() and grid[3].isdigit()
    },
    'speed': {
        'value': 'normal',
        'label': 'JS8Call Speed',
        'default': 'normal',
        'required': False,
        'options': ['slow', 'normal', 'fast', 'turbo'],
        'display': True,
        'restart': True,
        'validate': lambda option: option in default_settings['speed']['options']
    },
    'freq': {
        'value': '7078000', 
        'label': 'Frequency (Hz)',
        'default': '7078000',
        'required': True,
        'options': None,
        'display': True,
        'restart': False,
        'validate': lambda freq: freq.isnumeric()
    },
    'groups': {
        'value': '',
        'label': 'Groups (@)',
        'default': '',
        'required': False,
        'options': None,
        'display': True,
        'restart': False,
        'validate': lambda groups: all([bool(group.strip().startswith('@') and len(group.strip()) <= 9) for group in groups.split(',')])
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
        'validate': lambda aging: aging.isnumeric()
    },
    'heartbeat': {
        'value': 'disable', 
        'label': 'Heartbeat Net',
        'default': 'disable',
        'required': False,
        'options': ['enable', 'disable'],
        'display': True,
        'restart': False,
        'validate': lambda option: option in default_settings['heartbeat']['options']
    },
    'inbox': {
        'value': 'disable', 
        'label': 'Inbox Monitor',
        'default': 'disable',
        'required': False,
        'options': ['enable', 'disable', 'query @ALLCALL'],
        'display': True,
        'restart': False,
        'validate': lambda option: option in default_settings['inbox']['options']
    },
    'tab': {
        'value': 'activity', 
        'label': 'Default Tab',
        'default': 'activity',
        'required': False,
        'options': ['activity', 'messages'],
        'display': True,
        'restart': False,
        'validate': lambda option: option in default_settings['tab']['options']
    },
    'theme': {
        'value': 'light', 
        'label': 'App Theme',
        'default': 'light',
        'required': False,
        'options': ['light', 'dark'],
        'display': True,
        'restart': False,
        'validate': lambda option: option in default_settings['theme']['options']
    },
    'size': {
        'value': 'normal', 
        'label': 'Font Size',
        'default': 'normal',
        'required': False,
        'options': ['normal', 'large'],
        'display': True,
        'restart': False,
        'validate': lambda option: option in default_settings['size']['options']
    },
    'propagation': {
        'value': '60', 
        'label': 'Propagation Period (minutes)',
        'default': '60',
        'required': False,
        'options': ['30', '60', '120'],
        'display': False,
        'restart': False,
        'validate': lambda option: option in default_settings['propagation']['options']
    }
}

def validate(setting, value):
    return default_settings[setting]['validate'](value)

def update_modem_setting(setting, value):
    #TODO update modem name handling to support other modems
    if current_app.config['MODEM'].name.lower() == 'js8call':
        if setting == 'callsign': current_app.config['MODEM'].update_callsign(value)
        elif setting == 'speed': current_app.config['MODEM'].update_speed(value)

        # js8call must be running to update these settings
        if current_app.config['MODEM'].js8call.connected():
            if setting == 'freq': current_app.config['MODEM'].update_freq(value)
            elif setting == 'grid': current_app.config['MODEM'].update_grid(value)
            elif setting == 'heartbeat': current_app.config['MODEM'].update_heartbeat(value)
            elif setting == 'inbox': current_app.config['MODEM'].update_inbox(value)

# form_settings = flask.request.form from post request
def update_settings(form_settings):
    restart = False
    db_settings = db.get_settings()

    # initialize restart and error elements
    for setting in db_settings.keys():
        db_settings[setting]['restart'] = False
        db_settings[setting]['error'] = None
    
    for setting, value in form_settings.items():
        value = value.strip()
        
        if setting in ['callsign', 'grid']:
            value = value.upper()

        if value == db_settings[setting]['value']:
            # skip further processing if settings not changed
            continue
            
        if not default_settings[setting]['validate'](value):
            db_settings[setting]['error'] = 'Invalid {}: {}'.format(setting, value)
            # skip further processing if setting value invalid
            continue

        db.set_setting(setting, value)
        db_settings[setting]['value'] = value
        update_modem_setting(setting, value)

        # setting validated amd updated, indicate restart if required
        db_settings[setting]['restart'] = default_settings[setting]['restart']
        
    return db_settings
    
