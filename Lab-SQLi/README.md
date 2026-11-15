# Laboratorio local: inyección SQL en Vivero Florida

Material para estudiantes iniciales. Objetivo: reconocer cuándo una entrada altera una consulta y comprobar cómo los parámetros mantienen separados datos e instrucciones. Cada estudiante ejecuta su propia copia en su equipo.

## Requisitos y alcance

- Python 3.10 o superior con pip y venv; Flask se instala desde requirements.txt.
- SQLite viene con Python: no se necesita un servidor ni instalar una base aparte.
- Navegador moderno. Internet solo para instalar Flask; después funciona sin conexión.
- Aproximadamente 60–90 minutos. Conocimientos: formularios, usuario/clave y noción básica de tabla.
- Exclusivamente 127.0.0.1, puerto 5000. No publicar, usar túneles, redirección de puertos, servicios cloud, proxy ni cambiar a 0.0.0.0. No ejecutar con `flask run`; usar el comando indicado.
- No usar datos ni contraseñas reales. No existe un campo para indicar servidores o direcciones objetivo.

## Inicio en macOS (Terminal)

Instala Python 3 desde python.org si no lo tienes. Extrae el ZIP y coloca la carpeta Lab-SQLi en tu carpeta de usuario. Ejecuta:

```bash
cd ~/Lab-SQLi
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest -v
python simulador.py
```

## Inicio en Windows (PowerShell)

Instala Python 3 desde python.org si no lo tienes. Extrae el ZIP y coloca Lab-SQLi en tu carpeta de usuario. No necesitas activar el entorno ni cambiar la política de ejecución:

```powershell
Set-Location "$HOME\Lab-SQLi"
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest -v
.\.venv\Scripts\python.exe simulador.py
```

Si tu carpeta está en otro lugar, ajusta solo la primera ruta. Abre **http://127.0.0.1:5000**. Detén el laboratorio con **Ctrl+C** en la terminal. Si el puerto está ocupado, detén la otra copia que lo utiliza; no cambies el bind. No se requiere permitir acceso desde otras redes. Si falta pip/venv o `py`, revisa tu instalación de Python; en Windows puedes usar `python` en lugar de `py -3` si apunta a Python 3.10 o superior.

## Recorrido y resultados esperados

Selecciona «Comparar ambos». Los botones de casos reemplazan usuario y clave, ejecutan la consulta y dejan visibles las entradas empleadas.

| Caso | Usuario | Clave | Vulnerable | Parametrizada |
|---|---|---|---|---|
| Normal | `ana` | `semilla123` | 1 fila: ana | 1 fila: ana |
| Clave incorrecta | `ana` | `incorrecta` | 0 filas | 0 filas |
| Tautología | `' OR '1'='1' -- ` | `incorrecta` | 3 filas ficticias | 0 filas |
| Comentario | `ana' -- ` | `incorrecta` | 1 fila: ana | 0 filas |

En los dos últimos casos conserva el espacio después de `--`. Son ejemplos destinados únicamente a esta base ficticia.

Consulta vulnerable original:

```sql
SELECT id, usuario, rol FROM usuarios WHERE usuario = 'ana' AND clave = 'semilla123'
```

Con el comentario, queda:

```sql
SELECT id, usuario, rol FROM usuarios WHERE usuario = 'ana' -- ' AND clave = 'incorrecta'
```

El resto de esa línea se vuelve comentario; deja de comprobar la clave. En la tautología, OR introduce una condición verdadera. En cambio, la consulta segura siempre conserva esta estructura:

```sql
SELECT id, usuario, rol FROM usuarios WHERE usuario = ? AND clave = ?
```

Python entrega por separado `(usuario, clave)` al método execute. La entrada completa se interpreta como un valor: no existe un usuario llamado literalmente `ana' -- `. Los parámetros no son una lista de palabras prohibidas ni una limpieza de comillas.

## Actividad de 60 minutos

1. **0–10 min · Preparación.** Inicia el laboratorio, lee su alcance y localiza los campos, modos e indicadores. Identifica qué devuelve SELECT y qué filtra WHERE.
2. **10–20 min · Línea base.** Antes de ejecutar, predice los resultados de acceso normal y clave incorrecta. Comprueba ambos modos y registra filas y usuario devuelto.
3. **20–35 min · Alteración de la consulta.** Ejecuta tautología y comentario. Copia las consultas mostradas y marca dónde termina el dato y comienza una instrucción. Explica por qué el comentario permite omitir la clave.
4. **35–45 min · Defensa.** Compara las mismas entradas con los parámetros. Explica por qué cero filas no significa que se hayan eliminado las comillas. Prueba también un nombre con apóstrofo, por ejemplo `O'Connor`; observa error de sintaxis frente a valor literal sin coincidencia.
5. **45–55 min · Lectura de código.** Localiza SECURE_SQL, la concatenación y db.execute. Escribe el cambio mínimo para reemplazar la concatenación por una consulta parametrizada. No elimines el modo vulnerable de la copia de referencia.
6. **55–60 min · Cierre.** Entrega la tabla de cuatro casos, dos consultas anotadas y una explicación breve de la defensa y del alcance local.

## Extensión hasta 90 minutos

- **60–75 min:** en una copia de trabajo, sustituye la rama vulnerable por SECURE_SQL y sus parámetros. Ajusta las expectativas de las pruebas de tautología/comentario: ambos modos deben devolver cero filas. Ejecuta las pruebas y justifica el cambio.
- **75–85 min:** propone cinco mejoras para una aplicación real y clasifica su función: consultas parametrizadas, hash de contraseñas con librería especializada, privilegios mínimos, límites de intentos y errores sin detalles internos. Explica por qué ninguna sustituye a parametrizar.
- **85–90 min:** breve exposición y revisión entre pares.

## Evaluación (10 puntos)

| Criterio | Puntos |
|---|---|
| Predicciones y registro correcto de los cuatro casos en ambos modos | 3 |
| Explicación de OR, comillas y comentario con consulta anotada | 3 |
| Explicación de parámetros y propuesta correcta de cambio | 3 |
| Respeto del alcance local y uso de datos ficticios | 1 |

## Indicadores y límites del modelo

- **Filas devueltas:** registros obtenidos por la consulta, máximo 20 en pantalla.
- **Coincidencias literales:** verificación de referencia con parámetros; cuántas filas coinciden exactamente con ambos valores introducidos.
- **Omisión observada:** hay filas aunque la verificación literal devuelve cero. Es una medida del ejercicio, no un detector general de ataques.
- **Acceso simulado:** etiqueta educativa basada en filas; no autentica usuarios ni crea una sesión de acceso.
- **Tiempo:** medición real solo de la consulta; no incluye creación de base ni renderizado. No es un índice de seguridad.
- Se almacenan claves ficticias en texto para facilitar la clase. Esta simplificación no sirve para autenticación real. No se devuelven claves en los resultados.
- Base en memoria nueva para cada modo y cada envío; no hay archivo persistente que borrar ni botón de reinicio necesario. Al cerrar la conexión se descarta. No se guardan entradas en registros de aplicación ni historial de ejercicios; permanecen visibles en el formulario mientras está abierto.
- Contención adicional: solo lecturas de la tabla ficticia, una sentencia por ejecución, longitud limitada y presupuesto de instrucciones SQLite. Estos límites no corrigen la concatenación. Los parámetros son la defensa demostrada.
- Host y origen restringidos, token de formulario, salida HTML escapada, sin recursos externos, sin depurador ni recarga automática. Estos controles reducen exposición accidental; no sustituyen el aislamiento del equipo. Ejecuta el material en un equipo de prácticas, sin proxies ni túneles.

## Pruebas incluidas

Si aparece un rechazo al enviar, la página indica si se trata del origen, de cookies/sesión o de un formulario desactualizado. La terminal registra el motivo sin registrar tokens ni cookies. Vuelve al inicio y carga un formulario nuevo después de reiniciar el servidor. Se usa una cookie con nombre propio para evitar colisiones con otras aplicaciones Flask locales; las cookies del navegador se comparten entre puertos de un mismo host.

`python -m unittest -v` ejecuta cinco grupos: acceso normal/incorrecto, tautología/comentario, errores y regeneración, controles web/escape HTML y configuración de inicio. No contacta servicios externos. Una instalación correcta debe mostrar **Ran 5 tests** y **OK**. La prueba del inicio comprueba los argumentos del servidor; no abre un puerto. Comprueba además en el navegador los cuatro botones y confirma en la terminal que aparece 127.0.0.1 y debug desactivado.

## Archivos

- simulador.py: aplicación y creación de datos.
- templates/index.html: interfaz didáctica en español.
- static/style.css: estilos locales, sin CDN.
- test_simulador.py: pruebas automáticas.
- requirements.txt: dependencia de Flask.

## Referencias oficiales

- Python, parámetros de sqlite3: https://docs.python.org/3/library/sqlite3.html#sqlite3-placeholders
- Flask, inicio y visibilidad del servidor: https://flask.palletsprojects.com/en/stable/quickstart/

El material enseña el mecanismo usando consultas reales exclusivamente sobre una base desechable ficticia. No contiene escáner, tráfico de ataque, destinos remotos ni técnicas de extracción de datos reales.
