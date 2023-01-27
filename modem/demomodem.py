# modem allows app ui demo without installing radio modem applications

class DemoModem:
    def __init__(self, callsign, freq=None, headless=None):
        self.rx_callback = None
        self.name = 'null'

    def start(self):
        pass

    def stop(self):
        pass

    def tx(self, msg):
        # simulate tx
        time.sleep(2)
        # indicate tx complete
        self.tx_complete(msg)
        # simulate response
        time.sleep(2)
        # simulate rx
        self.rx(msg)

    def rx(self, msg):
        if self.rx_callback != None:
            self.rx_callback(msg)

    def spots(self, station=None, since_timestamp=0, from_only=False):
        return []

    def spotted(self, spots):
        pass

    def tx_complete(self, msg):
        pass

    def set_rx_callback(self, func):
        self.rx_callback = func

    def set_spot_callback(self, func):
        pass

    def set_tx_complete_callback(self, func):
        pass
      
    def set_tx_failed_callback(self, func):
        pass
      
