"""Tabla de traducción y asignación de puertos públicos."""
from pox.lib.packet.ipv4 import ipv4

#Definido por la IANA
PUERTO_MIN = 49152
PUERTO_MAX = 65535


class PAT:
    def __init__(self):
        self.salientes = {}  #(protocolo, ip_privada, puerto_privado)
        self.entrantes = {}  #(protocolo, puerto_publico)
        #Hace falta tener una regla para cada sentido y solo liberar cuando se venzan las dos para el caso de UDP
        self.reglas = {}  #(protocolo, puerto_publico) -> sentidos con regla activa
        self.puertos_tcp = list(range(PUERTO_MIN, PUERTO_MAX + 1));
        self.puertos_udp = list(range(PUERTO_MIN, PUERTO_MAX + 1));

    def _asignar_puerto(self, protocolo):
        if(protocolo == ipv4.TCP_PROTOCOL and len(self.puertos_tcp) > 0):
            return self.puertos_tcp.pop();
        elif(protocolo == ipv4.UDP_PROTOCOL and len(self.puertos_udp) > 0):
            return self.puertos_udp.pop();
        return None

    def obtener_puerto(self, protocolo, ip_privada, puerto_privado):
        key = (protocolo, ip_privada, puerto_privado)
        if(not key in self.salientes):
            puerto = self._asignar_puerto(protocolo)
            if(puerto is None):
                return None
            self.salientes[key] = puerto
            self.entrantes[(protocolo, puerto)] = (protocolo, ip_privada, puerto_privado)
        puerto = self.salientes[key]
        self.reglas[(protocolo, puerto)] = {"saliente", "entrante"}
        return puerto
        
    def buscar_entrante(self, protocolo, puerto_publico):
        key = (protocolo, puerto_publico)
        if(key in self.entrantes):
            item = self.entrantes[key]
            return item[1], item[2]
        return None

    def regla_vencida(self, protocolo, puerto_publico, sentido):
        reglas = self.reglas.get((protocolo, puerto_publico))
        if(reglas is None):
            return
        reglas.discard(sentido)
        if(len(reglas) == 0):
            self.liberar(protocolo, puerto_publico)

    def liberar(self, protocolo, puerto_publico):
        key_entrantes =(protocolo, puerto_publico)
        if(not key_entrantes in self.entrantes):
            return
        key_salientes = self.entrantes.pop(key_entrantes)
        self.salientes.pop(key_salientes)
        self.reglas.pop(key_entrantes, None)
        if(protocolo == ipv4.TCP_PROTOCOL):
            return self.puertos_tcp.append(puerto_publico);
        return self.puertos_udp.append(puerto_publico);
