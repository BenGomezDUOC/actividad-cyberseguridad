# Simulador de Comunicación Inversa y Monitoreo de Eventos (C2 Lab)

**Asignatura:** Ciberseguridad en Tecnología Cloud y Contenedores  
**Modalidad:** Individual o Parejas  
**Puntaje:** 100 puntos  

---

## 1. Descripción del Proyecto

Este laboratorio implementa una aplicación educativa en **Python** y **Flask** diseñada para comprender los fundamentos del modelo de **comunicación inversa sobre TCP** (Reverse Shell / Command & Control), la inspección de sockets de red y el monitoreo defensivo de eventos sospechosos en un centro de operaciones de seguridad (SOC).

El sistema se compone de tres elementos principales:
1. **Controlador TCP (C2):** Escucha localmente en `127.0.0.1:9000` y gestiona las instrucciones enviadas al agente.
2. **Agente Simulado:** Inicia activamente la conexión inversa hacia el controlador, procesa instrucciones y emite respuestas con telemetría.
3. **Panel Web Flask:** Proporciona un dashboard en tiempo real (`http://127.0.0.1:5000`) para despachar comandos, visualizar respuestas del agente, monitorear la bitácora de eventos y exportar registros en formato **CSV**.

> **Garantía de Seguridad y Alcance:** Todas las operaciones potencialmente destructivas (apagado de equipo o modificación de hardware) son **estrictamente simuladas en memoria**. Ninguna instrucción ejecuta llamadas al sistema operativo (`os.system`, `subprocess`) ni sale de la interfaz de loopback `127.0.0.1`.

---

## 2. Estructura del Directorio

```text
Simulador-Inverso/
├── app.py                      # Servidor Flask y API REST de control y monitoreo
├── controller.py               # Servidor TCP de escucha y despacho de instrucciones
├── agent.py                    # Agente cliente TCP de conexión inversa
├── event_manager.py            # Motor de auditoría, clasificación de alertas y CSV
├── generar_evidencias.py       # Script automatizado para ejecución de pruebas y logs
├── test_simulador.py           # Suite de pruebas automatizadas con pytest
├── evidencias_eventos.csv      # Archivo CSV exportado con eventos reales del laboratorio
├── DIAGRAMA_ARQUITECTURA.md    # Explicación de arquitectura y sentido del flujo TCP
├── MATRIZ_CASOS_DE_PRUEBA.md   # Matriz de los 10 casos de prueba obligatorios (CP-01 a CP-10)
├── INFORME_TECNICO.md          # Informe técnico detallado (4 a 6 páginas estándar)
├── requirements.txt            # Dependencias externas (Flask, pytest)
├── static/
│   ├── app.js                  # Lógica JavaScript de sondeo en tiempo real (Fetch API)
│   └── style.css               # Estilos modernos para el panel SOC
└── templates/
    └── index.html              # Plantilla HTML5 del panel de monitoreo
```

---

## 3. Requisitos Previos e Instalación

* **Python 3.10 o superior** (probado en Python 3.12 y 3.13 en Windows 11).
* Navegador Web (Chrome, Edge, Firefox).
* (Opcional para inspección de red) **Wireshark** con soporte de captura en bucle invertido (*Npcap Loopback Adapter*).

### Instalación de Dependencias

Abra una terminal de **PowerShell** en la carpeta del proyecto:

```powershell
Set-Location "C:\Users\Fernando\Documents\code\actividad-cyberseguridad\Simulador-Inverso"

# Si utiliza el entorno virtual local o el Python global:
python -m pip install -r requirements.txt
```

---

## 4. Guía de Ejecución

Para operar el laboratorio completo se recomienda abrir dos terminales de PowerShell:

### Terminal 1: Servidor Web y Controlador TCP

```powershell
python app.py
```
* Inicia el controlador TCP en `127.0.0.1:9000`.
* Inicia el servidor web Flask en `http://127.0.0.1:5000`.

### Terminal 2: Agente Simulado (Conexión Inversa)

```powershell
python agent.py
```
* El agente se conectará automáticamente al controlador e informará por consola las instrucciones recibidas.

### Acceso al Panel Web

Abra su navegador en: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

Desde allí podrá:
* Observar el estado en vivo de la conexión (**RF-04**).
* Ejecutar instrucciones predefinidas: `STATUS` (**RF-05**), `SIMULATE_DEVICE_ACTION` (**RF-08**), `SIMULATE_SHUTDOWN` (**RF-07**).
* Enviar mensajes de texto personalizados (**RF-09**).
* Probar el rechazo de comandos anómalos o maliciosos (**RF-14**).
* Descargar el reporte completo de auditoría en formato **CSV** (**RF-13**).

---

## 5. Ejecución de Pruebas Automatizadas

El proyecto cuenta con una suite completa de pruebas unitarias y de integración que validan los casos de prueba de la guía:

```powershell
python -m pytest test_simulador.py -v
```

Para regenerar el archivo CSV de evidencias reales:

```powershell
python generar_evidencias.py
```

---

## 6. Inspección de Tráfico con Wireshark (CP-10)

1. Abra **Wireshark**.
2. Seleccione la interfaz **Adapter for loopback traffic capture** (o *Npcap Loopback Adapter*).
3. Ingrese el siguiente filtro de captura/visualización:
   ```text
   tcp.port == 9000
   ```
4. Ejecute el agente y envíe instrucciones desde el panel web.
5. Observará:
   * **TCP 3-Way Handshake:** Paquetes `[SYN]`, `[SYN, ACK]`, `[ACK]`.
   * **Transferencia de Datos:** Paquetes con bandera `[PSH, ACK]` conteniendo el texto JSON en claro.
   * **Cierre de Conexión:** Paquetes con bandera `[FIN, ACK]`.
