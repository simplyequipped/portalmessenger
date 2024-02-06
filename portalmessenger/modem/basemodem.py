#try:
#    import ecc
#    encryption_available = True
#except ModuleNotFoundError:
#    encryption_available = False

class BaseModem:
    def __init__(self, modem_name):
        self.name = modem_name
        self.incoming = None
        self.outgoing = None
        self.spots = None
        self.inbox = None
        
        # encryption variables
        #self.encryption = False
        #self.idm = None
        #self._identity = None

#    def enable_encryption(self):
#        global encryption_available
#        
#        if encryption_available:
#            if self.idm is None:
#                self.idm = ecc.IdentityManager()
#                
#            self._identity = self.idm.identity_from_file(self._callsign)
#
#            if not self._identity.loaded_from_file:
#                self._identity = self.idm.new_identity(self._callsign)
#                self._identity.to_file()
#
#            self.js8call.process_incoming = self.process_incoming
#            self.js8call.process_outgoing = self.process_outgoing
#            
#            self.encryption = True
#
#        return self.encryption
#            
#    def disable_encryption(self, write_to_file=True):
#        self.encryption = False
#        self.js8call.process_incoming = None
#        self.js8call.process_outgoing = None
#        
#        if write_to_file:
#            self.idm.to_file()
#            
#        del self.idm
#        self.idm = None
#        del self._identity
#        self._identity = None
#        
#        return not self.encryption
                
    def start(self):
        pass

    def stop(self, *args):
        pass

    def restart(self):
        pass

    def online(self):
        pass

    def send(self, *args):
        pass

    def get_spots(self, *args, **kwargs):
        pass

    def get_call_activity(self, *args):
        pass

    # set as modem application incoming message callback function
    def incoming_callback(self, msg):
        if self.incoming is not None:
            self.incoming(msg)

    # set as modem application outgoing message status callback function
    def outgoing_callback(self, msg):
        if self.outgoing is not None:
            self.outgoing(msg)

    # set as modem application station activity callback function
    # spots arg to be type list
    def spots_callback(self, spots):
        if self.spots is not None:
            self.spots(spots)

    # set as modem application inbox activity callback function
    # msgs arg to be type list
    def inbox_callback(self, msgs):
        if self.inbox is not None:
            self.inbox(msgs)
        
    # update modem application setting
    # return True if modem restart required
    def update_callsign(self, *args):
        pass
        
    # update modem application setting
    # return True if modem restart required
    def update_freq(self, *args):
        pass
        
    # update modem application setting
    # return True if modem restart required
    def update_grid(self, *args):
        pass
        
    # update modem application setting
    # return True if modem restart required
    def update_speed(self, *args):
        pass
        
    # update modem application setting
    # return True if modem restart required
    def update_heartbeat(self, *args):
        pass
        
    # update modem application setting
    # return True if modem restart required
    def update_inbox(self, *args):
        pass
            
#    def process_incoming(self, msg):
#        if not self.encryption:
#            return msg
#        
#        msg.set('encrypted', True)
#            
#        try:
#            msg.set('text', self._identity.decrypt(msg.text))
#        except ValueError:
#            msg.set('error', 'decrypt failed')
#            
#        return msg
#    
#    def process_outgoing(self, msg):
#        if not self.encryption:
#            return msg
#        
#        # msg.text is overwritten when setting msg.value
#        text = msg.text
#
#        try:
#            msg.set('value', self.idm.encrypt(msg.value, msg.destination))
#            msg.set('encrypted', True)
#        except LookupError:
#            msg.set('error', 'public key unavailable')
#
#        # restore msg.text
#        msg.set('text', text)
#            
#        return msg
