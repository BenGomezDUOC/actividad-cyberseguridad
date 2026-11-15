# Validación de la entrega

Fecha: 26 de octubre de 2026.

Corrección del envío HTML: Referrer-Policy se cambia de no-referrer a same-origin. La primera política puede convertir Origin en null al enviar formularios desde navegadores, provocando el rechazo del origen. Se conservan la validación de origen, el token de sesión y el bind local. Se añade comprobación de la cabecera y de POST con origen local explícito; los clientes HTTP sin navegador no reproducen por sí solos el efecto de esta política.

Entorno ejecutado: Windows, Python 3.12, Flask 3.1.3 y SQLite incluido con Python.

- Cinco grupos de pruebas automáticas: OK.
- Acceso normal y clave incorrecta: resultados esperados en ambos modos.
- Tautología: tres filas en vulnerable, cero en parametrizado.
- Comentario: una fila en vulnerable, cero en parametrizado.
- Error SQL, sentencia múltiple, límite de longitud y base nueva: verificados.
- Rechazo de dirección remota, Host ajeno, POST sin token y origen ajeno: verificados.
- Escape HTML de las entradas y cabeceras de protección: verificados.
- Inicio: argumentos 127.0.0.1, puerto 5000, debug=False y use_reloader=False verificados automáticamente.
- Servidor real: GET y POST del caso tautología respondieron HTTP 200; se comprobó contenido de ambos modos. Proceso cerrado al finalizar.

El docente confirmó el funcionamiento en su navegador Windows después de aplicar la corrección de Referrer-Policy. No se ha ejecutado en macOS ni realizado una revisión visual completa por parte del agente. La guía para macOS usa comandos habituales de Python/venv; el código no depende de funciones específicas de Windows. Las pruebas no equivalen a una auditoría de seguridad ni habilitan un uso público.
