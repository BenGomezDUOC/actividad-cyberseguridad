# INFORME TÉCNICO DE LABORATORIO
## SIMULADOR DE COMUNICACIÓN INVERSA Y MONITOREO DE EVENTOS

**Asignatura:** Ciberseguridad en Tecnología Cloud y Contenedores  
**Entorno de Ejecución:** Windows 11 / Python 3.12 / Flask / Wireshark  
**Alcance:** Loopback (`127.0.0.1`), Acciones Defensivas y Simuladas  

---

### RESUMEN EJECUTIVO
El presente informe documenta el diseño, desarrollo, validación empírica y análisis forense de un simulador educativo de **comunicación inversa sobre TCP** (Command & Control / Reverse Shell) con monitoreo centralizado en una plataforma web construida en **Flask**. La solución permite estudiar en un entorno seguro y controlado cómo operan los canales de mando y control (C2), cómo se transportan instrucciones a nivel de capa de transporte y aplicación, y cómo un equipo de respuesta ante incidentes (SOC/Blue Team) puede clasificar eventos, correlacionar alertas y exportar bitácoras de auditoría, garantizando la ausencia de efectos lesivos en el sistema operativo anfitrión.

---

### 1. INTRODUCCIÓN Y FUNDAMENTOS TEÓRICOS

#### 1.1. Modelo Cliente-Servidor vs. Conexión Inversa (Reverse Connection)
En el modelo de red convencional, el servidor aloja un servicio a la espera pasiva en un puerto estático (por ejemplo, HTTP en el puerto 80), y los clientes externos inician peticiones hacia él. Sin embargo, en arquitecturas de red protegidas por cortafuegos corporativos, puertas de enlace NAT (Network Address Translation) y sistemas de inspección de paquetes (IPS), todo el tráfico entrante no solicitado (*Inbound*) es descartado por defecto.

Los atacantes y las herramientas de administración remota legítimas (RATs) recurren al paradigma de **comunicación inversa (Reverse TCP)**. En este esquema, el agente interno —situado tras el firewall— toma la iniciativa e inicia una conexión saliente (*Outbound*) hacia el servidor de control (Controlador/C2). Dado que la inmensa mayoría de las redes corporativas permiten conexiones salientes hacia Internet, la conexión TCP se establece con éxito y se mantiene viva, permitiendo que el controlador transmita órdenes hacia el agente en sentido inverso.

#### 1.2. Sockets TCP y Handshake de Tres Vías
Un socket TCP es un punto final (*endpoint*) de comunicación bidireccional entre dos procesos, definido por la tupla:
$$\text{Socket} = (\text{IP Origen}, \text{Puerto Origen}, \text{IP Destino}, \text{Puerto Destino})$$
Para garantizar una transmisión confiable, ordenada y libre de errores, el protocolo TCP realiza el proceso de negociación conocido como **Three-Way Handshake**:
1. **SYN:** El cliente envía un paquete con el flag `SYN` activo y un número de secuencia inicial ($ISN_c$).
2. **SYN-ACK:** El servidor responde confirmando la recepción (`ACK` = $ISN_c + 1$) y enviando su propio número de secuencia ($ISN_s$) con flag `SYN`.
3. **ACK:** El cliente confirma la recepción (`ACK` = $ISN_s + 1$). A partir de este instante el canal queda en estado `ESTABLISHED`.

#### 1.3. Marco de Referencia MITRE ATT&CK
El simulador aborda tácticas y técnicas catalogadas en la matriz de MITRE:
* **TA0011 (Command and Control):** Establecimiento del canal de comunicación para el envío de directivas hacia el agente.
* **T1219 (Remote Access Tools):** Emulación de un agente que recibe instrucciones de telemetría y ejecución.
* **T1529 (System Shutdown/Reboot):** Simulación de apagado de equipo como vector de disrupción de disponibilidad.
* **T1200 (Hardware Additions):** Simulación de alteración en el estado de periféricos o puertos de datos.

---

### 2. ARQUITECTURA DEL SISTEMA Y DECISIONES DE DISEÑO

El sistema está desacoplado en cuatro capas modulares para garantizar cohesión, mantenibilidad y seguridad:

```
[ Navegador Web ] <--- HTTP Polling ---> [ Servidor Flask (app.py) ]
                                                   |
                                            (Controlador C2)
                                          controller.py (:9000)
                                                   ^
                                                   | (TCP Loopback)
                                                   v
                                          [ Agente (agent.py) ]
                                                   |
                                       [ Motor EventManager ]
                                         (Alertas & CSV)
```

1. **Capa de Control TCP (`controller.py`):**
   * Implementa un servidor socket TCP vinculado estrictamente a `127.0.0.1:9000`.
   * Un hilo (`Thread`) en segundo plano ejecuta `_accept_loop` para aceptar conexiones sin bloquear el hilo principal.
   * Cuenta con un mecanismo de validación de lista blanca (`ALLOWED_COMMANDS`). Si una orden no está autorizada, el controlador la rechaza antes de enviarla por la red (**RF-14**).
2. **Capa de Agente Simulado (`agent.py`):**
   * Inicia la conexión saliente hacia el controlador (**RF-02**).
   * Incorpora control de reconexión automática mediante `ConnectionRefusedError` con intervalos de espera (**CP-09**).
   * **Simulación Segura:** Las órdenes de apagado (`SIMULATE_SHUTDOWN`) y periféricos (`SIMULATE_DEVICE_ACTION`) son procesadas en memoria modificando diccionarios de estado internos, sin invocar llamadas al sistema operativo (`subprocess`, `os.system`).
3. **Capa de Auditoría y Eventos (`event_manager.py`):**
   * Almacena cronológicamente cada evento con identificador único, marca de tiempo ISO, origen, destino, severidad (`INFO`, `WARNING`, `CRITICAL`) y categoría (`NORMAL` vs `ALERTA`).
   * Mecanismo de sincronización `threading.Lock` para evitar condiciones de carrera entre hilos concurrentes.
   * Generador de exportación a archivo **CSV** conforme al estándar RFC 4180 (**RF-13**).
4. **Capa de Interfaz de Usuario (`app.py`, `templates/`, `static/`):**
   * Construida con microframework Flask.
   * Proporciona endpoints REST (`/api/status`, `/api/events`, `/api/send-command`, `/api/export-csv`).
   * Panel interactivo con sondeo asíncrono cada 2 segundos para actualización en tiempo real de métricas, telemetría y logs.

---

### 3. PROTOCOLO DE APLICACIÓN Y MENSAJERÍA

Para el intercambio de mensajes sobre el flujo de bytes de TCP, se implementó un protocolo de capa de aplicación basado en tramas **JSON delimitadas por salto de línea (`\n`)**. Esto resuelve el problema de delimitación de paquetes (*packet framing*) intrínseco al streaming orientado a bytes de TCP.

* **Formato de Solicitud (Controlador -> Agente):**
  ```json
  {"command": "STATUS|SEND_TEXT|SIMULATE_DEVICE_ACTION|SIMULATE_SHUTDOWN", "param": "opcional"}\n
  ```
* **Formato de Respuesta (Agente -> Controlador):**
  ```json
  {
    "status": "SUCCESS|SIMULATED_SHUTDOWN_TRIGGERED|SIMULATED_DEVICE_ACTION_OK|REJECTED",
    "command": "NOMBRE_COMANDO",
    "is_alert": false,
    "alert_level": "INFO|WARNING|CRITICAL",
    "message": "Descripción legible de la acción",
    "data": { ... }
  }\n
  ```

---

### 4. RESULTADOS DE PRUEBAS Y ANÁLISIS DE TRÁFICO (WIRESHARK)

#### 4.1. Matriz de Casos de Prueba (CP-01 a CP-10)
Se ejecutaron satisfactoriamente el 100% de los diez casos de prueba obligatorios mediante la suite automatizada `test_simulador.py` (con motor `pytest`) y la consola web interactiva:
* **CP-01 / CP-02 (Conexión y Estado):** El agente completó el enlace local y el panel reflejó inmediatamente el estado *online* y la IP/puerto efímero asignado (`127.0.0.1:57015`).
* **CP-03 / CP-06 (Telemetría y Texto):** Los comandos `STATUS` y `SEND_TEXT` transfirieron datos bidireccionales con latencias inferiores a 5 ms en loopback.
* **CP-04 / CP-05 (Simulaciones de Seguridad):** Las órdenes críticas fueron clasificadas en la bitácora con flags de `ALERTA` y severidad `CRITICAL` / `WARNING`, verificándose que el hardware y sistema operativo anfitrión se mantuvieron intactos.
* **CP-07 (Rechazo de Anómalos):** Inyecciones de comandos como `SHELL_EXEC_POWERSHELL` fueron interceptadas y catalogadas con evento `COMMAND_REJECTED`.
* **CP-08 / CP-09 (Resiliencia y CSV):** Se generó el archivo `evidencias_eventos.csv` y se verificó que la desconexión del controlador activa la reconexión resiliente del agente sin fallas de software.

#### 4.2. Análisis Forense de Paquetes con Wireshark (CP-10)
Al capturar sobre el adaptador `Npcap Loopback Adapter` filtrando por `tcp.port == 9000`:
1. **Inspección de Flags:** Se comprobó el ciclo de vida del socket TCP:
   * Tramas de inicialización: `[SYN]` -> `[SYN, ACK]` -> `[ACK]`.
   * Tramas de transmisión: Paquetes con bandera `PSH` (Push) que fuerzan la entrega inmediata del buffer JSON hacia el espacio de usuario.
   * Tramas de finalización: Paquetes con flag `[FIN, ACK]` al terminar las sesiones de prueba.
2. **Hallazgo de Vulnerabilidad en Tráfico en Claro:** Wireshark reveló que el contenido de las instrucciones JSON se transmitió en texto plano sin cifrado (Cleartext Transmission). En un entorno de red real, cualquier atacante con acceso a la red local (mediante ARP Spoofing o sniffing promiscuo) podría leer las órdenes o alterar las cargas útiles mediante ataques Man-In-The-Middle (MITM).

---

### 5. EVALUACIÓN DEFENSIVA Y CONTROLES INSTITUCIONALES

Para neutralizar los riesgos derivados de canales de mando y control (C2) y conexiones inversas en una infraestructura corporativa, se justifican las siguientes medidas:

1. **Firewalls de Próxima Generación (NGFW) e Inspección TLS profunda:**
   * Implementar políticas de salida restrictivas (*Default Deny Outbound*), impidiendo conexiones TCP directas hacia puertos no autorizados fuera de los proxies institucionales.
   * Desencriptar e inspeccionar el tráfico saliente (SSL/TLS Decryption) para detectar firmas de comunicación no estándar o tramas JSON anómalas.
2. **Soluciones EDR (Endpoint Detection and Response):**
   * Monitoreo del árbol de procesos (`Process Lineage`) para detectar si procesos aparentemente benignos (ej. `powershell.exe`, binarios de Python o utilidades nativas LOLBins) abren sockets TCP salientes.
3. **Control y Bloqueo de Periféricos (DLP):**
   * Restricción por política de grupo (GPO) o software DLP del uso de unidades de almacenamiento masivo USB y desactivación de puertos no autorizados, neutralizando las acciones emuladas en `SIMULATE_DEVICE_ACTION`.
4. **MFA y Principio de Menor Privilegio:**
   * Restringir los permisos administrativos para que ningún usuario estándar pueda invocar comandos de apagado remoto o modificación de configuración del sistema (`SIMULATE_SHUTDOWN`).

---

### 6. LIMITACIONES DEL DISEÑO Y TRABAJO FUTURO

1. **Canal en Texto Plano:** La solución no implementó una capa criptográfica TLS/SSL sobre el socket TCP, exponiendo las tramas a inspección pasiva. Como mejora, se recomienda incorporar el módulo estándar `ssl` de Python con certificados mutuos (mTLS).
2. **Autenticación del Agente:** El controlador acepta la primera conexión recibida en el puerto 9000 sin validar un token o handshake criptográfico previo. Se recomienda agregar un desafío HMAC (Challenge-Response) para verificar la autenticidad del agente.
3. **Escalabilidad Multicliente:** El controlador actual maneja de forma óptima un agente concurrente para fines pedagógicos; la extensión a un pool multicliente requeriría selectores asíncronos (`asyncio`) o tablas dinámicas de conexiones activas.

---

### 7. CONCLUSIONES

1. El desarrollo del simulador permitió constatar de manera práctica por qué el modelo de **conexión inversa** es el estándar de facto empleado por operadores de pruebas de intrusión y atacantes avanzados para sobrepasar las barreras perimetrales NAT/Firewall.
2. La implementación demostró que es viable diseñar un laboratorio educativo de ciberseguridad con alto valor pedagógico mediante el uso estricto de **simulaciones seguras en memoria**, eliminando cualquier riesgo de impacto operativo en el equipo del estudiante.
3. La integración de la interfaz web en Flask junto al motor de eventos facilitó la correlación en tiempo real entre las acciones de red y las alertas de seguridad, simulando fielmente la experiencia operativa de un analista en un SOC moderno.
4. El análisis con Wireshark evidenció la importancia crítica de la criptografía de transporte para proteger la confidencialidad e integridad de la telemetría institucional.

---

### 8. REFERENCIAS BIBLIOGRÁFICAS
* National Institute of Standards and Technology (NIST). *Trojan Horse Definition*. CSRC Glossary. Disponible en: https://csrc.nist.gov/glossary/term/trojan_horse
* MITRE Corporation. *MITRE ATT&CK Matrix: Command and Control (TA0011)*. Disponible en: https://attack.mitre.org/tactics/TA0011/
* MITRE Corporation. *MITRE ATT&CK Technique: Remote Access Tools (T1219)*. Disponible en: https://attack.mitre.org/techniques/T1219/
* Python Software Foundation. *Socket programming in Python (socket module docs)*. Disponible en: https://docs.python.org/3/library/socket.html
* Pallets Projects. *Flask Documentation*. Disponible en: https://flask.palletsprojects.com/
* Wireshark Foundation. *Wireshark User's Guide: Analyzing Loopback Traffic*. Disponible en: https://www.wireshark.org/docs/wsug_html_chunked/
