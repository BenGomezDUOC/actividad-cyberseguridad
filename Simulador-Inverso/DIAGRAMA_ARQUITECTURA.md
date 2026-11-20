# ARQUITECTURA DEL SISTEMA Y DIAGRAMA DE COMUNICACIÓN

**Asignatura:** Ciberseguridad en Tecnología Cloud y Contenedores  
**Proyecto:** Laboratorio de Comunicación Inversa (Reverse Connection) y Monitoreo de Eventos

---

## 1. Justificación de la Arquitectura

En las arquitecturas de red tradicionales, los servidores ofrecen servicios pasivos en puertos bien conocidos (ej. HTTP en 80/443, SSH en 22), mientras que los clientes inician las solicitudes. Sin embargo, en escenarios modernos de ciberseguridad defensiva y auditoría de amenazas avanzadas (APTs) o troyanos de acceso remoto (**RATs**, técnica MITRE ATT&CK **T1219** y **TA0011 - Command and Control**):

1. **Evasión de Firewalls Perimetrales / NAT:** Los cortafuegos y routers empresariales típicamente bloquean todo tráfico entrante no solicitado (Inbound Filtering), pero permiten conexiones salientes hacia Internet (Outbound Traffic, puertos 80, 443 o puertos arbitrarios).
2. **Conexión Inversa (Reverse Shell / Reverse TCP):** En lugar de que el operador intente conectarse directamente hacia la máquina interna (lo cual sería descartado por la tabla NAT o firewall), el **Agente** situado dentro de la red corporativa es quien toma la iniciativa e **inicia la conexión hacia el Controlador** externo.
3. **Control Centralizado y Supervisión Defensiva:** El controlador actúa como servidor de socket TCP manteniendo el canal bidireccional abierto para despachar instrucciones y recibir telemetría. La interfaz web desacoplada en Flask permite a los analistas del SOC observar, categorizar y auditar el tráfico en tiempo real.

---

## 2. Diagrama de Secuencia y Sentido de la Comunicación

```
+-----------------------------------------------------------------------------------+
|                            INTERFAZ DE LOOPBACK (127.0.0.1)                       |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|    +-------------------------+                     +-------------------------+    |
|    |    PANEL WEB FLASK      |                     |      AGENTE LOCAL       |    |
|    |    (Puerto 5000)        |                     |      (Puerto Efímero)   |    |
|    +------------+------------+                     +------------+------------+    |
|                 |                                               |                 |
|       (HTTP Polling / REST)                                     |                 |
|                 v                                               |                 |
|    +-------------------------+       [1] TCP SYN (Handshake)    |                 |
|    |    CONTROLADOR TCP      | <--------------------------------+                 |
|    |    (Servidor :9000)     | -------------------------------->|                 |
|    +------------+------------+       [2] TCP SYN-ACK            |                 |
|                 |                                               |                 |
|                 |                    [3] TCP ACK                |                 |
|                 | <---------------------------------------------+                 |
|                 |                                                                 |
|                 |         [4] Envío de Instrucción JSON: {"command":"STATUS"}     |
|                 | --------------------------------------------------------------> |
|                 |                                                                 |
|                 |         [5] Telemetría y Acuse JSON: {"status":"SUCCESS"}       |
|                 | <-------------------------------------------------------------- |
|                 v                                                                 |
|    +-------------------------+                                                    |
|    |      EVENT MANAGER      |                                                    |
|    |   (Auditoría y Alertas) |                                                    |
|    +------------+------------+                                                    |
|                 |                                                                 |
|                 v                                                                 |
|    [Exportación CSV / Alertas]                                                    |
|                                                                                   |
+-----------------------------------------------------------------------------------+
```

---

## 3. Componentes del Laboratorio

### 3.1. Servidor Controlador (`controller.py`)
* **Rol:** Servidor de socket TCP (`AF_INET`, `SOCK_STREAM`) escuchando en `127.0.0.1:9000`.
* **Funciones:**
  * Espera pasivamente la conexión del agente mediante un hilo independiente (`_accept_loop`).
  * Despacha instrucciones estructuradas en JSON delimitadas por salto de línea (`\n`).
  * Implementa una lista blanca estricta (`ALLOWED_COMMANDS`) para descartar cualquier comando ajeno o malicioso (**RF-14**).
  * Comunica el resultado a la capa web y al motor de eventos.

### 3.2. Agente Simulado (`agent.py`)
* **Rol:** Cliente de socket TCP que implementa la conexión inversa.
* **Funciones:**
  * Resuelve activamente hacia `127.0.0.1:9000` con mecanismos de reconexión continua en caso de indisponibilidad (**CP-09**).
  * Recibe y analiza las instrucciones JSON.
  * **Aislamiento Seguro:** Todas las acciones potencialmente lesivas (como apagado de equipo o control de periféricos) son emuladas estrictamente en estructuras en memoria sin realizar llamadas a la API del sistema operativo (`subprocess`, `os.system`).
  * Imprime por consola y devuelve una respuesta estructurada al controlador.

### 3.3. Gestor de Eventos y Alertas (`event_manager.py`)
* **Rol:** Subsistema de auditoría centralizada con soporte multihilo (`threading.Lock`).
* **Funciones:**
  * Clasifica cada evento en categorías (`NORMAL` vs `ALERTA`) y niveles de severidad (`INFO`, `WARNING`, `CRITICAL`).
  * Mantiene el historial en memoria para visualización inmediata en el dashboard.
  * Provee el generador de reportes en formato estándar **CSV** (**RF-13**).

### 3.4. Interfaz Web y API REST (`app.py`, `templates/`, `static/`)
* **Rol:** Front-end interactivo basado en Flask (`127.0.0.1:5000`).
* **Funciones:**
  * Sondeo asíncrono (polling) cada 2 segundos mediante JavaScript Fetch API.
  * Botonera predefinida para ejecución controlada de pruebas (Estado, Mensaje de Texto, Simulación de Hardware, Simulación de Apagado, Comando Inválido).
  * Consola de visualización de respuesta JSON en tiempo real.
