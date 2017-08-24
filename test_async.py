import asyncio


async def hello(name):
    return 'Hello, {}!'.format(name)


async def print_hello(name):
    print(await hello(name))


loop = asyncio.get_event_loop()
loop.run_until_complete(print_hello('Vasya'))

