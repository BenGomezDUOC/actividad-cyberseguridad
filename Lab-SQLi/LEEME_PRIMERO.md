# Comienza aquí

1. Extrae todo el ZIP. No ejecutes archivos desde dentro del ZIP.
2. Abre una terminal en la carpeta que contiene **simulador.py** y **requirements.txt**. Según cómo extraigas el ZIP, puede quedar una carpeta Lab-SQLi dentro de otra; entra hasta encontrar esos archivos.
3. Ejecuta los comandos correspondientes a tu equipo que aparecen abajo.
4. Abre http://127.0.0.1:5000/ y selecciona **Acceso normal** con el modo **Comparar ambos**.
5. Sigue los ejercicios de **README.md**. Mantén la terminal abierta; termina con **Ctrl+C**.

## Windows: PowerShell

Pega este bloque desde la carpeta que contiene simulador.py. No requiere activar el entorno ni cambiar la política de ejecución.

```powershell
if (-not (Test-Path -LiteralPath '.\simulador.py')) {
    throw 'Entra primero en la carpeta que contiene simulador.py.'
}
if (-not (Test-Path -LiteralPath '.\.venv\Scripts\python.exe')) {
    py -3 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el entorno. Revisa la instalación de Python.' }
}
& '.\.venv\Scripts\python.exe' -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar las dependencias.' }
& '.\.venv\Scripts\python.exe' -m unittest -v
if ($LASTEXITCODE -ne 0) { throw 'Las pruebas fallaron. Revisa la salida anterior.' }
& '.\.venv\Scripts\python.exe' simulador.py
```

## macOS: Terminal

Desde la carpeta que contiene simulador.py:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest -v
python simulador.py
```

Continúa con el siguiente comando solo si el anterior terminó correctamente. Las pruebas deben mostrar **OK**.

## Requisitos y uso

Python 3.10 o superior, navegador e Internet para instalar Flask. SQLite viene con Python. Cada estudiante ejecuta el laboratorio en su propio equipo y usa únicamente los datos ficticios incluidos.

Esta entrega ya incorpora las correcciones del formulario, la cookie de sesión específica y los mensajes de error en español. No requiere parches manuales. Después de reiniciar el servidor, abre el inicio y recarga la página para obtener un formulario nuevo.

El laboratorio está limitado a 127.0.0.1. No cambiar la dirección de escucha, publicar ni usar túneles. Si el puerto 5000 está ocupado, detén la otra copia antes de iniciar esta.
