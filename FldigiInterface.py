from time import sleep
import sys
import serial
import threading
import time
import RNS
from RNS.Interfaces.Interface import Interface
import pyfldigi

# Notes:
#   Fldigi configuration (Configure -> UI -> User Inteface)
#   should be set to not have any exit prompts so we can cleanly
#   stop the application (successive starts without stopping old
#   instances results in multiple instances, and running multiple
#   instances of fldigi causes audio interface errors)


class Fldigi():

    # default host: 127.0.0.1
    # default port: 7362
    def __init__(self, host, port, headless):
        self.host = host
        self.port = port
        self.headless = headless

        # start fldigi application
        self.app = pyfldigi.ApplicationMonitor(self.host, self.port)
        # start application in headless mode, with no stderr output
        self.app.start(headless=self.headless, debug=0)
        # start fldigi xml-rpc client
        self.client = pyfldigi.Client(self.host, self.port)

        # set reasonable defaults
        self.client.modem.name = "BPSK31"
        self.client.modem.carrier = 1250
        self.client.main.squelch = True
        self.client.main.squelch_level = 2
        self.client.main.rsid = True
        self.client.main.afc = True
        self.client.main.rx()


    #TODO return true even if pyfldigi.app.start() didn't start the application
    def running(self):
        return self.app.is_running()


    def stop(self):
        self.app.stop()


    def __tx(self, data, timeout):
        self.client.main.send(data, timeout=timeout)
        self.client.main.rx()


    # call modem tx with a thread so we can wait and set modem
    # to rx after tx is complete, but without blocking
    def tx(self, data, timeout=30):
        thread = threading.Thread(target=self.__tx, args=(data, timeout))
        thread.setDaemon(True)
        thread.start()


    # get new received text since last query
    def rx(self):
        return self.client.text.get_rx_data()


    def __str__(self):
        return "<fldigi.xmlrpc @ " + str(self.host) + ":"+ str(self.port) +">"


    def __del__(self):
        self.stop()


# --- following code based on Reticulum SerialInterface --- #


class HDLC():
    # HDLC-ish packet framing
    # flags are unconventional, but multiple bytes prevents rx noise
    # from simulating a single byte flag
    START             = b"|->"
    END               = b"<-|"


class FldigiInterface(Interface):
    #TODO should this be changed?
    MAX_CHUNK = 32768

    owner    = None
    host     = None
    port     = None
    modem    = None

    #TODO remove headless parameter
    def __init__(self, owner, name, host, port, headless, outgoing = True):
        self.rxb = 0
        self.txb = 0
        
        self.serial   = None
        self.owner    = owner
        self.name     = name
        self.host     = host
        self.port     = port
        self.OUT      = outgoing
        self.timeout  = 100
        self.online   = False

        try:
            #TODO remove headless parameter
            self.modem = Fldigi(self.host, self.port, headless)
        except Exception as e:
            RNS.log("Could not connect to fldigi for interface " + str(self), RNS.LOG_ERROR)
            raise e

        if self.modem.running():
            #TODO does this need adjusted?
            sleep(0.5)
            thread = threading.Thread(target=self.readLoop)
            thread.setDaemon(True)
            thread.start()
            self.online = True
            RNS.log(str(self) + " is now running")
        else:
            raise IOError("Could not start fldigi")


    def processIncoming(self, data):
        self.rxb += len(data)            
        self.owner.inbound(data, self)


    def processOutgoing(self, data):
        if self.online:
            data = HDLC.START + data + HDLC.END
            self.modem.tx(data)
            self.txb += len(data)
            #TODO how to confirm data was sent?
            #if written != len(data):
                #raise IOError("Serial interface only wrote "+str(written)+" bytes of "+str(len(data)))


    def readLoop(self):
        try:
            data_buffer = b""

            while self.online:
                # retrieve the next bit of received from the modem
                # (only returns new data since last request)
                data_buffer += self.modem.rx()

                if HDLC.START in data_buffer:
                    if HDLC.END in data_buffer:
                        # start and stop delimiters found, capture the substring
                        start = data_buffer.find(HDLC.START) + len(HDLC.START)
                        end = data_buffer.find(HDLC.END, start)
                        if end > start:
                            data = data_buffer[start:end]
                            # remove received data from the buffer
                            data_buffer = data_buffer[end+len(HDLC.END):]
                            
                            if len(data) <= RNS.Reticulum.MTU:
                                # if we are under the max packet length, receive data
                                self.processIncoming(data)
                            else:
                                # if we are over the max packet lenth, drop it and
                                # carry on my wayward son
                                pass
                        else:
                            # if we are getting partial packets and delimiters
                            # are getting mixed up, remove the bad data from
                            # the beginning of the buffer
                            data_buffer = data_buffer[start+len(HDLC.START):]
                    else:
                        # if the buffer is over the max packet length, remove data up to
                        # the last start delimiter in the buffer
                        if len(data_buffer) > RNS.Reticulum.MTU:
                            data_buffer = data_buffer[data_buffer.rfind(HDCL.START):]
                else:
                    # avoid missing a start delimiter split over multiple loop iterations
                    if len(data_buffer) > 10 * len(HDLC.START):
                        data_buffer = b""

                # simmer down
                time.sleep(1)

        except Exception as e:
            self.online = False
            RNS.log("A fldigi xmlrpc error occurred, the contained exception was: "+str(e), RNS.LOG_ERROR)
            RNS.log("The interface "+str(self)+" experienced an unrecoverable error and is being torn down. Restart Reticulum to attempt to open this interface again.", RNS.LOG_ERROR)

            if RNS.Reticulum.panic_on_interface_error:
                RNS.panic()


    def __str__(self):
        return "FldigiInterface["+self.name+"]"





