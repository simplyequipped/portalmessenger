import pyjs8call


class JS8CallModem:
    def __init__(self, callsign, freq=None, headless=True):
        self.name = 'js8call'
        self.first_start = True
        self.rx_callback = None
        self.spot_callback = None
        self.tx_complete_callback = None
        self.identities = []

        self.js8call = pyjs8call.Client(headless = headless)

        # set app specific profile
        if 'Portal' not in self.js8call.config.get_profile_list():
            self.js8call.config.create_new_profile('Portal')

        self.js8call.set_config_profile('Portal')

        # set max idle timeout (1440 minutes, 24 hours)
        self.js8call.config.set('Configuration', 'TxIdleWatchdog', 1440)

        # enable autoreply which allows API message tx 
        self.js8call.config.set('Configuration', 'AutoreplyConfirmation', 'true')
        self.js8call.config.set('Configuration', 'AutoreplyOnAtStartup', 'true')

        self.js8call.config.set('Configuration', 'Miles', 'true')

        # handle first Portal app start with callsign = ''
        if callsign != None and callsign != '':
            self.js8call.set_station_callsign(callsign)

        # not critical to set freq here, but js8call will use this on restart
        if freq != None:
            self.js8call.config.set('Common', 'DialFreq', int(freq))

    def start(self):
        if not self.js8call.online:
            self.js8call.start()

            if self.first_start == True:
                self.js8call.register_rx_callback(self.rx, pyjs8call.Message.RX_DIRECTED)
                self.js8call.tx_monitor.set_tx_complete_callback(self.tx_complete)
                self.js8call.spot_monitor.set_new_spot_callback(self.spotted)
                self.identities.extend(self.js8call.config.get_groups())

                self.first_start = False

            callsign = self.js8call.get_station_callsign()
            if callsign not in self.identities:
                self.identities.append(callsign)

    def stop(self):
        self.js8call.stop()

    def tx(self, msg):
        self.js8call.send_directed_message(msg['to'], msg['text'])
        self.js8call.tx_monitor.monitor(text, identifier = msg['id'])

    def rx(self, msg):
        if msg['to'] not in self.identities:
            return None

        # filter heartbeat messages
        #if 'cmd' in msg.keys() and (msg['cmd'] == 'HEARTBEAT' or msg['cmd'] == 'HEARTBEAT SNR'):
        #    return None

        elif self.rx_callback != None:
            self.rx_callback(msg)

    def spots(self, station=None, since_timestamp=0, from_only=False):
        heard = self.js8call.get_station_spots(station=station, since_timestamp=since_timestamp, from_only=from_only)

        # remove duplicates, keeping the most recent spot
        heard_data = {}
        for station in heard:
            if station['from'] not in heard_data.keys():
                heard_data[station['from']] = station
            elif station['time'] > heard_data[station['from']]:
                heard_data[station['from']] = station

        heard = list(heard_data.values())
                
        # sort by spot timestamp
        if heard != None and len(heard) > 1:
            heard.sort(key = lambda spot: spot['time'])

        return heard

    def spotted(self, spots):
        if self.spot_callback != None:
            self.spot_callback(spots)

    def tx_complete(self, msg_id):
        if self.tx_complete_callback != None:
            self.tx_complete_callback(msg_id)

    def set_rx_callback(self, func):
        self.rx_callback = func

    def set_spot_callback(self, func):
        self.spot_callback = func

    def set_tx_complete_callback(self, func):
        self.tx_complete_callback = func

