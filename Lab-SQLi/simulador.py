"""Laboratorio exclusivamente local. Ejecutar: python simulador.py."""
import secrets
import sqlite3
from contextlib import closing
from time import perf_counter
from flask import Flask, abort, render_template, request, session

app = Flask(__name__)
app.secret_key = secrets.token_bytes(32)
app.config.update(MAX_CONTENT_LENGTH=4096, SESSION_COOKIE_HTTPONLY=True,
                  SESSION_COOKIE_SAMESITE="Strict",
                  SESSION_COOKIE_NAME="vivero_sqli_session")
CASES = {
    "normal": ("Acceso normal", "ana", "semilla123"),
    "incorrecto": ("Clave incorrecta", "ana", "incorrecta"),
    "tautologia": ("Tautología", "' OR '1'='1' -- ", "incorrecta"),
    "comentario": ("Comentario SQL", "ana' -- ", "incorrecta"),
}
SECURE_SQL = "SELECT id, usuario, rol FROM usuarios WHERE usuario = ? AND clave = ?"


def evaluate(mode, username, password):
    """Cada ejecución crea y descarta su propia base ficticia en memoria."""
    if mode not in ("vulnerable", "seguro"):
        raise ValueError("Modo no válido")
    if len(username) > 160 or len(password) > 160:
        raise ValueError("Máximo 160 caracteres por campo")
    with closing(sqlite3.connect(":memory:")) as db:
        db.row_factory = sqlite3.Row
        db.execute("CREATE TABLE usuarios (id INTEGER, usuario TEXT, clave TEXT, rol TEXT)")
        db.executemany("INSERT INTO usuarios VALUES (?, ?, ?, ?)", [
            (1, "ana", "semilla123", "Estudiante"),
            (2, "bruno", "maceta456", "Estudiante"),
            (3, "carla", "riego789", "Docente"),
        ])
        db.commit()
        expected = [dict(row) for row in db.execute(SECURE_SQL, (username, password))]
        sql = ("SELECT id, usuario, rol FROM usuarios WHERE usuario = '"
               + username + "' AND clave = '" + password + "'") if mode == "vulnerable" else SECURE_SQL
        params = (username, password) if mode == "seguro" else ()
        # Defensa de contención: el ejercicio solo puede leer la tabla ficticia.
        # No es la corrección de SQLi: esa corrección son los parámetros.
        def authorize(action, arg1, arg2, database, trigger):
            if action == sqlite3.SQLITE_SELECT:
                return sqlite3.SQLITE_OK
            if action == sqlite3.SQLITE_READ and arg1 == "usuarios":
                return sqlite3.SQLITE_OK
            return sqlite3.SQLITE_DENY
        db.set_authorizer(authorize)
        budget = [0]
        def limit_steps():
            budget[0] += 1
            return int(budget[0] > 100)
        db.set_progress_handler(limit_steps, 100)
        start = perf_counter()
        error = None
        try:
            cursor = db.execute(sql, params)
            fetched = cursor.fetchmany(21)
            rows = [dict(row) for row in fetched[:20]]
            truncated = len(fetched) > 20
        except sqlite3.Error as exc:
            rows, truncated, error = [], False, str(exc)
        elapsed = round((perf_counter() - start) * 1000, 3)
        bypass = bool(rows) and not expected
        if error:
            explanation = "SQLite rechazó la consulta. Un error no demuestra acceso ni una defensa completa."
        elif mode == "seguro":
            explanation = "Los signos ? conservan la estructura SQL. Cada entrada se entrega por separado como un valor literal, incluso si contiene comillas o comentarios."
        elif bypass:
            explanation = "Se devolvieron filas sin una coincidencia literal de usuario y clave: la entrada modificó la lógica SQL. OR puede hacer verdadera la condición y -- comenta el resto de la línea."
        else:
            explanation = "La consulta concatena entradas con instrucciones. Este resultado por sí solo no elimina la vulnerabilidad; compara los casos de tautología y comentario."
        return dict(mode=mode, sql=sql, params=params, rows=rows, error=error,
                    elapsed=elapsed, bypass=bypass, expected=len(expected),
                    truncated=truncated, explanation=explanation)


@app.before_request
def local_only():
    if request.remote_addr != "127.0.0.1":
        abort(403, description="Acceso permitido solo desde este equipo (127.0.0.1).")
    if request.host not in ("127.0.0.1:5000", "127.0.0.1"):
        abort(403, description="Abre exactamente http://127.0.0.1:5000/ en el navegador local.")
    if request.method == "POST":
        if request.headers.get("Origin") not in (None, "http://127.0.0.1:5000", "http://127.0.0.1"):
            app.logger.warning("Formulario rechazado: origen no permitido: %r", request.headers.get("Origin", "")[:160])
            abort(403, description="El origen del formulario no es el autorizado. Abre http://127.0.0.1:5000/ directamente, sin vista previa ni proxy, y vuelve a probar.")
        token = session.get("csrf", "")
        if not token:
            app.logger.warning("Formulario rechazado: falta la sesión local.")
            abort(403, description="No se recibió una sesión válida. Permite cookies para 127.0.0.1, vuelve al inicio y recarga el formulario. Si reiniciaste el servidor, usa un formulario nuevo.")
        if not secrets.compare_digest(token, request.form.get("csrf", "")):
            app.logger.warning("Formulario rechazado: el token no coincide con la sesión.")
            abort(403, description="El formulario está desactualizado o pertenece a otra sesión. Vuelve al inicio, recarga la página y ejecuta otra vez el caso.")


@app.errorhandler(403)
def forbidden(error):
    return render_template("error.html", explanation=error.description), 403


@app.after_request
def headers(response):
    response.headers["Content-Security-Policy"] = "default-src 'none'; style-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"
    response.headers["X-Content-Type-Options"] = "nosniff"
    # no-referrer convierte Origin en null en envíos HTML de navegadores.
    # same-origin conserva el origen local y evita divulgarlo a otros sitios.
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/", methods=["GET", "POST"])
def index():
    session.setdefault("csrf", secrets.token_hex(32))
    username, password, mode = "ana", "semilla123", "ambos"
    results, message = [], None
    if request.method == "POST":
        mode = request.form.get("modo", "ambos")
        username = request.form.get("usuario", "")
        password = request.form.get("clave", "")
        case = request.form.get("caso")
        if case in CASES:
            _, username, password = CASES[case]
        if mode not in ("ambos", "vulnerable", "seguro"):
            abort(400)
        try:
            results = [evaluate(m, username, password) for m in
                       (("vulnerable", "seguro") if mode == "ambos" else (mode,))]
        except ValueError as exc:
            message = str(exc)
    return render_template("index.html", cases=CASES, username=username,
                           password=password, mode=mode, results=results, message=message)


if __name__ == "__main__":
    print("Laboratorio local: http://127.0.0.1:5000 — detener con Ctrl+C")
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
