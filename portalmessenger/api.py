'''
API endpoints for Portal Messenger backend
Provides REST API for messages, conversations, and settings
'''


from datetime import datetime
import json

from starlette.routing import Route
from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException
from tinydb import Query

from .database import get_database


async def get_conversation(request):
    '''Get conversation with specified callsign'''
    callsign = request.path_params['callsign']
    
    # get query parameters
    limit = int(request.query_params.get('limit', 50))
    before = request.query_params.get('before')
    
    # get local callsign from settings
    db = get_database()
    local_setting = db.get_setting('callsign')
    
    if not local_setting:
        raise HTTPException(status_code=500, detail='Local callsign not configured')
    
    local_callsign = local_setting['value']
    messages = db.get_conversation(local_callsign, callsign, limit=limit)
    
    # filter by timestamp if provided
    if before:
        try:
            before_dt = datetime.fromisoformat(before.replace('Z', '+00:00'))
            messages = [m for m in messages if datetime.fromisoformat(m['time']) < before_dt]
            messages = messages[-limit:] if len(messages) > limit else messages
        except ValueError:
            raise HTTPException(status_code=400, detail='Invalid timestamp format')
    
    return JSONResponse(messages)


async def get_conversations(request):
    '''Get all conversations (callsigns/groups with messages)'''
    db = get_database()
    local_setting = db.get_setting('callsign')
    
    if not local_setting:
        raise HTTPException(status_code=500, detail='Local callsign not configured')
    
    local_callsign = local_setting['value']
    all_messages = db.get_all_messages()
    
    conversations_map = {}
    
    for message in all_messages:
        if message['destination'].startswith('@'):
            # group conversation
            conversation_with = message['destination']
        elif message['origin'] == local_callsign:
            # outgoing message - conversation is with destination
            conversation_with = message['destination']
        else:
            # incoming message - conversation is with origin
            conversation_with = message['origin']
        
        if conversation_with not in conversations_map:
            conversations_map[conversation_with] = {
                'callsign': conversation_with,
                'lastMessageTime': message['time'],
                'unreadCount': 0,
                'isOnline': False  # used by front end
            }
        else:
            # keep most recent message time
            if message['time'] > conversations_map[conversation_with]['lastMessageTime']:
                conversations_map[conversation_with]['lastMessageTime'] = message['time']
            
        if message.get('unread', False):
            conversations_map[conversation_with]['unreadCount'] += 1
    
    # sort by last message time
    conversations_list = list(conversations_map.values())
    conversations_list.sort(key=lambda c: c['lastMessageTime'], reverse=True)
    
    return JSONResponse(conversations_list)


async def get_conversation_unread_count(request):
    '''Get count of conversations with unread messages'''
    db = get_database()
    local_setting = db.get_setting('callsign')

    if not local_setting:
        raise HTTPException(status_code=500, detail='Local callsign not configured')
    
    Message = Query()
    unread_messages = db.messages.search(Message.unread == True)
    local_callsign = local_setting['value']
    
    # group by conversation
    conversations = set()
    for message in unread_messages:
        if message['destination'].startswith('@'):
            # group message are always addressed to the group
            conversations.add(message['destination'])
        elif message['origin'] != local_callsign:
            # message from a callsign
            conversations.add(message['origin'])
    
    return JSONResponse({'count': len(conversations)})


async def get_conversation_unread_status(request):
    '''Get true/false if conversation has unread messages'''
    callsign = request.path_params['callsign']
    
    db = get_database()
    local_setting = db.get_setting('callsign')

    if not local_setting:
        raise HTTPException(status_code=500, detail='Local callsign not configured')
    
    local_callsign = local_setting['value']
    messages = db.get_conversation(local_callsign, callsign)
    has_unread = any(message.get('unread', False) for message in messages)
    
    return JSONResponse({'unread': has_unread})


async def mark_conversation_read(request):
    '''Mark all messages in conversation as read'''
    callsign = request.path_params['callsign']
    
    db = get_database()
    local_setting = db.get_setting('callsign')

    if not local_setting:
        raise HTTPException(status_code=500, detail='Local callsign not configured')
    
    local_callsign = local_setting['value']
    messages = db.get_conversation(local_callsign, callsign)

    updated_count = 0
    for message in messages:
        if message.get('unread', False):
            if db.mark_message_read(message['id']):
                updated_count += 1
    
    return JSONResponse({'updated': updated_count})


async def delete_conversation(request):
    '''Delete all messages to/from specified callsign'''
    callsign = request.path_params['callsign']
    
    db = get_database()
    local_setting = db.get_setting('callsign')

    if not local_setting:
        raise HTTPException(status_code=500, detail='Local callsign not configured')
    
    local_callsign = local_setting['value']
    messages = db.get_conversation(local_callsign, callsign)

    deleted_count = 0
    for message in messages:
        if db.delete_message(message['id']):
            deleted_count += 1
    
    return JSONResponse({'deleted': deleted_count})


async def get_message(request):
    '''Get specific message by ID'''
    message_id = request.path_params['id']
    
    db = get_database()
    message = db.get_message(message_id)
    
    if not message:
        raise HTTPException(status_code=404, detail='Message not found')
    
    return JSONResponse(message)


async def create_message(request):
    '''Store new message'''
    try:
        body = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail='Invalid JSON')
    
    message_fields = ['id', 'origin', 'destination', 'type', 'time', 'text', 'status', 'error']
    message_data = {field: body.get(field, None) for field in message_fields}
    message_data['time'] = datetime.fromtimestamp(body['timestamp']).isoformat()
    # simplify pyjs8call message types (ex. 'RX.DIRECTED' -> 'rx', 'TX.SEND_MESSAGE' -> 'tx')
    message_data['type'] = message_data['type'][:2].lower()
    
    db = get_database()
    message_id = db.create_message(message_data)
    
    message = db.get_message(message_data['id'])
    return JSONResponse(message, status_code=201)


async def update_message(request):
    '''Partial update of message'''
    message_id = request.path_params['id']
    
    try:
        body = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail='Invalid JSON')
    
    db = get_database()
    
    if not db.get_message(message_id):
        raise HTTPException(status_code=404, detail='Message not found')
    
    success = db.update_message(message_id, body)
    if not success:
        raise HTTPException(status_code=500, detail='Failed to update message')
    
    message = db.get_message(message_id)
    return JSONResponse(message)


async def delete_message(request):
    '''Delete specific message'''
    message_id = request.path_params['id']

    db = get_database()
    
    if not db.get_message(message_id):
        raise HTTPException(status_code=404, detail='Message not found')
    
    success = db.delete_message(message_id)
    if not success:
        raise HTTPException(status_code=500, detail='Failed to delete message')
    
    return JSONResponse({'deleted': True})


async def get_all_settings(request):
    '''Get all settings'''
    db = get_database()
    settings = db.get_all_settings()
    return JSONResponse(settings)


async def get_setting(request):
    '''Get specific setting'''
    key = request.path_params['key']
    
    db = get_database()
    setting = db.get_setting(key)
    
    if not setting:
        raise HTTPException(status_code=404, detail='Setting not found')
    
    return JSONResponse(setting)


async def update_setting(request):
    '''Update specific setting value'''
    key = request.path_params['key']
    
    try:
        body = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail='Invalid JSON')
    
    if 'value' not in body:
        raise HTTPException(status_code=400, detail='Missing value field')
    
    db = get_database()
    setting = db.update_setting(key, body['value'])
    
    if not setting:
        raise HTTPException(status_code=404, detail='Setting not found')
    
    return JSONResponse(setting)


async def update_multiple_settings(request):
    '''Update multiple settings at once'''
    try:
        body = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail='Invalid JSON')
    
    db = get_database()
    updated_settings = []
    
    for key, value in body.items():
        setting = db.update_setting(key, value)
        if setting:
            updated_settings.append(setting)
    
    return JSONResponse(updated_settings)


async def get_status(request):
    '''Basic health check + app status'''
    return JSONResponse({
        'status': 'ok',
        'service': 'Portal Messenger Database Server',
        'timestamp': datetime.now().isoformat()
    })


# route definitions
api_routes = [
    Route('/conversations', get_conversations, methods=['GET']),
    Route('/conversation/{callsign}', get_conversation, methods=['GET']),
    Route('/conversation/unread', get_conversation_unread_count, methods=['GET']),
    Route('/conversation/unread/{callsign}', get_conversation_unread_status, methods=['GET']),
    Route('/conversation/read/{callsign}', mark_conversation_read, methods=['PATCH']),
    Route('/conversation/{callsign}', delete_conversation, methods=['DELETE']),
    
    Route('/messages/{id}', get_message, methods=['GET']),
    Route('/messages', create_message, methods=['POST']),
    Route('/messages/{id}', update_message, methods=['PATCH']),
    Route('/messages/{id}', delete_message, methods=['DELETE']),
    
    Route('/settings', get_all_settings, methods=['GET']),
    Route('/settings/{key}', get_setting, methods=['GET']),
    Route('/settings/{key}', update_setting, methods=['PUT']),
    Route('/settings', update_multiple_settings, methods=['PATCH']),
    
    Route('/status', get_status, methods=['GET']),
]
