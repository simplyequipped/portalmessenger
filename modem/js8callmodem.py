import pyjs8call

try:
    import ecc
    encryption_available = True
except ModuleNotFoundError:
    encryption_available = False


class JS8CallModem:
    def __init__(self, callsign, headless=True):
        self.name = 'js8call'
        self._callsign = callsign
        self.headless = headless
        self.first_start = True
        self.incoming = None
        self.outgoing = None
        self.spots = None
        self.inbox = None
        
        # encryption variables
        self.encryption = False
        self.idm = None
        self._identity = None

        # initialize pyjs8call client and callback functions
        self.js8call = pyjs8call.Client()
        self.js8call.callback.register_incoming(self.incoming_callback)
        self.js8call.callback.outgoing = self.outgoing_callback
        self.js8call.callback.spots = self.spots_callback
        self.js8call.callback.inbox = self.inbox_callback

        # set app specific profile
        if 'Portal' not in self.js8call.settings.get_profile_list():
            self.js8call.config.create_new_profile('Portal')
        self.js8call.settings.set_profile('Portal')
        # disable idle timeout
        self.js8call.settings.set_idle_timeout(0)
        # set distance units
        self.js8call.settings.set_distance_units_miles(True)
        # handle callsign not set
        if self._callsign not in (None, ''):
            self.js8call.settings.set_station_callsign(self._callsign)

        #TODO
        #global encryption_available
        #print('encryption available: ' + str(encryption_available))
        
    def enable_encryption(self):
        global encryption_available
        
        if encryption_available:
            if self.idm is None:
                self.idm = ecc.IdentityManager()
                
            self._identity = self.idm.identity_from_file(self._callsign)

            if not self._identity.loaded_from_file:
                self._identity = self.idm.new_identity(self._callsign)
                self._identity.to_file()

            self.js8call.process_incoming = self.process_incoming
            self.js8call.process_outgoing = self.process_outgoing
            
            self.encryption = True

        return self.encryption
            
    def disable_encryption(self, write_to_file=True):
        self.encryption = False
        self.js8call.process_incoming = None
        self.js8call.process_outgoing = None
        
        if write_to_file:
            self.idm.to_file()
            
        del self.idm
        self.idm = None
        del self._identity
        self._identity = None
        
        return not self.encryption
                
    def start(self):
        if not self.js8call.online:
            self.js8call.start(headless = self.headless)

    def stop(self):
        self.js8call.stop()

    def restart(self):
        self.js8call.restart()

    def online(self):
        return self.js8call.online

    def send(self, destination, text):
        return self.js8call.send_directed_message(destination, text)

    def get_spots(self, *args, **kwargs):
        all_spots = self.js8call.spots.filter(*args, **kwargs)

        # remove duplicates, keeping the most recent spot
        spots = {}
        for spot in all_spots:
            if spot.origin not in spots:
                spots[spot.origin] = spot
            elif spot.age() > spots[spot.origin].age():
                spots[spot.origin] = spot

        spots = list(spots.values())
        spots.sort()
        return spots
                
    def incoming_callback(self, msg):
        if msg.destination not in self.js8call.identities():
            return

        elif self.incoming != None:
            self.incoming(msg)

    def outgoing_callback(self, msg):
        if self.outgoing is not None:
            self.outgoing(msg)

    def spots_callback(self, spots):
        if self.spots is not None:
            self.spots(spots)

    def inbox_callback(self, msgs):
        if self.inbox is not None:
            self.inbox(msgs)
            
    def process_incoming(self, msg):
        if not self.encryption:
            return msg
        
        try:
            msg.set('text', self._identity.decrypt(msg.text))
            msg.set('encrypted', True)
        except ValueError:
            msg.set('error', 'decrypt failed')
            
        return msg
    
    def process_outgoing(self, msg):
        if not self.encryption:
            return msg
        
        # msg.text is overwritten when setting msg.value
        text = msg.text

        try:
            msg.set('value', self.idm.encrypt(msg.value, msg.destination))
            msg.set('encrypted', True)
        except LookupError:
            msg.set('error', 'public key unavailable')

        # restore msg.text
        msg.set('text', text)
            
        return msg
