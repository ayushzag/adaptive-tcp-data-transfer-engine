import asyncio


async def client(name):
    reader, writer = await asyncio.open_connection(
        "127.0.0.1",
        5050
    )

    print(f"{name} connected")

    data = await reader.read(1024)

    print(f"{name} received: {data.decode()}")

    writer.close()
    await writer.wait_closed()


async def main():
    await asyncio.gather(
        client("Client 1"),
        client("Client 2"),
        client("Client 3")
    )


asyncio.run(main())