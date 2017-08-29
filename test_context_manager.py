
class MyCM:
    def __init__(self, txt):
        print('init')
        self.txt = txt

    def __enter__(self):
        print('enter')
        return self.txt

    def __exit__(self, exc_type, exc_val, exc_tb):
        print('exit')


def main():
    with MyCM('hello') as t:
        print(t)
        raise Exception()


main()
