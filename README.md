# Actividad Práctica: Ciberseguridad en Tecnología Cloud y Contenedores

Este repositorio contiene los laboratorios prácticos de evaluación de ciberseguridad, incluyendo el **Simulador de Comunicación Inversa y Monitoreo de Eventos (100 puntos)**.

---

## 🚀 Guía Rápida de Ejecución: Simulador Inverso (Evaluación Principal)

Todo el código, documentación y evidencias de la actividad se encuentran en la carpeta **[`Simulador-Inverso/`](./Simulador-Inverso/)**.

### Requisitos Previos
* **Python 3.10 o superior**
* Navegador Web

### Paso 1: Instalar dependencias
Abre una terminal de PowerShell:
```powershell
Set-Location ".\Simulador-Inverso"
python -m pip install -r requirements.txt
```

### Paso 2: Iniciar el Controlador TCP y Servidor Web Flask (Terminal 1)
```powershell
python app.py
```
* Servidor Web Flask: `http://127.0.0.1:5000`
* Controlador TCP: `127.0.0.1:9000`

### Paso 3: Iniciar el Agente Simulado (Terminal 2)
Abre una **segunda terminal** de PowerShell:
```powershell
Set-Location ".\Simulador-Inverso"
python agent.py
```
* El agente establecerá la conexión inversa hacia el controlador.

### Paso 4: Monitoreo y Pruebas
1. Abre tu navegador en **[http://127.0.0.1:5000](http://127.0.0.1:5000)**.
2. Comprueba el estado "Agente Conectado".
3. Ejecuta las instrucciones predefinidas (`STATUS`, `SIMULATE_DEVICE_ACTION`, `SIMULATE_SHUTDOWN`, `SEND_TEXT` e `Instrucción Inválida`).
4. Haz clic en **"Exportar CSV"** para descargar la bitácora con los eventos generados.

---

## 📁 Entregables del Laboratorio (`Simulador-Inverso/`)

1. **Código fuente:**
   - `app.py`: Servidor web Flask y API REST.
   - `controller.py`: Servidor TCP con lista blanca defensiva.
   - `agent.py`: Agente de conexión inversa y acciones simuladas seguras.
   - `event_manager.py`: Motor de clasificación de alertas y exportación CSV.
   - `templates/` y `static/`: Frontend interactivo en tiempo real.
2. **Dependencias:** `requirements.txt`.
3. **Manual y documentación:** `README.md`.
4. **Arquitectura:** `DIAGRAMA_ARQUITECTURA.md`.
5. **Casos de prueba:** `MATRIZ_CASOS_DE_PRUEBA.md` (Validación de CP-01 a CP-10).
6. **Evidencia CSV generada:** `evidencias_eventos.csv`.
7. **Informe Técnico (PDF y Markdown):** `INFORME_TECNICO.pdf` (4 páginas) e `INFORME_TECNICO.md`.
8. **Pruebas automatizadas:** `test_simulador.py` (ejecutable con `python -m pytest test_simulador.py -v`).
