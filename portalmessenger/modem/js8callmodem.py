from portalmessenger.modem import BaseModem
import pyjs8call


class JS8CallModem(BaseModem):
    def __init__(self):
        super().__init__('JS8Call')
        # initialize pyjs8call client and callback functions
        self.js8call = pyjs8call.Client()
        # store previous js8call config profile
        self.js8call.callback.register_incoming(self.incoming_callback)
        self.js8call.callback.register_spots(self.spots_callback)
        self.js8call.callback.outgoing = self.outgoing_callback
        self.js8call.callback.inbox = self.inbox_callback
        self.js8call.callback.restart_complete = self.restart_complete_callback

        if 'Portal' not in self.js8call.settings.get_profile_list():
            # copy new profile from default profile
            self.js8call.config.create_new_profile('Portal')
            
        # set app specific config profile for JS8Call, restore previous profile on exit
        self.js8call.settings.set_profile('Portal', restore_on_exit=True)
                
    def start(self, *args, **kwargs):
        if not self.js8call.online:
            self.js8call.start(*args, **kwargs)

    def stop(self, *args):
        # pyjs8call writes config to file on stop
        self.js8call.stop()

    def restart(self):
        self.js8call.restart()

    def restart_async(self):
        self.js8call.restart_when_inactive()

    def online(self):
        return self.js8call.online

    def send(self, destination, text):
        # moved automatic command handling to pyjs8call
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

    def get_call_activity(self, age=None, hearing_age=None):
        call_activity = self.js8call.get_call_activity_from_spots(age = age, hearing_age = hearing_age)

        for i in range(len(call_activity)):
            # pre-process and set empty values to None for easier ui handling
            call_activity[i]['grid'] = call_activity[i]['grid'] if call_activity[i]['grid'] not in (None, '') else None
            call_activity[i]['distance'] = '({:,} {})'.format(call_activity[i]['distance'], call_activity[i]['distance_units']) if call_activity[i]['distance'] not in (None, '') else None
            call_activity[i]['snr'] = '{} dB'.format(call_activity[i]['snr']) if call_activity[i]['snr'] not in (None, '') else None
            call_activity[i]['hearing'] = ', '.join(call_activity[i]['hearing']) if len(call_activity[i]['hearing']) > 0 else None
            call_activity[i]['heard_by'] = ', '.join(call_activity[i]['heard_by']) if len(call_activity[i]['heard_by']) > 0 else None

        return call_activity
        
    def get_propagation_data(self, max_age=30):
        propagation_data = self.js8call.propagation.grids_median_dataset(max_age = max_age, normalize_snr=True)
        propagation_data = [[lat, lon, snr] for grid, lat, lon, snr, timestamp in propagation_data]

        station_grid = self.js8call.settings.get_station_grid()
        station_grid = station_grid if station_grid not in (None, '') else 'FM18lv' # default to Washington D.C. USA
        station = list(self.js8call.grid_to_lat_lon(station_grid))
        data = {
            'propagation': propagation_data,
            'station': station
        }

        return data

    def get_groups(self):
        return ', '.join(self.js8call.settings.get_groups_list())
                
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

    # set as modem application restart complete callback function
    def restart_complete_callback(self):
        super().restart_complete_callback()
        
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
        if inbox == 'query @ALLCALL':
            self.js8call.inbox.enable(query=True)
        else:
            self.js8call.inbox.disable()

    def update_groups(self, groups):
        self.js8call.settings.set_groups(groups)
