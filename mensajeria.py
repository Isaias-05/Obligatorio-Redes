import threading
import socket
import sys

def receptor():
    while True:
        #crear socket tcp de escucha
        #si recibe un mensaje lo muestra por la salida estadar 
        #si recibe un archivo, implenta logica para ver le llego bien
        #todo lo que imprime lo hara con fecha y hora, nombre del emisor + texto 
        

        pass

def emisor():
    while True:
        #crar socket tcp para enviar datos
        #hay que identificar si se envia un mensaje o un archivo 
        #evaluar si es mensaje, archivo o esta mal
        #establecer una conexion al puerto sys.argv[1] y la ip que ingreso el usuario
        #vhacer consulta dns ya sea ip o nombre de dominio
        #cualquier envio tambien manda el nombre del usuario
        #evaluar si se apreto cntrl + c para terminar el programa
    

        pass

# Inicio "main"
print("Mensajeria Redes 2025")


# Validamos argumentos
if len(sys.argv) < 3:
	print(" Error: faltan argumentos. Uso: cliente.py ipDest puertoDest")
	sys.exit(1)


#Validar que el usuario esta registrado. 



tReceptor = threading.Thread(target=receptor, daemon=True)
tEmisor = threading.Thread(target=emisor)

tReceptor.start()
tEmisor.start()

tReceptor.join()
tEmisor.join()