# modem allows app ui demo without installing radio modem software

import string
import random
import secrets
import time
import threading


class DemoMessage:
    def __init__(self, msg_type, origin = None, destination = None, text = None):
        # msg_type = 'rx' or 'tx'
        
        self.id = secrets.hex_token(16)
        
        if origin is None:
            self.origin = ''.join(random.choices(string.ascii_uppercase, k=2)) + str(random.randint(1,9)) + ''.join(random.choices(string.ascii_uppercase, k=3))
        else:
            self.origin = origin
        
        if destination is None:
            self.destination = ''.join(random.choices(string.ascii_uppercase, k=2)) + str(random.randint(1,9)) + ''.join(random.choices(string.ascii_uppercase, k=3))
        else:
            self.destination = destination
            
        self.type = msg_type
        self.time = time.time()
        
        if text is None:
            self.text = ''.join(random.choices(string.ascii_lowercase + '     ', k=random.randint(25, 250)))
        else:
            self.text = text
            
        if self.type == 'rx':
            self.status = 'received'
        elif self.type = 'tx':
            self.status = 'queued'
        
        
class DemoModem:
     def __init__(self, callsign):
        self.name = 'demo'
        self.incoming = None
        self.outgoing = None
        self.spots = None
        self.inbox = None
        self.callsign = callsign
        
        thread = threading.Thread(target=self._spots_simulation)
        thread.daemon = True
        thread.start()
        
        thread = threading.Thread(target=self._rx_simulation)
        thread.daemon = True
        thread.start()

    def start(self):
        pass
    
    def stop(self):
        pass

    def restart(self):
        pass

    def online(self):
        return True

    def send(self, destination, text):
        msg = DemoMessage('tx', self.callsign, destination, text)
        
        thread = threading.Thread(target=self._tx_simulation, args=(msg,))
        thread.daemon = True
        thread.start()
        
        return msg

    def get_spots(self, **kwargs):
        all_spots = self.js8call.spots.filter(**kwargs)

        # remove duplicates, keeping the most recent spot
        spots = {}
        for spot in all_spots:
            if spot.origin not in spots:
                spots[spot.origin] = spot
            elif spot.age() > spots[spot.origin].age():
                spots[spot.origin] = spot

        return list(spots.values()).sort()
                
    def incoming_callback(self, msg):
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
            
    def _spots_simulation(self):
        while True:
            time.sleep(random.choice(range(30, 180, 10)))
            
            msg = DemoMessage('rx')
            self.spots_callback(msg)
    
    def _rx_simulation(self):
        while True:
            time.sleep(random.choice(range(60, 180, 10)))
            
            if random.choice([True, False]):
                msg = DemoMessage('rx', destination = self.callsign)
                self.spots_callback(msg)
            
    def _tx_simulation(self, msg):
        time.sleep(random.randint(8, 17))
        msg.status = 'sending'
        self.outgoing_callback(msg)
        
        time.sleep(8)
        msg.status = 'sent'
        self.outgoing_callback(msg)
      
