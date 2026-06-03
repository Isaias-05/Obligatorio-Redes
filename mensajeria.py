import threading
import socket
import sys
import time
import ipaddress
import getpass
from pathlib import Path
import os

ipGlobal = "192.168.1.127"

def es_direccion_valida(direccion):    
    if direccion == "*":
        return True, "255.255.255.255"
    else:
        try:
            ip = socket.gethostbyname(direccion)
            return True, ip
        except socket.gaierror:
            print("Error: Ip o nombre de dominio invalido")
            return False, None

def controlEntradaEstandar():     
    while True:

        #Lee la entrada estandar y valida que tenga el formato correcto, es decir: "ip mensaje" o "ip &file rutaArchivo"
        entrada = input(" > ")
        entrada = entrada.strip()
        entrada = entrada.split(maxsplit=1)

        if len(entrada) == 2 and entrada[0] and entrada[1] :
            
            direccion = entrada[0]
            mensaje = entrada[1]

            esDireccion, direccion = es_direccion_valida(direccion); 

            if esDireccion:

                comando = mensaje.split(maxsplit=1)
                if comando[0] == "&file":
                    tipo = "archivo"
                
                    ruta = Path(comando[1].strip())

                    if not ruta.is_file():
                        print("Error: el archivo no existe")
                    elif direccion == "255.255.255.255":
                        print("Error: no se pueden enviar archivos por broadcast")
                    else:
                        tipo = "archivo"
                        return tipo, direccion, ruta.resolve()
                        break

                else:
                    tipo = "mensaje"
                    return tipo, direccion, mensaje
                    break
        else:
            print("Comando invalido")
            continue

def recibirMensajeTCP(client_socket, buf):
	while True:
		data = client_socket.recv(1024)
		if not data:  # Conexión cerrada
			break
		buf += data.decode('utf-8')
		if "\r\n" in buf:
			break
	return buf 

def enviarMensajeTCP(client_socket, msg):
	client_socket.send(msg.encode('utf-8'))

def establecerConexionTCP(ip, puerto):
    # Crea socket TCP y me conecto al ip y puerto pasados como parametro
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((ip, puerto))

    #vacio el buffer y espero un saludo
    buf = ""
    buf = recibirMensajeTCP(client_socket, buf)
    buf = buf.removesuffix("\r\n")

    if buf != "Redes - Mensajeria - 2026":  
        print("ERROR: Protocolo incorrecto.\n") 
        sys.exit(1)

    return client_socket  

def enviarMensajeUDP(ip, puerto, msg):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.sendto(msg.encode('utf-8'), (ip, puerto))
    
def recibirArchivoTCP(client_socket, tamaño_archivo):
    data = b""
    recibidos = 0
    while recibidos < tamaño_archivo:
        chunk = client_socket.recv(min(4096, tamaño_archivo - recibidos))
        if not chunk:
            print("Error: conexión cerrada antes de recibir el archivo completo")
            break
        data += chunk
        recibidos += len(chunk)

    return data

def hilo_escucha_broadcast():
    # Crea socket UDP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((ipGlobal, int(sys.argv[1]) + 1))

    while True:
        # Recibe msg
        data, addr = server_socket.recvfrom(1024)
        msg = data.decode('utf-8').strip()
        msg = msg.split("-", 1)

        Tiempo = time.strftime("%Y.%m.%d %H:%M:%S")
        usuario = msg[0]
        print("[" + Tiempo + "] " + str(addr[0]) + " - " + usuario + " dice: " + msg[1])
        
def hilo_emisor():
    while True:
        tipo, direccionIP, mensaje = controlEntradaEstandar()
        usuario = getpass.getuser()

        if direccionIP == "255.255.255.255":
            enviarMensajeUDP(direccionIP, int(sys.argv[1]) + 1, usuario + "-" + mensaje)
        elif tipo == "mensaje":
            client_socket = establecerConexionTCP(direccionIP, int(sys.argv[1]))
            enviarMensajeTCP(client_socket, "M-"+ usuario + "-" + mensaje + "\r\n")
            client_socket.close()
        elif tipo == "archivo":
            ruta = mensaje
            tamaño_archivo = os.path.getsize(ruta)
            nombre_archivo = os.path.basename(ruta)
            client_socket = establecerConexionTCP(direccionIP, int(sys.argv[1]))
            enviarMensajeTCP(client_socket, "A-"+ nombre_archivo + "-" + tamaño_archivo + "\r\n")
            with open(ruta, "rb") as archivo:
                while datos := archivo.read(4096):
                    socket.sendall(datos)

def hilo_receptor():
    # Crea socket TCP y asocia puerto de escucha
    recept_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    recept_socket.bind(("127.0.0.2", int(sys.argv[1])))
    recept_socket.listen(5)


    def hilo_cliente(client_socket, client_addr):
        enviarMensajeTCP(client_socket, "Redes - Mensajeria - 2026\r\n")
        buf = ""
        buf = recibirMensajeTCP(client_socket, buf)
        msg = buf.removesuffix("\r\n")
        msg = msg.split("-", 2)

        if len(msg) < 3:
            enviarMensajeTCP(client_socket, "Comando no conocido\r\n")
            client_socket.close()
            return
        else:
            if  msg[0] == "M":
                Tiempo = time.strftime("%Y.%m.%d %H:%M:%S")
                usuario = msg[1]
                print("[" + Tiempo + "] " + str(client_addr[0]) + " - " + usuario + " dice: " + msg[2])

            elif msg[0] == "A":
                nombre_archivo = msg[1]
                tamaño_archivo = msg[2]
                data = recibirArchivoTCP(client_socket,tamaño_archivo)
                with open(nombre_archivo, "wb") as archivo:
                    archivo.write(data)

        client_socket.close()

    while True:
        # Acepto la conexion entrante
        client_socket, client_addr = recept_socket.accept()
        threading.Thread(target=hilo_cliente, args=(client_socket, client_addr), daemon=True).start()
        
def main():
    
    receptor = threading.Thread(target=hilo_receptor, daemon=True)
    emisor = threading.Thread(target=hilo_emisor, daemon=True)
    escucha_broadcast = threading.Thread(target=hilo_escucha_broadcast, daemon=True)

    receptor.start()
    emisor.start()
    escucha_broadcast.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nPrograma terminado")
        sys.exit(0)
#* &file ./redes2026-lab1.pdf
main()

