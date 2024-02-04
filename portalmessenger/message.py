from flask import current_app

from portalmessenger import db


# msg = pyjs8call.Message object
def process_message(msg):
    msg = {
        'id': msg.id,
        'origin': msg.origin,
        'destination': msg.destination,
        'type': msg.type[0:2].lower(), # RX.DIRECTED = 'rx', TX.SEND_MESSAGE = 'tx'
        'time': msg.timestamp,
        'text': msg.text,
        'encrypted': msg.get('encrypted'),
        'error': msg.error,
        'unread': False,
        'status': msg.status
        }

    if msg['type'] == 'rx' and msg['origin'] != current_app.config['ACTIVE_CHAT_USER']:
        msg['unread'] = True

    if msg['type'] == 'tx':
        msg['origin'] = db.get_setting_value('callsign')

        if msg['status'] != 'failed':
            msg['status'] = 'queued'
    
    db.store_message(msg)

    return msg

