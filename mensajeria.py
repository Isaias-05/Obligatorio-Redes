import threading #Manejo de hilos
import socket #Manejo de sockets
import sys #Manejo del sistema
import signal #Señales del sistema
import time #Tiempo
import getpass #Obterer user
from pathlib import Path #Obtener la ruta del archivo
import os #Obtener tamaño y nombre de archivo
import hashlib #Hashear la contraseña a MD5


def es_direccion_valida(direccion):    
    if direccion == "*":
        return True, "255.255.255.255"
    else:
        try:
            ip = socket.gethostbyname(direccion)
            return True, ip
        except socket.gaierror:
            return False, None
        
def controlEntradaEstandar():     
    while True:

        #Lee la entrada estandar y valida que tenga el formato correcto, es decir: "ip mensaje" o "ip &file rutaArchivo"
        entrada = input("> ")
        entrada = entrada.strip()
        entrada = entrada.split(maxsplit=1)

        if len(entrada) == 2 :
            
            direccion = entrada[0]
            mensaje = entrada[1]

            esDireccion, direccion = es_direccion_valida(direccion)

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

                else:
                    tipo = "mensaje"
                    return tipo, direccion, mensaje
                
            else:
                print("Direccion IP invalida")
        else:
            print("Comando invalido")
            continue

def recibirMensajeTCP(client_socket):
    buf = ""
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

def establecerConexionTCP(ip, puerto, respuesta):
    # Crea socket TCP y me conecto al ip y puerto pasados como parametro
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((ip, puerto))

    #vacio el buffer y espero un saludo
    buf = recibirMensajeTCP(client_socket)
    buf = buf.removesuffix("\r\n")

    if buf != respuesta:  
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

def iniciarSesion():
    ipAuth = socket.gethostbyname("ti.esi.edu.uy")
    while True:

        usuario = input("Usuario: ")
        #contraseña = getpass.getpass("Clave: ")
        contraseña = input("Contraseña: ")
        solicitud = usuario +"-"+ hashlib.md5(contraseña.encode()).hexdigest() + "\r\n"
        socket_IniciarSesion = establecerConexionTCP(ipAuth, 33,"Redes 2026 - Laboratorio - Autenticacion de Usuarios")
        enviarMensajeTCP(socket_IniciarSesion, solicitud)
    
        respuesta = recibirMensajeTCP(socket_IniciarSesion)
        respuesta = respuesta.removesuffix("\r\n")
        
        if respuesta == "SI":
            respuesta = recibirMensajeTCP(socket_IniciarSesion)
            respuesta = respuesta.removesuffix("\r\n")
            print("Bienvenido " + respuesta)
            break
        else: 
            print("Usuario o contraseña incorrecta")

def hilo_escucha_broadcast():
    # Crea socket UDP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(("0.0.0.0", int(sys.argv[1]) + 1))

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
            try:
                client_socket = establecerConexionTCP(direccionIP, int(sys.argv[1]), str("Redes - Mensajeria - 2026"))
                enviarMensajeTCP(client_socket, "M-"+ usuario + "-" + mensaje + "\r\n")
                client_socket.close()
            except: 
                print("Error de conexion - hostname o ip invalida")
        elif tipo == "archivo":
            ruta = mensaje
            tamaño_archivo = os.path.getsize(ruta)
            nombre_archivo = os.path.basename(ruta)

            try:
                client_socket = establecerConexionTCP(direccionIP, int(sys.argv[1]),str("Redes - Mensajeria - 2026"))
                enviarMensajeTCP(client_socket, "A-"+ nombre_archivo + "-" + str(tamaño_archivo) + "\r\n")
                with open(ruta, "rb") as archivo:
                    while datos := archivo.read(4096):
                        client_socket.sendall(datos)
            except: 
                print("Error de conexion - hostname o ip invalida")

def hilo_cliente(client_socket, client_addr):
        enviarMensajeTCP(client_socket, "Redes - Mensajeria - 2026\r\n")
        buf = recibirMensajeTCP(client_socket)
        msg = buf.removesuffix("\r\n")
        msg = msg.split("-", 2)

        if len(msg) < 3:
            enviarMensajeTCP(client_socket, "Comando no conocido\r\n")
            client_socket.close()
            return
        else:
            if  msg[0] == "M":
                tiempo = time.strftime("%Y.%m.%d %H:%M:%S")
                usuario = msg[1]
                print("[" + tiempo + "] " + str(client_addr[0]) + " - " + usuario + " dice: " + msg[2])

            elif msg[0] == "A":
                nombre_archivo = msg[1]
                tamaño_archivo = int(msg[2])
                data = recibirArchivoTCP(client_socket,tamaño_archivo)
                with open(nombre_archivo, "wb") as archivo:
                    archivo.write(data)

        client_socket.close()

def hilo_receptor():
    # Crea socket TCP y asocia puerto de escucha
    recept_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    recept_socket.bind(("0.0.0.0", int(sys.argv[1])))
    recept_socket.listen(5)

    while True:
        # Acepto la conexion entrante
        client_socket, client_addr = recept_socket.accept()
        threading.Thread(target=hilo_cliente, args=(client_socket, client_addr), daemon=True).start()

def manejador_term(sig,frame):
   
    if sig == 2:
        print(f'\nSeñal CTRL + C recibida.... Cerrando Sesión')
    elif sig == 15: 
        print(f'\nSeñal KILL recibida.... Cerrando Sesión')

    sys.exit(0)
 
def main():
    
    iniciarSesion()
    
    receptor = threading.Thread(target=hilo_receptor, daemon=True)
    emisor = threading.Thread(target=hilo_emisor, daemon=True)
    escucha_broadcast = threading.Thread(target=hilo_escucha_broadcast, daemon=True)

    receptor.start()
    emisor.start()
    escucha_broadcast.start()

    signal.signal(signal.SIGINT, manejador_term)
    signal.signal(signal.SIGTERM, manejador_term)

    while True:
        time.sleep(1)

main()










#* &file ./redes2026-lab1.pdf
#192.168.1.134 buenash
#192.168.1.134 &file ./lab1.pdf
#localhost &file ./lab1.pdf