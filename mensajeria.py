import threading
import socket
import sys
import time
import ipaddress
import getpass
from pathlib import Path


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

def recibirTCP(client_socket, buf):
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
    buf = recibirTCP(client_socket, buf)
    buf = buf.removesuffix("\r\n")
    print(buf)

    if buf != "Redes - Mensajeria - 2026":  
        print("ERROR: Protocolo incorrecto.\n") 
        sys.exit(1)

    return client_socket  

def enviarMensajeUDP():
    pass

def recibirMensajeUDP():
    pass

def hilo_emisor(): 
    while True:
        tipo, direccion, mensaje = controlEntradaEstandar()
        usuario = getpass.getuser()

        if direccion == "255.255.255.255":
            pass
        elif tipo == "mensaje":
            client_socket = establecerConexionTCP(direccion, int(sys.argv[1]))
            enviarMensajeTCP(client_socket, "M-"+ usuario + "-" + mensaje + "\r\n")
            client_socket.close()
        elif tipo == "archivo":
            client_socket = establecerConexionTCP(direccion, int(sys.argv[1]))
            enviarMensajeTCP(client_socket, "A-" + usuario + "-" + " " + "\r\n")
            with open(str(mensaje), "rb") as archivo:
                while datos := archivo.read(1024):
                    client_socket.sendall(datos)
            client_socket.close()
            
def hilo_receptor():
    # Crea socket TCP y asocia puerto de escucha
    recept_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    recept_socket.bind(("127.0.0.2", int(sys.argv[1])))
    recept_socket.listen(5)


    def hilo_cliente(client_socket, client_addr):
        enviarMensajeTCP(client_socket, "Redes - Mensajeria - 2026\r\n")
        buf = ""
        buf = recibirTCP(client_socket, buf)
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
                pass

        client_socket.close()

    while True:
        # Acepto la conexion entrante
        client_socket, client_addr = recept_socket.accept()
        threading.Thread(target=hilo_cliente, args=(client_socket, client_addr), daemon=True).start()
        
def main():
    
    #receptor = threading.Thread(target=hilo_receptor, daemon=True)
    emisor = threading.Thread(target=hilo_emisor, daemon=True)

    #receptor.start()
    emisor.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nPrograma terminado")
        sys.exit(0)

main()
