import aiomysql
import asyncio
from pprint import pprint
from time import sleep

from superservice import settings


loop = asyncio.get_event_loop()

async def main():
    conn = await aiomysql.connect(host=settings.MYSQL_HOST,
                                  port=settings.MYSQL_PORT,
                                  user=settings.MYSQL_USER,
                                  password=settings.MYSQL_PASSWORD,
                                  db=settings.MYSQL_DB,
                                  cursorclass=aiomysql.cursors.DictCursor,
                                  autocommit=True,
                                  loop=loop)

    # print('Первый запрос')
    # async with conn.cursor() as cursor:
    #     await cursor.execute('SELECT * from users WHERE id=4;')
    #     r = await cursor.fetchall()
    #     pprint(r)

    # print('\nСпим 10 секунд\n')
    # sleep(10)
    #
    # print('Второй запрос')
    # async with conn.cursor() as cursor:
    #     await cursor.execute('SELECT * from users WHERE id=4;')
    #     r = await cursor.fetchall()
    #     pprint(r)

    print('Запрос с транзакцией')
    async with conn.cursor() as cursor:
        await conn.begin()
        print('Первый апдейт')
        await cursor.execute('UPDATE users SET wallet=100 WHERE id=4;')
        print('Спим 10 секунд\n')
        sleep(10)

        print('Второй апдейт')
        await cursor.execute('UPDATE users SET wallet=200 WHERE id=4;')
        print('Спим 10 секунд\n')

        print('Коммит')
        await conn.commit()

    conn.close()


loop.run_until_complete(main())
