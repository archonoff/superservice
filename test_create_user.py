import threading
import requests
import ujson
import logging
from time import sleep


logging.basicConfig(level=logging.DEBUG)


class Sender(threading.Thread):

    def __init__(self, requests_count, url, thread_num, *args, **kwargs):
        super(Sender, self).__init__(*args, **kwargs)
        self.requests_cont = requests_count
        self.url = url
        self.thread_num = thread_num

    def run(self):
        for data in give_json(self.requests_cont):
            r = requests.post(self.url, data=data)
            logging.debug('Тред {}, респонс {}'.format(self.thread_num, r))


def give_json(users_count: int):
    base = {
        'name': 'Usre Name',
        'login': '',
        'password': 'password',
        'user_type': 'customer'
    }

    for u in range(users_count):
        base['login'] = 'login-{}'.format(u)
        yield ujson.dumps(base)


def main():
    url = 'http://127.0.0.1:8000/api/users/register/'
    threads_count = 2
    for i in range(threads_count):
        t = Sender(5, url, i)
        logging.debug('Запуск треда {}'.format(i+1))
        t.start()
    logging.debug('Все треды запущены')


if __name__ == '__main__':
    main()
