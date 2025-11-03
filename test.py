import asyncio, websockets

async def test():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as ws:
        print("Połączono!")
        await ws.send('{"role": "master", "token": 2390}')
        print(await ws.recv())

asyncio.run(test())
