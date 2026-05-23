import threading
import socket
import sys

def receptor():
    while True:



        pass

def emisor():
    while True:

    

        pass

# Inicio "main"
print("Mensajeria Redes 2025")


# Validamos argumentos
if len(sys.argv) < 3:
	print(" Error: faltan argumentos. Uso: cliente.py ipDest puertoDest")
	sys.exit(1)






tReceptor = threading.Thread(target=receptor, daemon=True)
tEmisor = threading.Thread(target=emisor)

tReceptor.start()
tEmisor.start()

tReceptor.join()
tEmisor.join()