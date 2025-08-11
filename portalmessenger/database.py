'''
TinyDB database integration for Portal Messenger
Replaces SQLite with JSON-based TinyDB storage
'''

import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware


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
    'pyjs8call-api-host': {
        'value': 'localhost',
        'label': 'pyjs8call API IP/Host',
        'default': 'localhost',
        'required': True,
        'options': None,
        'display': True,
        'restart': False,
        'validate': lambda host: len(host.strip()) > 0
    },
    'pyjs8call-api-port': {
        'value': 8080,
        'label': 'pyjs8call API Port',
        'default': 8080,
        'required': True,
        'options': None,
        'display': True,
        'restart': False,
        'validate': lambda port: port.isnumeric() and 1 <= int(port) <= 65535
    },
    'callsign': {
        'value': '',
        'label': 'Callsign',
        'default': '',
        'required': True,
        'options': None,
        'display': True,
        'restart': True,
        'validate': lambda callsign: any([char.isdigit() for char in callsign]) and len(callsign) <= 9 and len(callsign) > 0
    },
    'grid': {
        'value': '',
        'label': 'Grid Square',
        'default': '',
        'required': False,
        'options': None,
        'display': True,
        'restart': False,
        'validate': lambda grid: len(grid) == 0 or (len(grid) >= 4 and grid[0].isalpha() and grid[1].isalpha() and grid[2].isdigit() and grid[3].isdigit())
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
        'restart': True,
        'validate': lambda groups: len(groups) == 0 or all([bool(group.strip().startswith('@') and len(group.strip()) <= 9) for group in groups.split(',')])
    },
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
        'value': 'dark',
        'label': 'App Theme',
        'default': 'dark',
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


class PortalDatabase:
    '''
    Database interface handling messages and settings using TinyDB
    '''
    
    def __init__(self, db_path: str = 'portalmessenger.json'):
        '''Initialize database with given path'''
        self.db_path = os.path.expanduser(db_path)
        # use caching middleware for better performance
        self.db = TinyDB(self.db_path, storage=CachingMiddleware(JSONStorage))
        
        # database tables
        self.messages = self.db.table('messages')
        self.settings = self.db.table('settings')
        
        # initialize default settings if empty
        if len(self.settings) == 0:
            self._initialize_default_settings()
    
    def _initialize_default_settings(self):
        '''Initialize default app settings by flattening global default_settings dict'''
        settings_list = []
        
        for setting_name, setting_config in default_settings.items():
            # flatten settings
            flattened_setting = {'setting': setting_name}
            for key, value in setting_config.items():
                # drop lambda functions
                if key not in ('validate'):
                    flattened_setting[key] = value
            
            settings_list.append(flattened_setting)
        
        self.settings.insert_multiple(settings_list)
    
    # settings methods
    def get_setting(self, setting_name: str) -> Optional[Dict[str, Any]]:
        '''Get a single setting by name'''
        Setting = Query()
        result = self.settings.search(Setting.setting == setting_name)
        return result[0] if result else None
    
    def get_all_settings(self) -> List[Dict[str, Any]]:
        '''Get all settings'''
        return self.settings.all()
    
    def update_setting(self, setting_name: str, value: Any) -> Optional[Dict[str, Any]]:
        '''Update a setting value with validation, returns setting dict with valid key'''
        if setting_name not in default_settings:
            return None
        
        validate_func = default_settings[setting_name]['validate']
        is_valid = validate_func(str(value))
        
        if is_valid:
            Setting = Query()
            self.settings.update({'value': str(value)}, Setting.setting == setting_name)
        
        setting = self.get_setting(setting_name)
        setting['valid'] = is_valid

        if not is_valid:
            # return invalid value
            setting['value'] = str(value)
        
        return setting
    
    def create_setting(self, setting_data: Dict[str, Any]) -> int:
        '''Create a new setting'''
        return self.settings.insert(setting_data)
    
    # message methods
    def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        '''Get a single message by ID'''
        Message = Query()
        result = self.messages.search(Message.id == message_id)
        return result[0] if result else None
    
    def get_all_messages(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        '''Get all messages, optionally limited'''
        messages = self.messages.all()
        # sort by time (most recent first)
        messages.sort(key=lambda m: m.get('time', ''), reverse=True)
        
        if limit:
            return messages[:limit]
        return messages
    
    def get_messages_by_origin(self, origin: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        '''Get messages from a specific origin'''
        Message = Query()
        messages = self.messages.search(Message.origin == origin)
        messages.sort(key=lambda m: m.get('time', ''), reverse=True)
        
        if limit:
            return messages[:limit]
        return messages
    
    def get_messages_by_destination(self, destination: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        '''Get messages to a specific destination'''
        Message = Query()
        messages = self.messages.search(Message.destination == destination)
        messages.sort(key=lambda m: m.get('time', ''), reverse=True)
        
        if limit:
            return messages[:limit]
        return messages
    
    def get_conversation(self, callsign1: str, callsign2: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        '''Get conversation between two callsigns or with a group'''
        Message = Query()
        
        if callsign2.startswith('@'):
            # group conversation: only messages to the group
            messages = self.messages.search(Message.destination == callsign2)
        else:
            # bidirectional conversation
            messages = self.messages.search(
                ((Message.origin == callsign1) & (Message.destination == callsign2)) |
                ((Message.origin == callsign2) & (Message.destination == callsign1))
            )
        
        messages.sort(key=lambda m: m.get('time', ''))
        
        if limit:
            return messages[-limit:]
        return messages
    
    def create_message(self, message_data: Dict[str, Any]) -> int:
        '''Create a new message'''
        if 'time' not in message_data:
            message_data['time'] = datetime.now().isoformat()
        
        # set defaults for optional fields
        message_data.setdefault('unread', True)
        message_data.setdefault('status', 'received')
        message_data.setdefault('error', None)
        
        return self.messages.insert(message_data)
    
    def update_message(self, message_id: str, updates: Dict[str, Any]) -> bool:
        '''Update a message'''
        Message = Query()
        result = self.messages.update(updates, Message.id == message_id)
        return len(result) > 0
    
    def mark_message_read(self, message_id: str) -> bool:
        '''Mark a message as read'''
        return self.update_message(message_id, {'unread': False})
    
    def delete_message(self, message_id: str) -> bool:
        '''Delete a message'''
        Message = Query()
        result = self.messages.remove(Message.id == message_id)
        return len(result) > 0
    
    def get_unread_count(self) -> int:
        '''Get count of unread messages'''
        Message = Query()
        return len(self.messages.search(Message.unread == True))
    
    def close(self):
        '''Close the database connection'''
        self.db.close()


# global database instance
_db_instance = None

def get_database(db_path: str = 'portalmessenger.json') -> PortalDatabase:
    '''Get or create the global database instance'''
    global _db_instance
    if _db_instance is None:
        _db_instance = PortalDatabase(db_path)
    return _db_instance

def close_database():
    '''Close the global database instance'''
    global _db_instance
    if _db_instance:
        _db_instance.close()
        _db_instance = None