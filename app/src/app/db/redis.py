import asyncio
import redis.asyncio as aioredis
import json
from fastapi import WebSocket


class RedisPubSubManager:
    """
    Creates an instance of this class which manages Redis connection and implement Pub and Sub pattern
    args: host(str) port(int)
    """

    def __init__(self,host="localhost",port=6379):
        self.redis_host = host
        self.redis_port = port
        self.pubsub = None

    async def __get_redis_connection(self) -> aioredis:
        return aioredis.Redis(host=self.redis_host,port=self.redis_port,auto_close_connection_pool=False)
    
    async def connect(self)->None:
        self.redis_connection = await self.__get_redis_connection()
        self.pubsub = self.redis_connection.pubsub()

    async def _publish(self,room_id:str, message:str)-> None:
        await self.redis_connection.publish(room_id,message)
    
    async def subscribe(self, room_id: str)-> aioredis.Redis:
        await self.pubsub.subscribe(room_id)
        return self.pubsub
    async def unsubscribe(self, room_id)->None:
        await self.pubsub.unsubscribe(room_id)
        

    