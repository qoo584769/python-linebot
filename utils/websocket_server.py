import asyncio
import datetime
import json
import os

import websockets
from bson import ObjectId
from pymongo import UpdateOne

from models.db_client import MongoDBClient

db = MongoDBClient()
users_collection = db.database['users']
messages_collection = db.database['messages']
rooms_collection = db.database['rooms']
friends_collection = db.database['friends']

user_id = None
user_email = None
# 儲存連接的用戶
connected_clients = {}
# 儲存房間及其用戶
rooms = {}


async def start_websocket_server():
	port = int(os.environ.get('PORT', 8080))
	print(port)
	async with websockets.serve(echo, '', port):
		print('ws伺服器啟動成功')
		# 永遠等待
		await asyncio.Future()


async def echo(websocket):
	path = websocket.request.path
	room_id = path.strip('/')
	if room_id not in rooms:
		rooms[room_id] = []
	rooms[room_id].append(websocket)

	try:
		async for message in websocket:
			message_data = json.loads(message)

			connected_clients[message_data.get('user_email')] = websocket

			await switch(message_data, websocket, room_id)

	finally:
		rooms[room_id].remove(websocket)
		if not rooms[room_id]:
			del rooms[room_id]
		if connected_clients[message_data.get('user_email')]:
			del connected_clients[message_data.get('user_email')]


# 判斷傳入類型
async def switch(data, websocket, room_id):
	match data['type']:
		case 'message':
			await send_message(data, websocket, room_id)
		case 'create_room':
			await create_room(data, websocket)
		case 'invite_to_room':
			await invite_to_room(data, websocket)
		case 'get_history':
			await send_history(data, websocket, room_id)
		case 'get_lists':
			await send_lists(data, websocket)
		case 'add_friend':
			await add_friend(data, websocket)
		case 'remove_friend':
			await remove_friend(data, websocket)
		case _:
			print(f'未定義類型 : {data["type"]}')


# 傳送訊息
async def send_message(data, websocket, room_id):
	now = datetime.datetime.now(
		tz=datetime.timezone(datetime.timedelta(hours=8))
	).strftime('%Y/%m/%d %H:%M:%S')

	message = {'author': data['author'], 'content': data['content'], 'time': now}

	db.database.rooms.find_one({'_id': ObjectId(room_id)})
	db.database['rooms'].update_one(
		{'_id': ObjectId(room_id)},
		{'$push': {'messages': message}},
	)

	response = {'type': 'message'} | message
	for user in rooms[room_id]:
		await user.send(json.dumps(response))


# 建立聊天室
async def create_room(data, websocket):
	user = db.database['users'].find_one({'email': data['creator_id']})

	room = {
		'name': data['room_name'],
		'created_by': ObjectId(user['_id']),
		'members': [{'_id': str(user['_id']), 'member_name': user['username']}],
		'room_type': 'group',
		'messages': [],
	}

	room_id = rooms_collection.insert_one(room).inserted_id
	db.database['users'].update_one(
		{'_id': ObjectId(user['_id'])},
		{
			'$push': {
				'rooms': {
					'room_id': str(room_id),
					'room_name': data['room_name'],
					'room_type': 'group',
				}
			}
		},
	)

	await websocket.send(
		json.dumps(
			{
				'type': 'room_created',
				'room_name': data['room_name'],
				'room_id': str(room_id),
				'room_type': 'group',
				'message': '聊天室建立成功！',
			}
		)
	)


async def invite_to_room(data, websocket):
	friend_id = data['friend_id']
	friend_name = data['friend_name']
	friend_email = data['friend_email']
	room_id = data['room_id']
	room_name = data['room_name']

	user_requests = [
		UpdateOne(
			{'_id': ObjectId(friend_id)},
			{
				'$addToSet': {
					'rooms': {
						'room_id': room_id,
						'room_name': room_name,
						'room_type': 'group',
					}
				}
			},
		),
	]

	room_requests = [
		UpdateOne(
			{'_id': ObjectId(room_id)},
			{'$addToSet': {'members': [{'_id': friend_id, 'member_name': friend_name}]}},
		),
	]

	response = {
		'type': 'invited_to_room',
		'friend_id': friend_id,
		'friend_name': friend_name,
		'room_id': room_id,
		'room_name': room_name,
		'room_type': 'group',
	}
	users_collection.bulk_write(user_requests)
	rooms_collection.bulk_write(room_requests)
	if friend_email in connected_clients:
		await connected_clients[friend_email].send(json.dumps(response))


# 取得歷史訊息
async def send_history(data, websocket, room_id):
	room_id = ObjectId(room_id)
	room = db.database.rooms.find_one({'_id': room_id})
	messages = room.get('messages')
	members = room.get('members')
	await websocket.send(
		json.dumps({'type': 'history', 'messages': messages, 'members': members})
	)


async def send_lists(data, websocket):
	user_email = data['user_email']
	user = db.database['users'].find_one({'email': user_email})

	chatLists = user['rooms']
	friendLists = user['friends']
	response = {
		'type': 'list_update',
		'chatLists': chatLists,
		'friendLists': friendLists,
	}
	await websocket.send(json.dumps(response))


async def add_friend(data, websocket):
	user_email = data['user_email']
	friend_email = data['friend_email']

	user = db.database['users'].find_one({'email': user_email})
	friend = db.database['users'].find_one({'email': friend_email})

	friend_ids = {friend['friend_id'] for friend in user['friends']}
	old_friend_ids = {friend['friend_id'] for friend in friend['friends']}
	exists = str(friend['_id']) in friend_ids
	if exists:
		response = {'type': 'friend_existed', 'friend_id': str(friend['_id'])}
		await websocket.send(json.dumps(response))

	elif str(user['_id']) in old_friend_ids:
		old_room_id = {
			'room_id': friend['friend_room_id']
			for friend in friend['friends']
			if friend['friend_id'] == str(user['_id'])
		}
		db.database['users'].update_one(
			{'_id': user['_id']},
			{
				'$addToSet': {
					'friends': {
						'friend_id': str(friend['_id']),
						'friend_name': friend['username'],
						'friend_room_id': old_room_id['room_id'],
						'friend_email': friend_email,
					},
					'rooms': {
						'room_id': old_room_id['room_id'],
						'room_name': friend['username'],
						'room_type': 'friend',
					},
				}
			},
		)
		response = {
			'type': 'friend_added',
			'friend_id': str(friend['_id']),
			'friend_email': friend_email,
			'friend_name': friend['username'],
			'friend_room_id': old_room_id['room_id'],
		}
		await websocket.send(json.dumps(response))

	elif user and friend:
		room = {
			'name': f'{user.get("username")} and {friend.get("username")} room',
			'created_by': ObjectId(user['_id']),
			'room_type': 'friend',
			'members': [
				{'_id': str(user['_id']), 'member_name': user['username']},
				{'_id': str(friend['_id']), 'member_name': friend['username']},
			],
			'messages': [],
		}
		room_id = rooms_collection.insert_one(room).inserted_id
		db.database['users'].update_one(
			{'_id': friend['_id']},
			{
				'$addToSet': {
					'friends': {
						'friend_id': str(user['_id']),
						'friend_name': user['username'],
						'friend_room_id': str(room_id),
						'friend_email': user_email,
					},
					'rooms': {
						'room_id': str(room_id),
						'room_name': user['username'],
						'room_type': 'friend',
					},
				}
			},
		)
		db.database['users'].update_one(
			{'_id': user['_id']},
			{
				'$addToSet': {
					'friends': {
						'friend_id': str(friend['_id']),
						'friend_name': friend['username'],
						'friend_room_id': str(room_id),
						'friend_email': friend_email,
					},
					'rooms': {
						'room_id': str(room_id),
						'room_name': friend['username'],
						'room_type': 'friend',
					},
				}
			},
		)

		response = {
			'type': 'friend_added',
			'friend_id': str(friend['_id']),
			'friend_email': friend_email,
			'friend_name': friend['username'],
			'friend_room_id': str(room_id),
		}
		response_to_friend = {
			'type': 'friend_added',
			'friend_id': str(user['_id']),
			'friend_email': user_email,
			'friend_name': user['username'],
			'friend_room_id': str(room_id),
		}

		if friend_email in connected_clients:
			await connected_clients[friend_email].send(json.dumps(response_to_friend))
		await websocket.send(json.dumps(response))

	else:
		response = {'type': 'friend_not_found', 'friend_email': friend_email}
		await websocket.send(json.dumps(response))


async def remove_friend(data, websocket):
	user_email = data['user_email']
	friend_id = data['friend_id']
	user = db.database['users'].find_one({'email': user_email})
	user_requests = [
		UpdateOne({'_id': user['_id']}, {'$pull': {'friends': {'friend_id': friend_id}}}),
		UpdateOne(
			{'_id': user['_id']},
			{'$pull': {'rooms': {'room_id': data['friend_room_id']}}},
		),
	]
	response = {
		'type': 'friend_removed',
		'friend_id': friend_id,
		'friend_room_id': data['friend_room_id'],
	}

	users_collection.bulk_write(user_requests)
	await websocket.send(json.dumps(response))
