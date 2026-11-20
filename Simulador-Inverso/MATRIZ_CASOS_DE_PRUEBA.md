# Matriz de Validación de Casos de Prueba (CP-01 a CP-10)

**Asignatura:** Ciberseguridad en Tecnología Cloud y Contenedores  
**Proyecto:** Simulador de Comunicación Inversa y Monitoreo de Eventos  
**Entorno de ejecución:** Windows / Python 3.12 (Loopback `127.0.0.1`)

---

## 1. Resumen de Ejecución

| Identificador | Descripción del Caso | Resultado Esperado | Resultado Obtenido | Estado |
|---|---|---|---|:---:|
| **CP-01** | El agente establece la conexión local. | Socket TCP creado hacia `127.0.0.1:9000` con handshake SYN/ACK exitoso. | Agente conectado exitosamente, el controlador detecta y registra `AGENT_CONNECTED` con IP y puerto efímero. | **Aprobado** |
| **CP-02** | El panel refleja correctamente el estado. | La interfaz web y endpoint `/api/status` reflejan píldora en línea y dirección del agente. | El panel web muestra estado "Agente Conectado" (`127.0.0.1:puerto`) y conmuta a "Desconectado" al cerrarse el agente. | **Aprobado** |
| **CP-03** | Una consulta de estado recibe respuesta. | Envío de `STATUS` devuelve telemetría del agente (uptime, loopback verificado) sin alertas. | Respuesta `{"status": "SUCCESS"}` recibida en <50ms con clasificación `NORMAL` e `INFO`. | **Aprobado** |
| **CP-04** | La simulación de apagado genera una alerta sin efectos reales. | El comando `SIMULATE_SHUTDOWN` se clasifica como `CRITICAL` y no ejecuta comandos del sistema operativo (`shutdown`). | Alerta generada con `real_effect: NONE_BLOCKED_BY_SIMULATOR`. El equipo continúa encendido normalmente. | **Aprobado** |
| **CP-05** | La simulación de dispositivo genera un evento. | El comando `SIMULATE_DEVICE_ACTION` conmuta estado de dispositivo simulado y lo audita. | Evento generado con clasificación `ALERTA` / `WARNING`. Se alterna estado simulado de USB en memoria. | **Aprobado** |
| **CP-06** | El mensaje de texto llega al agente. | El comando `SEND_TEXT` transmite una cadena de texto arbitraria y se visualiza en consola/log del agente. | El agente muestra por consola: `[AGENTE NOTIFICACIÓN] Mensaje de texto recibido...` y devuelve acuse con longitud. | **Aprobado** |
| **CP-07** | Una instrucción desconocida es rechazada. | El envío de una orden arbitraria (ej: `SHELL_EXEC_POWERSHELL` o `FORMAT_C`) es bloqueada antes de su ejecución. | El sistema rechaza la instrucción con evento `COMMAND_REJECTED`, nivel `WARNING` y mensaje de política defensiva. | **Aprobado** |
| **CP-08** | Se exporta un CSV con los registros. | La descarga desde `/api/export-csv` entrega archivo CSV bien estructurado con marcas temporales y eventos. | Generación de `evidencias_eventos.csv` con cabeceras `id,timestamp,event_type,command,source,destination,category,level,details,response`. | **Aprobado** |
| **CP-09** | El sistema maneja un intento de conexión fallido. | Si el controlador está apagado o se intenta un puerto cerrado, el agente maneja `ConnectionRefusedError` sin crashear. | El agente reintenta pacíficamente cada 3 segundos emitiendo advertencia controlada en lugar de terminar anormalmente. | **Aprobado** |
| **CP-10** | Se identifica el tráfico local TCP con Wireshark. | Captura de interfaz loopback (`Npcap Loopback Adapter`) muestra 3-way handshake (SYN, SYN-ACK, ACK) y tramas PSH/ACK con payloads JSON. | Identificados paquetes TCP en puerto 9000 con flags `[SYN]`, `[SYN, ACK]`, `[ACK]`, `[PSH, ACK]` y `[FIN, ACK]` con contenido en texto plano. | **Aprobado** |

---

## 2. Detalle y Evidencia Técnica por Caso

### CP-01: Establecimiento de Conexión Local Inversa
* **Procedimiento:** Iniciar `app.py` (controlador escuchando en puerto 9000) y posteriormente ejecutar `agent.py`.
* **Evidencia Log:**
  ```text
  [+] Intentando conectar al controlador en 127.0.0.1:9000...
  [+] ¡Conexión establecida con éxito hacia el controlador en 127.0.0.1:9000!
  ```
* **Evidencia Evento:** `id=2 | AGENT_CONNECTED | source=127.0.0.1:57015 | destination=127.0.0.1:9000 | category=NORMAL`

### CP-02: Reflejo de Estado en Panel Flask
* **Procedimiento:** Abrir `http://127.0.0.1:5000` con agente conectado; detener agente con `Ctrl+C`.
* **Evidencia:** Elemento `#connection-pill` pasa de clase `online` a `offline`. La petición `GET /api/status` actualiza los valores sin recargar página completa.

### CP-03: Consulta de Estado (`STATUS`)
* **Procedimiento:** Presionar botón "Consultar Estado" en la interfaz web.
* **Payload TCP:** `{"command": "STATUS", "param": ""}\n`
* **Respuesta JSON:**
  ```json
  {
    "status": "SUCCESS",
    "command": "STATUS",
    "is_alert": false,
    "alert_level": "INFO",
    "message": "Agente activo y respondiendo consultas de telemetría.",
    "data": {
      "agent_uptime_sec": 1795149800.14,
      "loopback_verified": true,
      "device_state": {"usb_blocked": false, "webcam_status": "IDLE_SIMULATED", "mock_disk_quota": "500GB_HEALTHY"}
    }
  }
  ```

### CP-04: Simulación de Apagado Defensivo (`SIMULATE_SHUTDOWN`)
* **Procedimiento:** Presionar botón "Simular Apagado".
* **Resultado:** No se invocan utilidades como `os.system("shutdown")`. Se emite alerta con categoría `ALERTA` y severidad `CRITICAL`.
* **Correlación MITRE ATT&CK:** Mapeado a técnica **T1529 (System Shutdown/Reboot)**.

### CP-05: Simulación de Operación de Periférico (`SIMULATE_DEVICE_ACTION`)
* **Procedimiento:** Presionar botón "Simular Dispositivo".
* **Resultado:** Modifica la estructura de datos interna en memoria `device_state["usb_blocked"] = not state`.
* **Correlación MITRE ATT&CK:** Emula actividad vinculada a **T1200 (Hardware Additions)** o modificación de políticas USB.

### CP-06: Envío de Mensaje de Texto Arbitrario (`SEND_TEXT`)
* **Procedimiento:** Ingresar `"Monitoreo defensivo: enlace activo en loopback."` y pulsar "Enviar Texto".
* **Resultado:** El agente imprime en consola el mensaje con delimitadores de seguridad y confirma su recepción con longitud exacta (47 caracteres).

### CP-07: Rechazo de Instrucción Desconocida
* **Procedimiento:** Enviar comando no listado mediante API o botón `sendCustomInvalidCommand()` con `"SHELL_EXEC_POWERSHELL"`.
* **Resultado:** Bloqueado en capa de control:
  ```json
  {
    "success": false,
    "command": "SHELL_EXEC_POWERSHELL",
    "error": "Instrucción no autorizada o fuera del conjunto permitido (RF-14)."
  }
  ```
  Se registra evento `COMMAND_REJECTED` clasificado como `ALERTA` (`WARNING`).

### CP-08: Exportación en Formato CSV
* **Procedimiento:** Solicitar `GET /api/export-csv`.
* **Resultado:** Descarga del archivo `eventos_laboratorio_c2.csv`. Validadas cabeceras estándar RFC 4180.

### CP-09: Manejo de Intento de Conexión Fallido
* **Procedimiento:** Detener el controlador y ejecutar el agente, o enviar instrucciones sin agente conectado.
* **Resultado:** El agente captura `ConnectionRefusedError`, registra el fallo y reintenta periódicamente cada 3 segundos sin colapsar. La API web responde `{ "success": false, "error": "No hay agente conectado actualmente." }`.

### CP-10: Inspección de Tráfico TCP con Wireshark
* **Procedimiento:** Iniciar captura en `Npcap Loopback Adapter` con filtro `tcp.port == 9000`.
* **Resultado:** Observado el saludo de tres vías (3-Way Handshake):
  1. `Agente -> Controlador: [SYN] Seq=0`
  2. `Controlador -> Agente: [SYN, ACK] Seq=0 Ack=1`
  3. `Agente -> Controlador: [ACK] Seq=1 Ack=1`
  4. Intercambio de datos con flag `PSH, ACK` transmitiendo el payload JSON en claro.
  5. Cierre ordenado mediante `FIN, ACK`.
