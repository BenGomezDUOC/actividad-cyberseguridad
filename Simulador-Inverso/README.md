# Simulador de Comunicación Inversa y Monitoreo de Eventos

Este proyecto implementa un laboratorio local para estudiar el intercambio de mensajes mediante sockets TCP entre un **Controlador** y un **Agente** bajo el modelo de comunicación inversa (Reverse Connection / Command & Control educativo), supervisado mediante un panel web desarrollado en **Flask**.

El entorno está diseñado con fines estrictamente pedagógicos y defensivos: todas las acciones potencialmente críticas (como apagado o interacción con periféricos) son simuladas y no producen ningún efecto en el sistema operativo del host.

---

## Estructura del Proyecto

```text
Simulador-Inverso/
├── app.py                 # Aplicación Flask y API web para monitoreo y control
├── controller.py          # Servidor TCP multihilo que escucha en 127.0.0.1:9000
├── agent.py               # Agente cliente TCP que se conecta al controlador
├── event_manager.py       # Motor de registro, clasificación de alertas y exportación CSV
├── requirements.txt       # Dependencias del proyecto (Flask)
├── README.md              # Documentación técnica, instalación y uso
├── static/
│   ├── app.js             # Lógica cliente para polling de eventos y envío de instrucciones
│   └── style.css          # Estilos de la interfaz web
└── templates/
    └── index.html         # Panel de monitoreo y control web
```

---

## Requisitos de Instalación

* **Python 3.10 o superior** (verificado en Python 3.13)
* Sistema Operativo: Windows / Linux / macOS
* Navegador web moderno
* (Opcional para análisis de paquetes) **Wireshark** con interfaz de captura en Loopback (`Npcap Loopback Adapter`).

---

## Instrucciones de Ejecución en Windows (PowerShell)

### 1. Creación del entorno e instalación de dependencias

```powershell
Set-Location ".\Simulador-Inverso"
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. Ejecución del Servidor Web y Controlador TCP

En una primera terminal de PowerShell:

```powershell
.\.venv\Scripts\python.exe app.py
```

Esto iniciará:
* El **Controlador TCP** escuchando en `127.0.0.1:9000`.
* El **Servidor Web Flask** escuchando en `http://127.0.0.1:5000`.

### 3. Ejecución del Agente Simulado

En una segunda terminal de PowerShell:

```powershell
.\.venv\Scripts\python.exe agent.py
```

El agente establecerá la conexión inversa hacia `127.0.0.1:9000` y reportará su estado al controlador.

### 4. Acceso al Panel de Monitoreo

Abre tu navegador en:
**[http://127.0.0.1:5000](http://127.0.0.1:5000)**
