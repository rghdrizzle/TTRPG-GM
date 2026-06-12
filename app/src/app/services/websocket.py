import asyncio
import redis.asyncio as aioredis
import json
from fastapi import WebSocket
from app.db.redis import RedisPubSubManager
import logging



class WebSocketManager:
    """
    Initializes a web socket manager instance that performs functions such as adding websocket connection to the list or using pub/sub client to subscribe to the redis channel and broadcast
    """

    def __init__(self):
        self.rooms: dict ={}
        self.redis_client = RedisPubSubManager()
        self.tasks = {}
    

    async def add_user_to_room(self,room_id, websocket: WebSocket)->None:
        await websocket.accept()
        if room_id in self.rooms: # If room id exists in the rooms then just add websocket to the list of websockets for that room
            self.rooms[room_id].append(websocket)
        else:
            self.rooms[room_id] = [websocket] # new room with the first connection

            await self.redis_client.connect()
            pubsub_subscriber = await self.redis_client.subscribe(room_id)
            task = asyncio.create_task(self._pubsub_data_reader(pubsub_subscriber))
            self.tasks[room_id]= task
    # Pushes the message to the room
    async def broadcast(self,room_id, message)->None:
        await self.redis_client._publish(room_id,message)
    
    async def remove_user_from_room(self,room_id,websocket:WebSocket)->None:
        self.rooms[room_id].remove(websocket)

        if len(self.rooms[room_id])==0:
            del self.rooms[room_id]
            await self.redis_client.unsubscribe(room_id)
            task = self.tasks.pop(room_id,None) # removing the task from the dict
            if task: # JUST IN CASE IF THE TASK DOESNT EXIST
                task.cancel() # cancel the task when the room is empty
                try:
                    await task # wait for it to stop
                except asyncio.CancelledError:
                    pass # this is what we need i.e to finally remove the task once and for all
                
    # this tasks one sends the message from the room to every other client
    async def _pubsub_data_reader(self, pubsub_subscriber):
        while True:
            message = await pubsub_subscriber.get_message(ignore_subscribe_messages=True)
            if message is not None:
                room_id = message['channel'].decode('utf-8')
                data = message['data'].decode('utf-8')
                all_sockets = self.rooms[room_id]
                for socket in all_sockets:
                    try:
                        await socket.send_text(data)
                    except Exception:
                        logging.exception( "Failed to send websocket message to socket %s",id(socket))
        