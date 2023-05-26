# modem allows app ui demo without installing radio modem software

import string
import random
import secrets
import time
import threading


class DemoMessage:
    def __init__(self, msg_type, origin = None, destination = None, text = None):
        # msg_type = 'rx' or 'tx'
        
        self.id = secrets.token_hex(16)
        self.type = msg_type
        self.time = time.time()
        self.timestamp = time.time()
        
        if origin is None:
            self.origin = ''.join(random.choices(string.ascii_uppercase, k=2)) + str(random.randint(1,9)) + ''.join(random.choices(string.ascii_uppercase, k=3))
        else:
            self.origin = origin.upper()
        
        if destination is None:
            self.destination = ''.join(random.choices(string.ascii_uppercase, k=2)) + str(random.randint(1,9)) + ''.join(random.choices(string.ascii_uppercase, k=3))
        else:
            self.destination = destination.upper()
            
        if text is None:
            self.text = ''.join(random.choices(string.ascii_uppercase + ' '*10, k=random.randint(25, 250)))
        else:
            self.text = text.upper()
            
        if self.type == 'rx':
            self.status = 'received'
        elif self.type == 'tx':
            self.status = 'queued'
        
        
class DemoModem:
    def __init__(self, callsign):
        self.name = 'demo'
        self.incoming = None
        self.outgoing = None
        self.spots = None
        self.inbox = None
        self.callsign = callsign
        self._spots = []
        
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

    def get_spots(self, origin=None, age=0):
        spots = []

        for spot in self._spots:
            if (
                (age == 0 or (time.time() - spot.time) <= age) and
                (origin is None or origin.upper() == spot.origin)
            ):
                spots.append(spot)

        return spots
                
    def incoming_callback(self, msg):
        if self.incoming != None:
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
            
            new_spots = [DemoMessage('rx') for i in range(random.randint(0, 2))]
            self._spots.extend(new_spots)
            self.spots_callback(new_spots)
    
    def _rx_simulation(self):
        while True:
            time.sleep(random.choice(range(30, 180, 10)))
            
            if random.choice([True, False]):
                msg = DemoMessage('rx', destination = self.callsign)
                self._spots.append(msg)
                self.spots_callback([msg])
                self.incoming_callback(msg)
            
    def _tx_simulation(self, msg):
        time.sleep(random.randint(8, 17))
        msg.status = 'sending'
        self.outgoing_callback(msg)
        
        time.sleep(8)
        msg.status = 'sent'
        self.outgoing_callback(msg)
      
