import time
import RNS
from FldigiInterface import FldigiInterface

def rx_packet(message, packet):
    print(message)

rns = RNS.Reticulum()
print('Reticulum started')

interface = FldigiInterface(RNS.Transport, 'xml-rpc', '127.0.0.1', 7362, headless=True)
RNS.Transport.interfaces.append(interface)

identity = RNS.Identity()
dest = RNS.Destination(identity, RNS.Destination.IN, RNS.Destination.SINGLE, 'portal', 'fldigi')
dest.set_packet_callback(rx_packet)
dest.announce()
print('announce sent')

