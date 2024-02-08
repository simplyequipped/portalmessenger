from portalmessenger.modem import BaseModem
import pyjs8call


class JS8CallModem(BaseModem):
    def __init__(self, callsign=None, headless=True):
        super().__init__('JS8Call')
        self.callsign = callsign
        self.headless = headless

        # initialize pyjs8call client and callback functions
        self.js8call = pyjs8call.Client()
        self.js8call.callback.register_incoming(self.incoming_callback)
        self.js8call.callback.register_spots(self.spots_callback)
        self.js8call.callback.outgoing = self.outgoing_callback
        self.js8call.callback.inbox = self.inbox_callback

        if 'Portal' not in self.js8call.settings.get_profile_list():
            # copy new profile from default profile
            self.js8call.config.create_new_profile('Portal')
            
        self.js8call.settings.set_profile('Portal')
        # disable idle timeout
        self.js8call.settings.set_idle_timeout(0)
        self.js8call.settings.set_distance_units_miles(True)
        
        if self.callsign not in (None, ''):
            self.js8call.settings.set_station_callsign(self.callsign)
                
    def start(self):
        if not self.js8call.online:
            self.js8call.start(headless = self.headless)

    def stop(self, *args):
        self.js8call.stop()

    def restart(self):
        self.js8call.restart()

    def online(self):
        return self.js8call.online

    def send(self, destination, text):
        #TODO consider moving command handling to pyjs8call
        # check for command in text
        # sort decending by command length to avoid matching a partial command
        msg_cmds = sorted(pyjs8call.Message.COMMANDS, key=len, reverse=True)

        cmd_found = False
        for cmd in msg_cmds:
            if text.startswith(cmd):
                cmd_found = True
                text = text.replace(cmd, '').strip()
                if len(text) == 0:
                    text = None
                break

        if cmd_found:
            return self.js8call.send_directed_command_message(destination, cmd, text)
            
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

    def get_call_activity(self, age=None):
        call_activity = self.js8call.get_call_activity(age = age)

        for activity in call_activity.copy():
            # pre-process and set empty values to None for easier ui handling
            call_activity[activity]['grid'] = call_activity[activity]['grid'] if call_activity[activity]['grid'] not in [None, ''] else None
            call_activity[activity]['distance'] = '{0[0]:,} {0[1]}'.format(call_activity[activity]['distance']) if call_activity[activity]['distance'][0] not in [None, ''] else None
            call_activity[activity]['snr'] = '{}dB'.format(call_activity[activity]['snr']) if call_activity[activity]['snr'] not in [None, ''] else None
            call_activity[activity]['hearing'] = ', '.join(call_activity[activity]['hearing']) if len(call_activity[activity]['hearing']) > 0 else None
            call_activity[activity]['heard_by'] = ', '.join(call_activity[activity]['heard_by']) if len(call_activity[activity]['heard_by']) > 0 else None

        return call_activity
                
    # set as modem application incoming message callback function
    # msg arg to be type pyjs8call.Message
    def incoming_callback(self, msg):
        if msg.destination not in self.js8call.identities():
            return
    
        super().incoming_callback(msg)

    # set as modem application outgoing message status callback function
    # msg arg to be type pyjs8call.Message
    def outgoing_callback(self, msg):
        super().outgoing_callback(msg)

    # set as modem application station activity callback function
    # spots arg to be type list
    def spots_callback(self, spots):
        super().spots_callback(spots)

    # set as modem application inbox activity callback function
    # msgs arg to be type list
    def inbox_callback(self, msgs):
        super().inbox_callback(msgs)
        
    # update modem application setting
    # return True if modem restart required
    def update_callsign(self, callsign):
        self.js8call.settings.set_station_callsign(callsign)
        # restart required
        return True
        
    # update modem application setting
    # return True if modem restart required
    def update_freq(self, freq):
        self.js8call.settings.set_freq( int(freq) )
        
    # update modem application setting
    # return True if modem restart required
    def update_grid(self, grid):
        self.js8call.settings.set_station_grid(grid)
        
    # update modem application setting
    # return True if modem restart required
    def update_speed(self, speed):
        self.js8call.settings.set_speed(speed)
        # restart required
        return True
        
    # update modem application setting
    # return True if modem restart required
    def update_heartbeat(self, heartbeat):
        if heartbeat == 'enable':
            self.js8call.heartbeat.enable()
        else:
            self.js8call.heartbeat.disable()
        
    # update modem application setting
    # return True if modem restart required
    def update_inbox(self, inbox):
        if inbox == 'enable':
            self.js8call.inbox.enable()
        if inbox == 'query allcall':
            self.js8call.inbox.enable(query = True)
        else:
            self.js8call.inbox.disable()
