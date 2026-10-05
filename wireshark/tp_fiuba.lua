-- Dissector de Wireshark para el protocolo del TP.
--
-- Instalacion:
--   Linux/Mac:  cp tp_fiuba.lua ~/.local/lib/wireshark/plugins/
--   Windows:    copiar a %APPDATA%\Wireshark\plugins\
--   Recargar sin reiniciar: Analyze > Reload Lua Plugins  (Ctrl+Shift+L)
--
-- Por defecto se engancha al puerto UDP 8080. Para otro puerto:
--   Edit > Preferences > Protocols > TPFIUBA > Puerto UDP
--
-- Decodifica las dos capas propias:
--   1. El segmento RDT de 11 bytes  (tipo, secuencia, confirmacion, longitud)
--   2. El mensaje de aplicacion de 3 bytes dentro de los segmentos DATOS

local tp = Proto("tpfiuba", "TP Redes - File Transfer")

-- ----------------------------------------------------------- constantes

local TIPO_SEGMENTO = {
    [1] = "SYN",
    [2] = "ACK",
    [3] = "DATOS",
    [4] = "FIN",
}

local PROTOCOLO = {
    [0] = "Stop & Wait",
    [1] = "SACK",
    [2] = "Directo",
}

local TIPO_MENSAJE = {
    [1] = "SOLICITUD_SUBIDA",
    [2] = "SOLICITUD_DESCARGA",
    [3] = "ACEPTADO",
    [4] = "BLOQUE_ARCHIVO",
    [5] = "FIN_ARCHIVO",
    [6] = "COMPLETADO",
    [7] = "ERROR",
}

local CABECERA_SEGMENTO = 11
local CABECERA_MENSAJE = 3

-- -------------------------------------------------------------- campos

local f = tp.fields

f.tipo = ProtoField.uint8("tpfiuba.tipo", "Tipo", base.DEC, TIPO_SEGMENTO)
f.secuencia = ProtoField.uint32("tpfiuba.secuencia", "Secuencia", base.DEC)
f.confirmacion = ProtoField.uint32("tpfiuba.confirmacion", "Confirmacion",
                                   base.DEC)
f.longitud = ProtoField.uint16("tpfiuba.longitud", "Longitud de carga",
                               base.DEC)

f.protocolo = ProtoField.uint8("tpfiuba.protocolo", "Protocolo solicitado",
                               base.DEC, PROTOCOLO)

f.bloques = ProtoField.none("tpfiuba.sack", "Bloques SACK")
f.bloque_inicio = ProtoField.uint32("tpfiuba.sack.inicio", "Inicio", base.DEC)
f.bloque_fin = ProtoField.uint32("tpfiuba.sack.fin", "Fin", base.DEC)

f.msg = ProtoField.none("tpfiuba.msg", "Mensaje de aplicacion")
f.msg_tipo = ProtoField.uint8("tpfiuba.msg.tipo", "Tipo", base.DEC,
                              TIPO_MENSAJE)
f.msg_longitud = ProtoField.uint16("tpfiuba.msg.longitud", "Longitud",
                                   base.DEC)
f.msg_json = ProtoField.string("tpfiuba.msg.json", "Carga (JSON)")
f.msg_datos = ProtoField.bytes("tpfiuba.msg.datos", "Carga (bytes)")

-- expert info: resalta en rojo los datagramas que no cuadran
local e_corto = ProtoExpert.new("tpfiuba.corto", "Datagrama demasiado corto",
                                expert.group.MALFORMED, expert.severity.ERROR)
local e_longitud = ProtoExpert.new("tpfiuba.longitud_mal",
                                   "La longitud declarada no coincide",
                                   expert.group.MALFORMED,
                                   expert.severity.WARN)
tp.experts = { e_corto, e_longitud }

-- ------------------------------------------------------------ auxiliares

local function describir_sack(buf, arbol)
    -- La carga de un ACK son rangos de 8 bytes: inicio y fin, ambos !I.
    local cantidad = math.floor(buf:len() / 8)
    if cantidad == 0 then
        return ""
    end

    local sub = arbol:add(f.bloques, buf)
    local partes = {}
    for i = 0, cantidad - 1 do
        local inicio = buf(i * 8, 4):uint()
        local fin = buf(i * 8 + 4, 4):uint()
        local rango = sub:add(f.bloque_inicio, buf(i * 8, 4))
        sub:add(f.bloque_fin, buf(i * 8 + 4, 4))
        rango:append_text(string.format("  [%d-%d]", inicio, fin))
        partes[#partes + 1] = string.format("%d-%d", inicio, fin)
    end
    sub:append_text(string.format(" (%d)", cantidad))
    return " SACK=[" .. table.concat(partes, ",") .. "]"
end

local function describir_mensaje(buf, arbol)
    -- Dentro de un DATOS viaja un mensaje de aplicacion: tipo(1), long(2).
    if buf:len() < CABECERA_MENSAJE then
        return ""
    end

    local tipo = buf(0, 1):uint()
    local longitud = buf(1, 2):uint()
    local nombre = TIPO_MENSAJE[tipo] or string.format("DESCONOCIDO(%d)", tipo)

    local sub = arbol:add(f.msg, buf)
    sub:append_text(": " .. nombre)
    sub:add(f.msg_tipo, buf(0, 1))
    sub:add(f.msg_longitud, buf(1, 2))

    local carga = buf:len() - CABECERA_MENSAJE
    if carga > 0 then
        local cuerpo = buf(CABECERA_MENSAJE, carga)
        if tipo == 4 then
            -- BLOQUE_ARCHIVO: bytes crudos, no tiene sentido mostrarlos.
            sub:add(f.msg_datos, cuerpo)
            return string.format(" %s %d bytes", nombre, carga)
        end
        -- El resto lleva JSON en UTF-8.
        local texto = cuerpo:string(ENC_UTF_8)
        sub:add(f.msg_json, cuerpo, texto)
        return " " .. nombre .. " " .. texto
    end

    return " " .. nombre
end

-- -------------------------------------------------------------- principal

function tp.dissector(buf, pinfo, arbol)
    local largo = buf:len()
    if largo == 0 then
        return 0
    end

    pinfo.cols.protocol = "TP-FT"

    local raiz = arbol:add(tp, buf(), "TP Redes - File Transfer")

    if largo < CABECERA_SEGMENTO then
        raiz:add_proto_expert_info(e_corto)
        pinfo.cols.info = "Datagrama corto (" .. largo .. " bytes)"
        return largo
    end

    local tipo = buf(0, 1):uint()
    local secuencia = buf(1, 4):uint()
    local confirmacion = buf(5, 4):uint()
    local longitud = buf(9, 2):uint()
    local nombre = TIPO_SEGMENTO[tipo] or string.format("DESCONOCIDO(%d)", tipo)

    raiz:add(f.tipo, buf(0, 1))
    raiz:add(f.secuencia, buf(1, 4))
    raiz:add(f.confirmacion, buf(5, 4))
    raiz:add(f.longitud, buf(9, 2))
    raiz:append_text(", " .. nombre)

    local carga = largo - CABECERA_SEGMENTO
    if longitud ~= carga then
        raiz:add_proto_expert_info(e_longitud)
    end

    local info = nombre
    if carga > 0 then
        local cuerpo = buf(CABECERA_SEGMENTO, carga)

        if tipo == 1 then
            -- SYN: un byte con el protocolo pedido.
            raiz:add(f.protocolo, cuerpo(0, 1))
            local p = PROTOCOLO[cuerpo(0, 1):uint()] or "?"
            info = info .. " protocolo=" .. p
        elseif tipo == 2 then
            info = info .. describir_sack(cuerpo, raiz)
        elseif tipo == 3 then
            info = info .. describir_mensaje(cuerpo, raiz)
        end
    end

    -- La columna Info es lo que se lee en la captura sin abrir nada.
    if tipo == 2 then
        pinfo.cols.info = string.format("ACK confirmacion=%d%s",
                                        confirmacion,
                                        info:sub(#nombre + 1))
    elseif tipo == 3 then
        pinfo.cols.info = string.format("DATOS seq=%d%s",
                                        secuencia,
                                        info:sub(#nombre + 1))
    else
        pinfo.cols.info = info
    end

    return largo
end

-- ------------------------------------------------------------ registro

tp.prefs.puerto = Pref.uint("Puerto UDP", 8080,
                            "Puerto en el que escucha el servidor")

local puerto_actual = nil

function tp.prefs_changed()
    local udp = DissectorTable.get("udp.port")
    if puerto_actual then
        udp:remove(puerto_actual, tp)
    end
    puerto_actual = tp.prefs.puerto
    udp:add(puerto_actual, tp)
end

local udp = DissectorTable.get("udp.port")
puerto_actual = tp.prefs.puerto
udp:add(puerto_actual, tp)
