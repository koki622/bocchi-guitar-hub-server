import asyncio

import redis.asyncio as redis

async def reader(channel: redis.client.PubSub):
    try:
        while True:
            message = await channel.get_message(ignore_subscribe_messages=True)
            if message is not None:
                print(f"(Reader) Message Received: {message}")
                if message["data"].decode() == "STOP":
                    print("(Reader) STOP")
                    break
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        print("Reader stopped")
    

async def main():
    r = redis.from_url("redis://redis:6379",
                         health_check_interval=10,
                         socket_connect_timeout=5,
                         retry_on_timeout=True,
                         socket_keepalive=True)
    async with r.pubsub() as pubsub:
        await pubsub.subscribe("channel:gpu")

        future = asyncio.create_task(reader(pubsub))
        await r.publish("channel:gpu", "hello")
        await r.publish("channel:gpu", "STOP")

    await future

asyncio.run(main())


    