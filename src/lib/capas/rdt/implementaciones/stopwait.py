"""Punto de extensión para el futuro canal Stop-and-Wait."""

from ..canal import Canal
from ..errores import ErrorModoNoImplementado,ErrorSegmento,ErrorConfirmacion
from ...udp.errores import ErrorTiempoEspera
from queue import Queue,Empty
import logging
import threading

from ..segmento import (
    Segmento,
    TipoSegmento,
    codificar_segmento,
    decodificar_segmento,
)

logger = logging.getLogger(__name__)

class CanalStopWait(Canal):
    def __init__(self, enlace):
        self._enlace = enlace
        self.RTT = 0.04 # -----------> 40ms
        self.TIMEOUT_APK_SW = self.RTT + 1/2 * self.RTT
        self.secuencia_actual_envio = 0
        self.secuencia_actual_recepcion = 0
        self.datos_en_espera = Queue()
    
    def _procesar_datos(self,segmento):
            logger.debug("Secuencia correcta,Enviando ACK")
            self._enlace.enviar(codificar_segmento(Segmento(TipoSegmento.ACK ,confirmacion = segmento.secuencia)))
            logger.debug("ACK enviado")
            self.secuencia_actual_recepcion += 1
            
    def enviar(self, datos: bytes):
        logger.debug(
                    "[%s] Enviando segmento DATOS: %d bytes",
                    threading.current_thread().name,
                    len(datos)
                )
        ack_ok = False
        
        while not ack_ok:
            segmento = codificar_segmento(
                    Segmento(TipoSegmento.DATOS,secuencia = self.secuencia_actual_envio ,carga=datos))
            try:   
                
                self._enlace.enviar(segmento)
            
                logger.debug("SW: DATOS seq=%d enviado",
                                         self.secuencia_actual_envio)
                
                recepcion = decodificar_segmento(self._enlace.recibir(timeout = self.TIMEOUT_APK_SW))
                
                logger.debug("SW: recibo tipo=%s y confirmacion=%s",
                                         recepcion.tipo,recepcion.confirmacion)
                
                if recepcion.tipo == TipoSegmento.ACK:
                    if recepcion.confirmacion != self.secuencia_actual_envio:
                        raise ErrorConfirmacion
                        
                    self.secuencia_actual_envio += 1
                    ack_ok = True
                    logger.debug("SW: ACK correcto")
                    
                elif recepcion.tipo == TipoSegmento.DATOS:
                    if recepcion.secuencia == self.secuencia_actual_recepcion:
                        self.datos_en_espera.put(recepcion.carga)
                        self. _procesar_datos(recepcion)
                    else:
                        self._enlace.enviar(codificar_segmento(Segmento(TipoSegmento.ACK ,confirmacion = recepcion.secuencia)))
                else: 
                    raise ErrorSegmento("Segmento inesperado")
                
            except (ErrorTiempoEspera,ErrorSegmento,ErrorConfirmacion):
                    continue

    def recibir(self) -> bytes:
        if not self.datos_en_espera.empty():
            return self.datos_en_espera.get()
        while True:
            try:
                logger.debug("SW: servidor esperando datos")
                segmento = decodificar_segmento(self._enlace.recibir(timeout = self.TIMEOUT_APK_SW))
                
                logger.debug("SW recibi %s, de secuencia %s y esperaba %s",segmento.tipo,segmento.secuencia,self.secuencia_actual_recepcion)
                
                if segmento.tipo != TipoSegmento.DATOS and segmento.tipo != TipoSegmento.ACK:
                    raise ErrorSegmento("Segmento inesperado")
                
                if segmento.tipo == TipoSegmento.ACK:
                    continue
                logger.debug("SW: AHORA recibi %s, de secuencia %s y esperaba %s",segmento.tipo,
                            segmento.secuencia,self.secuencia_actual_recepcion)                             
                if segmento.secuencia == self.secuencia_actual_recepcion:
                    self._procesar_datos(segmento)
                    return segmento.carga
                
                else:
                    self._enlace.enviar(codificar_segmento(Segmento(TipoSegmento.ACK
                                            ,confirmacion = segmento.secuencia)))
                
            except(ErrorTiempoEspera,ErrorSegmento):
                continue
            
    def vaciar(self):
        pass

    def cerrar(self):
        pass
