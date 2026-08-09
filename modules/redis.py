from dataclasses import dataclass
from typing import Optional

from ashredis import RedisManager, RedisParams, RecordBase, MISSING

import config

REDIS_PARAMS = None

@dataclass
class DeepseekParams(RecordBase):
    message_id: Optional[int] = MISSING

async def init():
    global REDIS_PARAMS

    REDIS_PARAMS = RedisParams(
        config.REDIS_HOST,
        config.REDIS_PORT,
        config.REDIS_USER,
        config.REDIS_PASSWORD,
        config.REDIS_DATABASE
    )

    async with RedisManager(redis_params=REDIS_PARAMS) as redis:
        if not (await redis.get_exists(DeepseekParams, "deepseek_params"))[0]:
            await set_deepseek_message_id(config.DS_MSGID)

async def get_deepseek_message_id() -> int:
    async with RedisManager(redis_params=REDIS_PARAMS) as redis:
        return (await redis.load(DeepseekParams, "deepseek_params")).message_id

async def set_deepseek_message_id(message_id: int) -> None:
    async with RedisManager(redis_params=REDIS_PARAMS) as redis:
        temp = await redis.load(DeepseekParams, "deepseek_params")
        if temp:
            temp.message_id = message_id
        else:
            temp = DeepseekParams(message_id=message_id)
        await redis.save(temp, "deepseek_params")

async def incr_key(key, ttl=None):
    async with RedisManager(redis_params=REDIS_PARAMS) as redis:
        return await redis.incr_raw(key, ttl=ttl)
