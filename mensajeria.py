import threading


def receptor():
    while True:
        pass

def emisor():
    while True:
        pass

tReceptor = threading.Thread(target=receptor, daemon=True)
tEmisor = threading.Thread(target=emisor)

tReceptor.start()
tEmisor.start()

tReceptor.join()
tEmisor.join()