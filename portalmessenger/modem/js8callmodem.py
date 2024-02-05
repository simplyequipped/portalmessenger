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
        self.js8call.callback.outgoing = self.outgoing_callback
        self.js8call.callback.spots = self.spots_callback
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
            call_activity[activity]['snr'] = '{}dB'.format(call_activity[activity]['snr'])
            call_activity[activity]['hearing'] = ', '.join(call_activity[activity]['hearing'])
            call_activity[activity]['heard_by'] = ', '.join(call_activity[activity]['heard_by'])
            call_activity[activity]['distance'] = '{0[0]:,} {0[1]}'.format(call_activity[activity]['distance'])

        return call_activity
                
    def incoming_callback(self, msg):
        if msg.destination not in self.js8call.identities():
            return
    
        parent().incoming_callback(msg)

    def outgoing_callback(self, msg):
        parent().outgoing_callback(msg)

    def spots_callback(self, spots):
        parent().spots_callback(spots)

    def inbox_callback(self, msgs):
        parent().inbox_callback(msgs)
    
