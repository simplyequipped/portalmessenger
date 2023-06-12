import json
import sqlite3

try:
    import ecc
    encryption_available = True
except ImportError:
    encryption_available = False

    
class Settings:
    def __init__(self, db_file):
        self._db_file = db_file
        self._local_settings = {}
        

        #TODO initialize local app settings

        # initialize settings in db
        with sqlite3.connect(self._db_file, detect_types=sqlite3.PARSE_DECLTYPES) as con:
            sqlite3.register_adapter(bool, int)
            sqlite3.register_converter('BOOLEAN', lambda v: v != '0')
            cur = con.cursor()

            tables = cur.execute('SELECT name FROM sqlite_master').fetchall()
            tables = [tables[i][0] for i in range(len(tables))]

            if 'settings' not in tables:
                cur.execute('CREATE TABLE settings(setting, value, label, "default", required, options)')

            settings = self.db_settings()
            global default_settings
            global encryption_available

            for default_setting, default_data in default_settings.items():
                if default_setting not in settings.keys():
                    new_setting = default_data
                    new_setting['setting'] = default_setting

                    if default_setting == 'encryption' and not encryption_available:
                        new_setting['options'].remove('enable')
                        new_setting['value'] = 'disable'
                        
                    if isinstance(new_setting['options'], list):
                        new_setting['options'] = json.dumps(new_setting['options'])

                    cur.execute('INSERT INTO settings VALUES (:setting, :value, :label, :default, :required, :options)', new_setting)

            con.commit()

        self.set('db_file', self._db_file)

    def db_settings(self):
        with sqlite3.connect(self._db_file, detect_types=sqlite3.PARSE_DECLTYPES) as con:
            sqlite3.register_adapter(bool, int)
            sqlite3.register_converter('BOOLEAN', lambda v: v != '0')
            db = con.cursor()
            global encryption_available

            columns = ['setting', 'value', 'label', 'default', 'required', 'options']
            settings = db.execute('SELECT * FROM settings').fetchall()
            settings = [dict(zip(columns, setting)) for setting in settings]
    
            if len(settings) > 0:
                settings = {setting['setting']: setting for setting in settings}

                for setting in settings:
                    if settings[setting]['options'] != None:
                        settings[setting]['options'] = json.loads(settings[setting]['options'])
                        
                    if setting == 'encryption' and 'enable' in settings[setting]['options'] and not encryption_available:
                        settings[setting]['options'].remove('enable')
                        settings[setting]['value'] = 'disable'
            else:
                settings = {}

            con.commit()

        return settings

    def local_settings(self):
        return self._local_settings

    def settings(self):
        return {setting: data['value'] for setting, data in self.db_settings().items()}
    
    def get(self, setting):

        if setting in self._local_settings.keys():
            return self._local_settings[setting]
        
        db_settings = self.settings()

        if setting in db_settings.keys():
            return db_settings[setting]
        else:
            return None

    def set(self, setting, value):
        db_settings = self.db_settings()
        
        if setting in db_settings:
            # set db setting
            valid, error = self.validate_setting(setting, value, db_settings)

            if valid:
                # update setting in db
                with sqlite3.connect(self._db_file, detect_types=sqlite3.PARSE_DECLTYPES) as con:
                    sqlite3.register_adapter(bool, int)
                    sqlite3.register_converter('BOOLEAN', lambda v: v != '0')
                    db = con.cursor()
                    db.execute('UPDATE settings SET value = :value WHERE setting = :setting', {'setting': setting, 'value': value})
                    con.commit()

            return (valid, error)

        else:
            # set local setting
            self._local_settings[setting] = value

    def validate_setting(self, setting, value, settings):
        error = None
        valid = False

        if setting not in settings:
            error = 'Invalid setting'
            return (valid, error)

        if setting == 'callsign':
            valid, error = self.validate_callsign(value)
        elif setting == 'grid':
            valid, error = self.validate_grid(value)
        elif setting == 'aging':
            valid, error = self.validate_aging(value)
        elif setting == 'freq':
            valid, error = self.validate_freq(value)
        else:
            #TODO test logic
            if not isinstance(settings[setting], dict):
                # local setting
                valid = True
            elif (
                # db setting
                isinstance(settings[setting], dict) and
                settings[setting]['options'] != None and
                value in settings[setting]['options']
            ):
                valid = True
            else:
                valid = False
                error = 'Invalid ' + setting

        return (valid, error)

    def validate_callsign(self, callsign):
        error = None
        valid = False

        if any([char.isdigit() for char in callsign]):
            valid = True
        else:
            valid = False
            error = 'Callsign must contain at least one digit [0-9]'

        if len(callsign) <=9:
            if valid:
                valid = True
        else:
            valid = False
            if error == None:
                error = 'Callsign max length is 9 characters'
            else:
                error += ', and have a max length of 9 characters'

        return (valid, error)

    def validate_grid(self, grid):
        error = None
        valid = False

        if len(grid) == 4:
            valid = True
        else:
            valid = False
            error = 'Grid square length must be 4 characters'
            return (valid, error)

        if grid[0].isalpha() and grid[1].isalpha() and grid[2].isdigit() and grid[3].isdigit():
            if valid:
                valid = True
        else:
            valid = False
            if error == None:
                error = 'Grid square format must be AB12'
            else:
                error += ', and formatted as AB12'

        return (valid, error)

    def validate_aging(self, aging):
        error = None
        valid = False

        if aging.isnumeric():
            valid = True
        else:
            valid = False
            error = 'Activity aging must be a number'

        return (valid, error)

    def validate_freq(self, freq):
        error = None
        valid = False

        if freq.isnumeric():
            valid = True
        else:
            valid = False
            error = 'Frequency must be a number'

        return (valid, error)



default_settings = {
    #TODO add applicable modem to each setting
    'modem': {
        'value': 'JS8Call', 
        'label': 'Modem',
        'default': 'JS8Call',
        'required': False,
        'options': ['JS8Call']
    },
    'callsign': {
        'value': '',
        'label': 'Callsign',
        'default': '',
        'required': True,
        'options': None
    },
    'freq': {
        'value': '7078000', 
        'label': 'Frequency (Hz)',
        'default': '7078000',
        'required': True,
        'options': None
    },
    'grid': {
        'value': '',
        'label': 'Grid Square',
        'default': '',
        'required': False,
        'options': None
    },
    'speed': {
        'value': 'fast',
        'label': 'JS8Call Speed',
        'default': 'fast',
        'required': False,
        'options': ['slow', 'normal', 'fast', 'turbo']
    },
    'theme': {
        'value': 'light', 
        'label': 'App Theme',
        'default': 'light',
        'required': False,
        'options': ['light', 'dark']
    },
    'tab': {
        'value': 'activity', 
        'label': 'Default Tab',
        'default': 'activity',
        'required': False,
        'options': ['activity', 'messages']
    },
    'size': {
        'value': 'normal', 
        'label': 'Font Size',
        'default': 'normal',
        'required': False,
        'options': ['normal', 'large']
    },
    # activity/spot aging in minutes
    'aging': {
        'value': '15', 
        'label': 'Aging (minutes)',
        'default': '15',
        'required': True,
        'options': None
    },
    # ECC/AES-256 encryption
    'encryption': {
        'value': 'disable', 
        'label': 'Encryption',
        'default': 'disable',
        'required': False,
        'options': ['enable', 'disable']
    }
}

