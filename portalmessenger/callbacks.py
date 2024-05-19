import time

from flask import current_app

from portalmessenger import db
from portalmessenger import message
from portalmessenger.websockets import socketio


# incoming directed message callback
def incoming_message(msg):
    msg = message.process_message(msg)

    if msg['destination'].startswith('@') and msg['destination'] == current_app.config['ACTIVE_CHAT_USER']:
        # pass messages for active chat to client side
        socketio.emit('msg', [msg])
        socketio.emit('heard-user', msg['time'])
    elif msg['origin'] == current_app.config['ACTIVE_CHAT_USER']:
        # pass messages for active chat to client side
        socketio.emit('msg', [msg])

    if msg['destination'].startswith('@'):
        username = msg['destination']
    else:
        username = msg['origin']

    unread = bool( db.get_user_unread_message_count(username) )

    conversation = {
        'username': username, 
        'time': msg['time'],
        'unread': unread
    }

    # pass conversation to client side
    socketio.emit('conversation', [conversation])

# new spots callback
def new_spots(spots):
    spots = [{'username': spot.origin, 'time': spot.timestamp} for spot in spots]
    socketio.emit('spot', spots)

    username = current_app.config['ACTIVE_CHAT_USER']
    if username is not None and username in [spot['username'] for spot in spots]:
        # update current chat last heard timestamp
        socketio.emit('heard-user', spots[username]['timestamp'])
    
# outgoing message status change callback
def outgoing_status(msg):
    # works inconsistently without this delay, root cause unknown
    time.sleep(0.001)
    db.update_outgoing_message_status(msg)
    socketio.emit('update-tx-status', {'id': msg.id, 'status': msg.status})
    
