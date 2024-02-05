import time

from flask import current_app

from portalmessenger import db
from portalmessenger import message



# incoming directed message callback
#TODO confirm: this function does not have the flask request context because it is called via callback
def incoming_message(msg):
    msg = message.process_message(msg)

    if msg['origin'] == current_app.config['ACTIVE_CHAT_USER']:
    # pass messages for active chat to client side
        socketio.emit('msg', [msg])

    unread = bool( db.get_user_unread_message_count(msg['origin']) )

    conversation = {
        'username': msg['origin'], 
        'time': msg['time'],
        'unread': unread
    }

    # pass conversation to client side
    socketio.emit('conversation', [conversation])

# new spots callback
def new_spots(spots):
    spots = [{'username': spot.origin, 'time': spot.timestamp} for spot in spots]
    socketio.emit('spot', spots)
    
# outgoing message status change callback
def outgoing_status(msg):
    # works inconsistently without this delay, root cause unknown
    time.sleep(0.001)
    db.update_outgoing_message_status(msg)
    socketio.emit('update-tx-status', {'id': msg.id, 'status': msg.status})


if __name__ == 'main':
    #TODO
    #app = portalmessenger.create_app()
    #app.run(host='0.0.0.0')
    #socketio = SocketIO(app)
    # TODO turn off debugging in production
    socketio.run(app, debug=True, host='0.0.0.0')

    app.config['MODEM'].incoming = incoming_message
    app.config['MODEM'].spots = new_spots
    app.config['MODEM'].outgoing = outgoing_status
    
