# default settings
# note: lambda references to dict elements will not be updated after dict creation
settings = {
    'modem': {
        'value': 'JS8Call', 
        'label': 'Modem',
        'default': 'JS8Call',
        'required': False,
        'options': ['JS8Call'],
        'validate': lambda option: option in settings['modem']['options']
    },
    'callsign': {
        'value': '',
        'label': 'Callsign',
        'default': '',
        'required': True,
        'options': None
        'validate': lambda callsign: any([char.isdigit() for char in callsign]) and len(callsign) <= 9
    },
    'freq': {
        'value': '7078000', 
        'label': 'Frequency (Hz)',
        'default': '7078000',
        'required': True,
        'options': None,
        'validate': lambda freq: freq.isnumeric()
    },
    'grid': {
        'value': '',
        'label': 'Grid Square',
        'default': '',
        'required': False,
        'options': None,
        'validate': lambda grid: grid[0].isalpha() and grid[1].isalpha() and grid[2].isdigit() and grid[3].isdigit()
    },
    'speed': {
        'value': 'normal',
        'label': 'JS8Call Speed',
        'default': 'normal',
        'required': False,
        'options': ['slow', 'normal', 'fast', 'turbo'],
        'validate': lambda option: option in settings['speed']['options']
    },
    'theme': {
        'value': 'light', 
        'label': 'App Theme',
        'default': 'light',
        'required': False,
        'options': ['light', 'dark'],
        'validate': lambda option: option in settings['theme']['options']
    },
    'tab': {
        'value': 'activity', 
        'label': 'Default Tab',
        'default': 'activity',
        'required': False,
        'options': ['activity', 'messages'],
        'validate': lambda option: option in settings['tab']['options']
    },
    'size': {
        'value': 'normal', 
        'label': 'Font Size',
        'default': 'normal',
        'required': False,
        'options': ['normal', 'large'],
        'validate': lambda option: option in settings['size']['options']
    },
    # activity/spot aging in minutes
    'aging': {
        'value': '15', 
        'label': 'Aging (minutes)',
        'default': '15',
        'required': True,
        'options': None,
        'validate': lambda settting: setting['value'].isnumeric()
    },
    'heartbeat': {
        'value': 'disable', 
        'label': 'Heartbeat Net',
        'default': 'disable',
        'required': False,
        'options': ['enable', 'disable'],
        'validate': lambda option: option in settings['heartbeat']['options']
    }
#    },
#    # ECC/AES-256 encryption
#    'encryption': {
#        'value': 'disable', 
#        'label': 'Encryption',
#        'default': 'disable',
#        'required': False,
#        'options': ['enable', 'disable'],
#        'validate': lambda option: option in settings['encryption']['options']
#    }
}

