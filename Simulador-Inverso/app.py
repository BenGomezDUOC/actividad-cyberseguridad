from flask import Flask, render_template, request, jsonify, Response
from controller import ControllerServer
from event_manager import EventManager
import threading
import sys

app = Flask(__name__)

# Instancias compartidas del servidor de control y auditoría
event_manager = EventManager()
controller = ControllerServer(host="127.0.0.1", port=9000, event_manager=event_manager)

# Iniciar el controlador TCP en segundo plano
controller.start()

@app.route("/")
def index():
    """RF-12: Panel web con Flask"""
    status = controller.get_status()
    stats = event_manager.get_stats()
    return render_template("index.html", status=status, stats=stats)

@app.route("/api/status", methods=["GET"])
def api_status():
    """RF-04: Retorna estado de conexión y métricas para polling web"""
    status = controller.get_status()
    stats = event_manager.get_stats()
    return jsonify({
        "status": status,
        "stats": stats
    })

@app.route("/api/events", methods=["GET"])
def api_events():
    """RF-10, RF-11: Retorna lista de eventos con clasificación de alertas"""
    events = event_manager.get_events(limit=50)
    return jsonify({"events": events})

@app.route("/api/send-command", methods=["POST"])
def api_send_command():
    """
    RF-05, RF-06, RF-07, RF-08, RF-09, RF-14:
    Despacha instrucciones predefinidas hacia el agente y retorna resultado
    """
    data = request.get_json() or {}
    command = data.get("command", "")
    param = data.get("param", "")

    result = controller.send_command(command, param)
    return jsonify(result)

@app.route("/api/export-csv", methods=["GET"])
def api_export_csv():
    """RF-13: Exportar los registros en formato CSV"""
    csv_data = event_manager.export_csv()
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=eventos_laboratorio_c2.csv"}
    )

@app.route("/api/clear-events", methods=["POST"])
def api_clear_events():
    """Limpia la bitácora de eventos"""
    event_manager.clear()
    event_manager.log_event(
        event_type="SYSTEM",
        command="CLEAR_LOGS",
        source="FLASK_PANEL",
        destination="EVENT_MANAGER",
        category="NORMAL",
        level="INFO",
        details="Registros de eventos reiniciados por el operador."
    )
    return jsonify({"success": True})

if __name__ == "__main__":
    print("="*60)
    print(" [*] PANEL WEB DE MONITOREO Y CONTROLADOR INVERSO")
    print(" [*] Web Panel: http://127.0.0.1:5000")
    print(" [*] TCP Controller: 127.0.0.1:9000")
    print("="*60)
    # Servidor local seguro
    app.run(host="127.0.0.1", port=5000, debug=False)
