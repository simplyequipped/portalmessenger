import pyjs8call


class JS8CallModem:
    def __init__(self, callsign, headless=True):
        self.name = 'js8call'
        self.first_start = True
        self.incoming = None
        self.outgoing = None
        self.spots = None
        self.inbox = None

        self.js8call = pyjs8call.Client(headless = headless)
        self.js8call.callback.register_incoming(self.incoming_callback)
        self.js8call.callback.spots = self.spots_callback
        self.js8call.callback.inbox = self.inbox_callback

        # set app specific profile
        if 'Portal' not in self.js8call.config.get_profile_list():
            self.js8call.config.create_new_profile('Portal')

        self.js8call.set_config_profile('Portal')

        # set max idle timeout (1440 minutes, 24 hours)
        self.js8call.config.set('Configuration', 'TxIdleWatchdog', 1440)
        self.js8call.config.set('Configuration', 'Miles', 'true')

        # handle first Portal app start with callsign = ''
        if callsign not in (None, ''):
            self.js8call.set_station_callsign(callsign)

    def start(self):
        if not self.js8call.online:
            self.js8call.start()

    def stop(self):
        self.js8call.stop()

    def restart(self):
        self.js8call.restart()

    def online(self):
        return self.js8call.online

    def send(self, destination, text):
        return self.js8call.send_directed_message(destination, text)

    def get_spots(self, station=None, group=None, age=0):
        all_spots = self.js8call.get_station_spots(station=station, group=group, age=age)

        # remove duplicates, keeping the most recent spot
        spots = {}
        for spot in all_spots:
            if spot.origin not in spots:
                spots[spot.origin] = spot
            elif spot.age() > spots[spot.origin].age():
                spots[spot.origin] = spot

        return list(spot_data.values()).sort()
                
    def incoming_callback(self, msg):
        if msg.destination not in self.identities:
            return None

        elif self.rx_callback != None:
            self.rx_callback(msg)

    def outgoing_callback(self, msg):
        if self.outgoing is not None:
            self.outgoing(msg)

    def spots_callback(self, spots):
        if self.spots is not None:
            self.spots(spots)

    def inbox_callback(self, msgs):
        if self.inbox is not None:
            self.inbox(msgs)
            
