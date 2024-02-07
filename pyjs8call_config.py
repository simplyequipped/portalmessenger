# pyjs8call configuration parameters
#   - config parameters must match the name of a pyjs8call.settings function
#   - config parameters set to a value will pass that value to the corresponding pyjs8call.settings function
#   - config parameters set to None will call the corresponding pyjs8call.settings function without any arguments
#   - all config parameters are implemented before starting pyjs8call (i.e. in the js8call config file, see pyjs8call.confighandler)
#
# see pyjs8call.settings docs for available functions: https://simplyequipped.github.io/pyjs8call/pyjs8call/client.html#Settings

SET_HEARTBEAT_INTERVAL = 15 # minutes
ENABLE_HEARTBEAT_ACKNOWLEDGEMENTS = None
ENABLE_MULTI_DECODE = None
ENABLE_AUTOREPLY_STARTUP = None
DISABLE_AUTOREPLY_CONFIRMATION = None # autoreply confirmation box is inaccessible when running headless
SET_IDLE_TIMEOUT = 0 # disable idle timeout
SET_DISTANCE_UNITS = 'miles'
#SET_STATION_INFO = ''
#APPEND_PYJS8CALL_TO_STATION_INFO = None
#SET_PRIMARY_HIGHLIGHT_WORDS = []
#SET_SECONDARY_HIGHLIGHT_WORDS = []
